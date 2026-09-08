# Desenhador2D

Aplicação web para desenho de primitivos gráficos 2D com manipulação direta de
pixels. Os algoritmos de rasterização (Bresenham, Midpoint) são implementados
manualmente, sem bibliotecas gráficas prontas.

---

## Arquitetura

```
                        Navegador
              ┌────────────────────────────┐
              │  HTML + JS sem framework   │
              │                            │
              │  #tela         ← ImageData │
              │  #sobreposicao ← elástico  │
              │                  e seleção │
              └─────────────┬──────────────┘
                            │  REST / JSON
                            ▼
              ┌────────────────────────────┐
              │  FastAPI  (api/routes.py)  │
              │                            │
              │  ┌──────────────────────┐  │
              │  │ Imagem — NumPy RGBA  │  │
              │  │ (altura, largura, 4) │  │
              │  └──────────▲───────────┘  │
              │             │ carimbar()   │
              │  ┌──────────┴───────────┐  │
              │  │ Algoritmos           │  │
              │  │  Bresenham (reta)    │  │
              │  │  Midpoint  (círculo) │  │
              │  │  Retângulo, Triângulo│  │
              │  └──────────────────────┘  │
              │                            │
              │  Figura (ED) · Hit-test    │
              │  Serialização · Viewport   │
              └────────────────────────────┘
```

O buffer de pixels é um array NumPy `uint8` de shape `(altura, largura, 4)`, que
mapeia diretamente para o `ImageData` do canvas. Nenhum pixel é rasterizado no
cliente — a imagem exibida vem sempre do backend.

### Componentes

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/main.py` | Instancia o FastAPI, inclui as rotas e serve o frontend |
| `backend/app/api/routes.py` | Endpoints REST e o estado único da aplicação |
| `backend/app/graphics/image.py` | Buffer RGBA e o carimbo de disco que dá espessura |
| `backend/app/graphics/color.py` | `Cor` RGB validada |
| `backend/app/graphics/point.py` | `Ponto2D` em coordenadas de pixel |
| `backend/app/graphics/figura.py` | A ED: `Figura` e os primitivos, com ids sequenciais |
| `backend/app/graphics/hittest.py` | Seleção por proximidade do clique |
| `backend/app/graphics/serializacao.py` | Conversão entre a `Figura` e o arquivo JSON |
| `backend/app/graphics/algorithms/` | Bresenham, Midpoint, retângulo e triângulo |
| `backend/app/graphics/transforms/viewport.py` | Coordenadas normalizadas ⇄ pixels |
| `frontend/index.html` | Interface: barra de ferramentas, canvas, painéis |
| `frontend/canvas.js` | Ferramentas, elásticos, seleção, exportação e importação |
| `frontend/style.css` | Estilos |
| `executar.sh` / `iniciar.bat` | Scripts de inicialização |

### Algoritmos

- **Reta** — [Bresenham](https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm):
  decide pixel a pixel qual posição ligar, acumulando o erro, sem ponto flutuante.
- **Círculo** — [Midpoint](https://en.wikipedia.org/wiki/Midpoint_circle_algorithm):
  calcula o primeiro octante e reflete nas oito posições simétricas.
- **Retângulo** — 4 retas de Bresenham. **Triângulo** — 3 retas de Bresenham.
- **Ponto** — carimbo direto.

### Espessura

`Imagem.carimbar()` é o único ponto do sistema que trata espessura: pinta um
disco de diâmetro `esp` em vez de um único pixel. Todos os algoritmos chamam
esse método, o que dá traços de largura uniforme e juntas arredondadas com uma
única implementação.

Discos de espessura par são deslocados meio pixel, porque não têm centro exato
na grade; assim a largura resultante é exatamente `esp` para qualquer valor.

---

## Pré-requisitos

- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/)** para gerenciar as dependências

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Como executar

### Script

```bash
./executar.sh
```

Ele verifica o `uv`, sincroniza as dependências, confere se a porta está livre e
sobe o servidor. Para usar outra porta: `PORTA=8001 ./executar.sh`.

No Windows, dê duplo clique em `iniciar.bat`.

### Passo a passo manual

Cada operação isolada, para inspecionar o resultado entre uma e outra:

```bash
# 1. Instalar as dependências no .venv do projeto
uv sync

# 2. Subir o servidor
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# 3. Abrir no navegador
open http://127.0.0.1:8000
```

### Testes

```bash
uv run pytest                       # suíte completa
uv run pytest backend/tests -v      # detalhado
uv run pytest backend/tests/test_line.py -k bresenham
```

Os testes não precisam do servidor no ar: as rotas são exercitadas pelo
`TestClient` do FastAPI.

---

## Como usar

### Ferramentas

| Ferramenta | Interação |
|---|---|
| **Ponto** | 1 clique |
| **Reta** | clique para ancorar → mova → clique para fechar |
| **Círculo** | clique no centro → mova → clique na borda |
| **Retângulo** | clique num canto → mova → clique no canto oposto |
| **Triângulo** | 3 cliques (A → B → C) |
| **Selecionar** | clique sobre uma figura |

**Cor** e **espessura** valem para o próximo primitivo criado e são aplicadas na
rasterização.

### Elásticos

Reta, círculo e retângulo têm comportamento tipo Paint: o primeiro clique
ancora, o movimento do mouse redimensiona a prévia continuamente e o segundo
clique confirma. `Esc` cancela, assim como trocar de ferramenta. Mudar cor ou
espessura com o elástico ativo atualiza a prévia na hora.

A prévia é traçada na sobreposição com a API 2D do navegador e **nunca vira
pixel da imagem** — é apenas um guia. O desenho definitivo continua vindo
inteiro dos algoritmos em Python. Fazer a prévia no servidor exigiria uma
mensagem por movimento do mouse, ou seja o WebSocket que ainda não foi feito.

### Seleção e remoção

Com a ferramenta **Selecionar**, o clique consulta o backend, que devolve a
figura mais próxima. O painel lateral mostra id, tipo, espessura, pontos e cor,
e a figura recebe um contorno tracejado na sobreposição.

Remove-se pelo botão **Remover selecionada** ou pela tecla `Delete`. Como nenhum
primitivo é preenchido, a seleção é feita pelo contorno: clicar no miolo de um
círculo ou retângulo não seleciona nada. A tolerância acompanha a espessura do
traço, com um mínimo de 4 pixels.

### Outros comandos

- **Redesenhar** — limpa a imagem e redesenha a ED, com filtro por tipo.
- **Limpar tela** — apaga os pixels e **preserva** a ED.
- **Limpar tudo** — apaga os pixels e a ED.

---

## Persistência

**Exportar** baixa dois arquivos com o mesmo carimbo de tempo:

- `figura-AAAAMMDD-HHMMSS.json` — a figura no formato abaixo;
- `figura-AAAAMMDD-HHMMSS.png` — a imagem rasterizada.

**Importar** lê um `.json` e substitui a figura, redesenhando pelos algoritmos do
Python. Um arquivo malformado é reportado no registro e **preserva o desenho
atual**: a nova figura só é adotada depois de lida por inteiro sem falhas.

### Formato do arquivo

Coordenadas normalizadas em `[0, 1]`, o que torna a figura independente da
resolução. `esp` em pixels, `id` sequencial por tipo.

```json
{
  "figura": {
    "ponto":     [{"x": 0.162, "y": 0.693, "cor": {"r": 0, "g": 102, "b": 102}, "esp": 50, "id": "ponto_1"}],
    "reta":      [{"p1": {"x": 0.669, "y": 0.434}, "p2": {"x": 0.669, "y": 0.484},
                   "cor": {"r": 79, "g": 56, "b": 7}, "esp": 12, "id": "reta_1"}],
    "triangulo": [{"p1": {"...": 0}, "p2": {"...": 0}, "p3": {"...": 0},
                   "cor": {"r": 255, "g": 153, "b": 153}, "esp": 6, "id": "triangulo_1"}],
    "retangulo": [{"p1": {"...": 0}, "p2": {"...": 0},
                   "cor": {"r": 0, "g": 102, "b": 102}, "esp": 18, "id": "retangulo_1"}],
    "circulo":   [{"centro": {"x": 0.246, "y": 0.320}, "raio": {"x": 0.643, "y": 0.500},
                   "cor": {"r": 102, "g": 0, "b": 255}, "esp": 10, "id": "circulo_1"}]
  }
}
```

Detalhes do formato:

- No **ponto**, `x` e `y` ficam no próprio item, sem objeto aninhado.
- No **círculo**, `raio` é um **ponto sobre a circunferência**, não um escalar:
  o raio efetivo é a distância entre `centro` e `raio`. É exatamente a interação
  de dois cliques (centro → borda).
- No **retângulo**, `p1` e `p2` são cantos opostos, em qualquer ordem.

---

## API

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/estado` | dimensões, primitivos da ED e id selecionado |
| `GET` | `/api/imagem` | buffer RGBA cru (`application/octet-stream`) |
| `POST` | `/api/primitivo` | cria um primitivo em coordenadas de pixel |
| `DELETE` | `/api/primitivo/{id}` | remove e redesenha |
| `POST` | `/api/selecionar` | `{x, y}` → id atingido ou `null` |
| `POST` | `/api/redesenhar` | `{tipo}` — limpa e redesenha filtrado |
| `POST` | `/api/limpar` | limpa a imagem; com `{"figura": true}` limpa a ED |
| `GET` | `/api/figura/exportar` | figura no formato JSON acima |
| `POST` | `/api/figura/importar` | substitui a figura e redesenha |

O buffer de pixels trafega como bytes crus, e não como JSON: 800×600×4 seriam
quase dois milhões de números por desenho.

O payload em pixels aceito por `/api/primitivo` é simétrico ao devolvido por
`/api/estado`. Ele não se confunde com o formato do arquivo, que é normalizado:

```bash
curl -X POST http://127.0.0.1:8000/api/primitivo \
  -H 'Content-Type: application/json' \
  -d '{"tipo":"circulo","centro":{"x":400,"y":300},"borda":{"x":500,"y":300},
       "cor":{"r":0,"g":102,"b":102},"esp":6}'
```

---

## O que assumir e o que pode dar errado

**A ordem entre tipos diferentes não sobrevive ao arquivo.** O formato agrupa os
primitivos por tipo, então não há onde gravar a ordem global de inserção. Ao
importar, a figura é remontada na ordem `ponto, reta, triangulo, retangulo,
circulo`. Isso só aparece quando figuras de **tipos diferentes se sobrepõem**:
elas voltam empilhadas em outra ordem. Nenhum dado é perdido — só a ordem muda.
É uma limitação do formato exigido, não da implementação.

**Precisão da normalização.** O arquivo grava 3 casas decimais. Em 800×600 o erro
máximo é 0,4 pixel, então pixel → arquivo → pixel é exato. O sentido inverso
tem quantização: um valor normalizado arbitrário não cai sobre um pixel e pode
deslocar até meio pixel.

**Estado único, em memória.** A aplicação é local e de usuário único: há uma
imagem e uma figura por processo, sem sessões nem banco. Reiniciar o servidor
apaga o desenho — use **Exportar** para guardar.

**Espessura grande.** `esp` não tem limite artificial. Valores como 50 são
válidos e recortados nas bordas da imagem, mas dominam um canvas de 800×600.

**Resolução fixa em 800×600.** Definida em `backend/app/api/routes.py`
(`LARGURA`, `ALTURA`). O frontend lê as dimensões de `/api/estado` e ajusta os
canvas sozinho.

### Problemas comuns

| Sintoma | Causa provável |
|---|---|
| `executar.sh` diz que a porta está ocupada | outro servidor no ar — veja com `lsof -i :8000 -sTCP:LISTEN` |
| `uv: command not found` | uv não instalado ou fora do PATH |
| A tela abre em branco e o registro mostra erro em `/api/imagem` | o servidor caiu; veja o terminal |
| Importar não faz nada | o registro mostra o motivo, com o tipo e o índice do item inválido |

---

## Próximos passos previstos

O `CLAUDE.md` prevê **WebSocket** para as atualizações interativas, enviando
apenas a região alterada em vez do buffer inteiro. Hoje a comunicação é REST e o
elástico é desenhado no cliente justamente para não precisar de uma mensagem por
movimento do mouse.
