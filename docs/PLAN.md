# Plano de Adaptação — Desenhador2D

Migração da implementação atual (plana, matriz booleana, grade de `div`s) para a
arquitetura definida em `.claude/CLAUDE.md`, mais três comportamentos novos:
elásticos, seleção de figura e persistência em arquivo.

---

## 1. Situação atual vs. alvo

| Aspecto | Hoje | Alvo |
|---|---|---|
| Layout | `main.py` + `models.py` na raiz, `static/` | `backend/app/...` + `frontend/` |
| Buffer de pixels | `list[list[bool]]` 64×48 | NumPy `uint8[H][W][4]` (RGBA) |
| Renderização | grade de `div` (3072 elementos) | HTML Canvas + `ImageData` |
| Cor | nenhuma (verde fixo) | por figura (`cor: {r,g,b}`) |
| Espessura | nenhuma (1px) | por figura (`esp`) |
| IDs | `uuid4()` | `ponto_1`, `reta_1`, ... |
| Testes | scripts ad-hoc na raiz que exigem servidor no ar | `backend/tests/` com pytest, sem servidor |
| Dependências | `pip` + `requirements.txt` | `uv` + `pyproject.toml` |
| Execução | `iniciar.bat` | `executar.sh` (+ `.bat` atualizado) |

---

## 2. Decisões tomadas

Confirmadas com o usuário:

1. **Migração completa** para a árvore do `CLAUDE.md`.
2. **`raio` do círculo** no JSON é um **ponto sobre a circunferência**; o raio
   efetivo é `distância(centro, raio)`. É exatamente a interação de 2 cliques
   (centro → borda) que já existe.
3. **`esp` é rasterizada de verdade** — traço com a espessura informada.
4. **Persistência nos dois sentidos**: exportar `.json` + imagem, e importar
   `.json` de volta.

Decididas por mim (sinalize se discordar):

5. **Comunicação REST**, não WebSocket. O `CLAUDE.md` diz "REST initially,
   WebSocket later". Ver decisão 6.
6. **O elástico é desenhado no cliente**, num `<canvas>` de overlay, usando a
   API 2D do navegador (`lineTo`/`arc`/`strokeRect`). Nenhuma requisição por
   `mousemove`. Os **pixels comprometidos continuam vindo 100% do Python** — o
   elástico é só um guia visual transitório, nunca vira pixel na imagem. A
   alternativa (rasterizar no servidor a cada movimento do mouse) exigiria
   WebSocket e está fora do escopo atual.
7. **Resolução do canvas: 800×600** (mesma proporção 4:3 do 64×48 atual).
   Necessária para que `esp` entre 3 e 50 do formato JSON faça sentido e para
   que coordenadas normalizadas com 3 casas decimais tenham precisão útil.
8. **Fundo branco**, cores por figura. Hoje o fundo é preto com pixels verdes;
   com cores arbitrárias (ex.: `204,255,204`) o branco é mais legível.
9. **Imagem exportada como PNG gerado no cliente** via `canvas.toBlob()`. O
   canvas é cópia byte a byte do buffer NumPy, então o resultado é idêntico a
   gerar no servidor, sem adicionar Pillow como dependência.
10. **Elástico só para reta, círculo e retângulo**, como especificado. Triângulo
    e ponto mantêm o comportamento atual de cliques.
11. **Funcionalidades atuais preservadas**: redesenhar filtrado por tipo, limpar
    tela mantendo a ED, listar ED, adicionar primitivo via JSON.

---

## 3. Estrutura de arquivos alvo

```
desenhador2d/
├── pyproject.toml              # uv
├── uv.lock
├── executar.sh                 # runner bash
├── iniciar.bat                 # runner Windows (atualizado p/ uv)
├── README.md
├── PLAN.md
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # instancia FastAPI, monta frontend/, inclui routes
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py       # todos os endpoints REST
│   │   └── graphics/
│   │       ├── __init__.py
│   │       ├── color.py        # Cor(r,g,b)
│   │       ├── point.py        # Ponto2D(x,y) em pixels
│   │       ├── image.py        # Imagem: buffer NumPy RGBA + stamp de espessura
│   │       ├── figura.py       # Figura (ED) + primitivos
│   │       ├── hittest.py      # seleção: distância ponto→figura
│   │       ├── serializacao.py # JSON <-> Figura no formato exigido
│   │       ├── algorithms/
│   │       │   ├── __init__.py
│   │       │   ├── line.py     # Bresenham
│   │       │   ├── circle.py   # Midpoint
│   │       │   ├── rectangle.py
│   │       │   └── triangle.py
│   │       └── transforms/
│   │           ├── __init__.py
│   │           └── viewport.py # normalizado [0,1] <-> pixel
│   └── tests/
│       ├── test_line.py
│       ├── test_circle.py
│       ├── test_rectangle.py
│       ├── test_thickness.py
│       ├── test_viewport.py
│       ├── test_serializacao.py
│       ├── test_hittest.py
│       └── test_api.py
└── frontend/
    ├── index.html
    ├── canvas.js
    └── style.css
```

Docstrings em português, conforme `CLAUDE.md`.

---

## 4. Formato JSON (contrato)

Formato fixo, definido pelo enunciado. Coordenadas **normalizadas em [0,1]**,
`esp` em pixels, `id` sequencial por tipo.

```json
{ "figura": {
    "ponto":     [{ "x":0.162, "y":0.693, "cor":{"r":0,"g":102,"b":102}, "esp":50, "id":"ponto_1" }],
    "reta":      [{ "p1":{"x":..,"y":..}, "p2":{"x":..,"y":..}, "cor":{...}, "esp":12, "id":"reta_1" }],
    "triangulo": [{ "p1":{...}, "p2":{...}, "p3":{...}, "cor":{...}, "esp":6, "id":"triangulo_1" }],
    "retangulo": [{ "p1":{...}, "p2":{...}, "cor":{...}, "esp":18, "id":"retangulo_1" }],
    "circulo":   [{ "centro":{...}, "raio":{...}, "cor":{...}, "esp":10, "id":"circulo_1" }]
} }
```

Regras derivadas:

- `retangulo.p1`/`p2` são cantos opostos; a ordem não é normalizada na
  serialização (preservamos o que foi clicado), mas a rasterização usa
  `min`/`max`.
- `circulo.raio` é um ponto; raio efetivo = `distância(centro, raio)` em pixels,
  calculado **após** desnormalizar ambos.
- Chaves de tipo ausentes são tratadas como lista vazia na importação.
- `esp` é sanitizada para `>= 1` na importação.

---

## 5. Tarefas

Cada tarefa é independentemente verificável. Ordem sugerida = ordem de execução.

---

### Tarefa 1 — Scaffolding: uv, árvore de diretórios, gitignore, runner

**Objetivo:** preparar o esqueleto do projeto sem lógica ainda.

- Criar `pyproject.toml` com `fastapi`, `uvicorn[standard]`, `numpy`; grupo dev
  com `pytest` e `httpx` (para `TestClient`). Gerar `uv.lock` com `uv sync`.
- Criar a árvore `backend/app/{api,graphics/{algorithms,transforms}}` e
  `backend/tests/` com os `__init__.py`.
- Criar `executar.sh`: verifica que `uv` existe, roda `uv sync`, checa se a
  porta 8000 está livre, e executa `uv run uvicorn backend.app.main:app`.
  Sem `set -e` silencioso — cada passo informa o que está fazendo.
- Atualizar `.gitignore`: `__pycache__/`, `*.pyc`, `.venv/`, `desenhador/`,
  `.pytest_cache/`, `exportados/`.
- Atualizar `iniciar.bat` para usar `uv` (hoje chama `python -m pip`, e o
  cabeçalho `@echo off` foi removido por engano — restaurar).

**Feito quando:** `uv sync` funciona e `./executar.sh` sobe um app FastAPI vazio.

**Nota:** existe uma venv antiga versionada como `desenhador/` (não rastreada
pelo git). Vou ignorá-la no `.gitignore` mas **não apagá-la** sem sua confirmação.

---

### Tarefa 2 — Núcleo gráfico: `color.py`, `point.py`, `image.py`

**Objetivo:** substituir a matriz booleana pelo buffer NumPy RGBA.

- `Cor`: dataclass `(r, g, b)`, validação 0–255, `to_rgba()` → tupla com A=255,
  `from_dict()` / `to_dict()`.
- `Ponto2D`: dataclass `(x, y)` inteiros, em pixels.
- `Imagem`:
  - `buffer: np.ndarray` shape `(altura, largura, 4)`, dtype `uint8`.
  - `limpar()` → preenche de branco opaco.
  - `set_pixel(x, y, cor)` com recorte (clipping) nos limites.
  - `stamp(x, y, cor, esp)` → **a peça central da espessura**: pinta um disco
    cheio de diâmetro `esp` centrado em `(x,y)`. `esp <= 1` degenera para um
    único pixel. Todos os algoritmos chamam `stamp` em vez de `set_pixel`, e é
    isso que dá espessura uniforme e juntas arredondadas para reta, círculo,
    retângulo e triângulo com uma única implementação.
  - `to_bytes()` → `bytes` do buffer, para o endpoint de estado.

**Feito quando:** testes de `stamp` verificam raio e recorte nas bordas.

---

### Tarefa 3 — `transforms/viewport.py`

**Objetivo:** conversão entre o espaço normalizado do JSON e pixels.

- `normalizar(x_px, y_px, largura, altura) -> (float, float)`
- `desnormalizar(x, y, largura, altura) -> (int, int)`
- Convenção: `x_px = round(x * (largura - 1))`, idem para y. Assim `0.0` mapeia
  para o primeiro pixel e `1.0` para o último, sem estourar o buffer.
- Arredondamento na exportação: 3 casas decimais, como no exemplo do enunciado.

**Feito quando:** teste de ida-e-volta confirma que
`desnormalizar(normalizar(p)) == p` para todos os pixels de uma amostra.

---

### Tarefa 4 — Algoritmos de rasterização com espessura

**Objetivo:** portar os algoritmos existentes para o buffer RGBA + `esp`.

- `algorithms/line.py` — Bresenham inteiro (porte direto do `models.py` atual),
  assinatura `desenhar_reta(imagem, p1, p2, cor, esp)`.
- `algorithms/circle.py` — Midpoint com simetria de 8 pontos, assinatura
  `desenhar_circulo(imagem, centro, raio, cor, esp)`.
- `algorithms/rectangle.py` — 4 retas.
- `algorithms/triangle.py` — 3 retas.
- Ponto: `stamp` direto, sem módulo próprio.

Nenhuma biblioteca de desenho; a espessura vem de `Imagem.stamp`.

**Feito quando:** `test_line.py`, `test_circle.py`, `test_rectangle.py` e
`test_thickness.py` passam, comparando conjuntos de pixels esperados.

---

### Tarefa 5 — Modelo de domínio: `figura.py`

**Objetivo:** a ED passa a ser uma **Figura** — uma coleção tipada de primitivos.

- Classes `Ponto`, `Reta`, `Triangulo`, `Retangulo`, `Circulo`. Cada uma guarda
  seus pontos **em coordenadas de pixel**, `cor`, `esp` e `id`.
- `Figura`:
  - `adicionar(primitivo)` → atribui `id` sequencial por tipo
    (`ponto_1`, `ponto_2`, `reta_1`, ...), com contadores por tipo.
  - `remover(id) -> bool`
  - `limpar()`
  - `desenhar(imagem, tipo="all")` → substitui `ED.redraw`, mantendo o filtro
    por tipo que a UI já usa.
  - `listar()` → resumo para a UI.
- IDs sequenciais são estáveis dentro da sessão; ao importar um JSON, os
  contadores são recalculados a partir dos ids recebidos.

**Feito quando:** adicionar/remover/filtrar funciona e os ids seguem o padrão.

---

### Tarefa 6 — `serializacao.py`: JSON ⇄ Figura

**Objetivo:** implementar exatamente o contrato da seção 4.

- `figura_para_json(figura, largura, altura) -> dict` — normaliza coordenadas,
  agrupa por tipo, arredonda em 3 casas.
- `json_para_figura(dados, largura, altura) -> Figura` — desnormaliza, valida
  campos obrigatórios, calcula o raio do círculo a partir do ponto `raio`,
  sanitiza `esp` e `cor`, e levanta `ValueError` com mensagem clara em caso de
  JSON malformado.
- Round-trip preserva a figura dentro do erro de arredondamento de 3 casas.

**Feito quando:** `test_serializacao.py` cobre round-trip, o JSON de exemplo do
enunciado importado sem erro, e as mensagens de erro para JSON inválido.

---

### Tarefa 7 — `hittest.py`: seleção geométrica

**Objetivo:** dado um clique, descobrir qual figura foi atingida.

- `encontrar(figura, x, y) -> id | None`.
- Percorre os primitivos em **ordem inversa de inserção** (a figura desenhada
  por cima ganha).
- Distância analítica por tipo, sem varrer o buffer:
  - ponto → distância euclidiana;
  - reta → distância ponto-segmento;
  - retângulo → menor distância às 4 arestas;
  - triângulo → menor distância às 3 arestas;
  - círculo → `abs(distância(p, centro) - raio)`.
- Tolerância = `max(esp / 2, 4px)`, para que traços finos continuem clicáveis.

**Feito quando:** `test_hittest.py` cobre acerto, erro por pouco, e a regra de
prioridade do último desenhado.

---

### Tarefa 8 — API REST: `api/routes.py` + `app/main.py`

**Objetivo:** expor tudo por REST e servir o frontend.

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | serve `frontend/index.html` |
| `GET` | `/api/estado` | largura, altura, figura (lista) e id selecionado |
| `GET` | `/api/imagem` | buffer RGBA cru (`application/octet-stream`) para `ImageData` |
| `POST` | `/api/primitivo` | cria primitivo (pixels, cor, esp), desenha e retorna o id |
| `POST` | `/api/selecionar` | `{x, y}` → id atingido ou `null` |
| `DELETE` | `/api/primitivo/{id}` | remove e redesenha |
| `POST` | `/api/redesenhar` | `{tipo}` — limpa e redesenha filtrado (comportamento atual) |
| `POST` | `/api/limpar` | limpa a imagem, preserva a figura (comportamento atual) |
| `GET` | `/api/figura/exportar` | JSON no formato da seção 4 |
| `POST` | `/api/figura/importar` | recebe o JSON, substitui a figura, redesenha |

- O buffer vai como bytes crus, não como JSON de 480.000 números — é o que torna
  800×600 viável.
- Estado global do módulo (uma `Imagem` + uma `Figura`), como hoje. Sem sessões
  nem banco: é uma aplicação local de disciplina.
- Erros de validação → `400` com `{"ok": false, "erro": "..."}`.

**Feito quando:** `test_api.py` cobre cada rota com `TestClient`, incluindo os
caminhos de erro.

---

### Tarefa 9 — Frontend: Canvas + `ImageData`

**Objetivo:** substituir a grade de `div`s por um `<canvas>` real.

- `frontend/index.html`: dois `<canvas>` sobrepostos —
  `#canvas` (imagem vinda do backend) e `#overlay` (elástico e destaque de
  seleção). Toolbar com: ferramenta, **seletor de cor**, **espessura**,
  filtro de redesenho, e os botões de limpar/redesenhar/exportar/importar.
- `frontend/canvas.js`:
  - `carregarImagem()` → `fetch('/api/imagem')` → `ArrayBuffer` →
    `new ImageData(new Uint8ClampedArray(buf), largura, altura)` → `putImageData`.
  - conversão de coordenadas do mouse → pixel, respeitando escala CSS do canvas.
  - painel da ED e logs, mantendo o que já existe.
- `frontend/style.css`: portar `static/styles.css`, remover as regras da grade.

**Feito quando:** desenhar ponto/reta/círculo/retângulo/triângulo com cor e
espessura funciona ponta a ponta.

---

### Tarefa 10 — Elásticos (reta, círculo, retângulo)

**Objetivo:** o comportamento "Paint" pedido.

- Máquina de estados no `canvas.js`: `ocioso → ancorado → (commit) → ocioso`.
  - 1º clique ancora o primeiro ponto;
  - `mousemove` (sem botão pressionado) redesenha o preview no `#overlay` a cada
    movimento, com a cor e espessura correntes;
  - 2º clique confirma: `POST /api/primitivo`, limpa o overlay, recarrega a
    imagem;
  - `Esc` cancela a ancoragem; trocar de ferramenta também cancela.
- Preview por tipo: reta = segmento; círculo = `arc` com raio =
  distância(âncora, cursor); retângulo = `strokeRect` entre âncora e cursor.
- O overlay é limpo com `clearRect` a cada frame — não acumula rastro.
- `mousemove` é limitado por `requestAnimationFrame` para não redesenhar mais de
  uma vez por frame.

**Feito quando:** os três primitivos mostram o elástico seguindo o cursor e só
viram pixel no segundo clique.

---

### Tarefa 11 — Seleção e remoção

**Objetivo:** selecionar uma figura para inspeção e remoção.

- Ferramenta "Selecionar" na toolbar.
- Clique → `POST /api/selecionar` → id ou `null`.
- Figura selecionada é destacada **no overlay** (contorno tracejado ao redor do
  seu retângulo envolvente) — a imagem rasterizada não é alterada.
- Painel lateral mostra os dados da figura selecionada (tipo, pontos, cor, esp,
  id) — é o "for testing" do enunciado.
- Botão "Remover selecionada" e tecla `Delete` → `DELETE /api/primitivo/{id}` →
  redesenha.
- Clicar no vazio limpa a seleção.

**Feito quando:** selecionar, inspecionar e remover funciona para os 5 tipos.

---

### Tarefa 12 — Exportar e importar arquivo

**Objetivo:** a persistência pedida — JSON da figura + a imagem.

- Botão **"Exportar"**: baixa dois arquivos —
  `figura.json` (de `GET /api/figura/exportar`) e `figura.png`
  (de `canvas.toBlob()`).
- Botão **"Importar"**: `<input type="file" accept=".json">` → lê o arquivo →
  `POST /api/figura/importar` → recarrega imagem e ED.
- JSON malformado mostra a mensagem de erro do backend na UI, sem quebrar o
  estado atual.

**Feito quando:** exportar → limpar tudo → importar reproduz a mesma imagem.

---

### Tarefa 13 — Suíte de testes pytest

**Objetivo:** testes reais, em diretório próprio, sem depender de servidor no ar.

- Substituir `test_draw.py` e `test_primitives.py` (scripts que exigem o servidor
  rodando e só imprimem no terminal) pelos testes de `backend/tests/`.
- Configurar `pytest` no `pyproject.toml` (`testpaths = ["backend/tests"]`).
- Cobertura: algoritmos, espessura, viewport, serialização, hit-test, API.

**Feito quando:** `uv run pytest` passa sem nenhum servidor rodando.

---

### Tarefa 14 — Remoção dos arquivos antigos e documentação

**Objetivo:** não deixar o repositório com duas implementações.

- Remover: `main.py`, `models.py`, `test_draw.py`, `test_primitives.py`,
  `static/` (`index.html`, `app.js`, `styles.css`), `requirements.txt`.
- Reescrever o `README.md`: nova arquitetura, novos comandos (`uv sync`,
  `./executar.sh`, `uv run pytest`), formato JSON documentado, e como usar
  elásticos, seleção e exportação/importação.
- Documentar em `README.md` a decisão 6 (elástico no cliente) e a nota do
  `CLAUDE.md` sobre WebSocket como passo futuro.

**Feito quando:** o repositório tem uma única implementação e o README descreve
o que o código realmente faz.

---

## 6. Riscos e efeitos colaterais

| Risco | Mitigação |
|---|---|
| Contrato REST muda (`/state` → `/api/estado` etc.) | Não há consumidores externos; o único cliente é o frontend, reescrito junto. |
| Buffer de 800×600×4 = 1,9 MB por `GET /api/imagem` | Local, via loopback. Se pesar, o passo seguinte é o WebSocket com região suja, já previsto no `CLAUDE.md`. |
| `esp` grande (ex.: 50) domina o canvas | `stamp` recorta nas bordas; espessura é escolha do usuário. Sem limite artificial, conforme decidido. |
| Perda de precisão na normalização (3 casas) | Em 800×600, 0.001 ≈ 0.8px. Documentado; round-trip testado com essa tolerância. |
| Estado global no módulo | Já é assim hoje; adequado para aplicação local de disciplina. Não introduzir sessões. |
| Venv antiga `desenhador/` no diretório | Adicionada ao `.gitignore`; remoção física só com confirmação. |

## 7. Fora de escopo

Explicitamente não incluído, por não estar na especificação:

- WebSocket (o `CLAUDE.md` marca como "later").
- Elástico para triângulo e ponto (o enunciado pede reta, círculo e retângulo).
- Edição/movimentação da figura selecionada (o enunciado pede testar e remover).
- Undo/redo, camadas, preenchimento, zoom/pan.
- Persistência em banco de dados.
