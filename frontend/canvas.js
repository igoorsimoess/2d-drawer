/*
 * Interface do Desenhador2D.
 *
 * A imagem exibida vem sempre do backend: /api/imagem devolve o buffer RGBA
 * cru, que vira um ImageData e e escrito no canvas. Nenhum pixel e
 * rasterizado aqui - os algoritmos ficam todos no Python.
 */

const tela = document.getElementById("tela");
const contexto = tela.getContext("2d");
const sobreposicao = document.getElementById("sobreposicao");
const contextoSobreposicao = sobreposicao.getContext("2d");

const ferramentaEl = document.getElementById("ferramenta");
const corEl = document.getElementById("cor");
const espessuraEl = document.getElementById("espessura");
const filtroEl = document.getElementById("filtro");
const resumoEl = document.getElementById("resumo");
const listaEl = document.getElementById("lista");
const logEl = document.getElementById("log");
const semSelecaoEl = document.getElementById("semSelecao");
const detalhesEl = document.getElementById("detalhes");
const removerEl = document.getElementById("remover");
const arquivoEl = document.getElementById("arquivo");

/* Quantos cliques cada ferramenta precisa para fechar um primitivo. */
const CLIQUES = { ponto: 1, reta: 2, circulo: 2, retangulo: 2, triangulo: 3 };

let estado = { largura: 800, altura: 600, figura: [], selecionado: null };
let pendentes = []; /* cliques acumulados das ferramentas sem elastico */
let ancora = null; /* primeiro ponto das ferramentas com elastico */
let cursor = null; /* ultima posicao conhecida do mouse, em pixels */

/* ---------------------------------------------------------------- registro */

function registrar(mensagem, ehErro = false) {
  const linha = document.createElement("div");
  linha.textContent = `[${new Date().toLocaleTimeString()}] ${mensagem}`;
  if (ehErro) linha.className = "erro";
  logEl.appendChild(linha);
  while (logEl.children.length > 200) logEl.removeChild(logEl.firstChild);
  logEl.scrollTop = logEl.scrollHeight;
}

/* ------------------------------------------------------------ comunicacao */

/** Faz a requisicao e devolve o JSON, ou null quando o backend recusa. */
async function pedir(rota, opcoes = {}) {
  try {
    const resposta = await fetch(rota, opcoes);
    const corpo = await resposta.json();
    if (!resposta.ok) {
      registrar(`${rota}: ${corpo.erro || resposta.status}`, true);
      return null;
    }
    return corpo;
  } catch (erro) {
    registrar(`${rota}: falha de rede (${erro})`, true);
    return null;
  }
}

async function enviarJson(rota, dados, metodo = "POST") {
  const opcoes = { method: metodo };
  if (dados !== null) {
    opcoes.headers = { "Content-Type": "application/json" };
    opcoes.body = JSON.stringify(dados);
  }
  return pedir(rota, opcoes);
}

/* -------------------------------------------------------------- renderizacao */

/** Busca o buffer RGBA no backend e o escreve no canvas via ImageData. */
async function carregarImagem() {
  try {
    const resposta = await fetch("/api/imagem");
    if (!resposta.ok) {
      registrar(`/api/imagem: ${resposta.status}`, true);
      return;
    }
    const bytes = new Uint8ClampedArray(await resposta.arrayBuffer());
    contexto.putImageData(new ImageData(bytes, tela.width, tela.height), 0, 0);
  } catch (erro) {
    registrar(`/api/imagem: falha de rede (${erro})`, true);
  }
}

async function carregarEstado() {
  const dados = await pedir("/api/estado");
  if (!dados) return;
  estado = dados;
  ajustarDimensoes();
  renderizarPainel();
}

/** Alinha os dois canvas as dimensoes informadas pelo backend. */
function ajustarDimensoes() {
  for (const alvo of [tela, sobreposicao]) {
    if (alvo.width !== estado.largura || alvo.height !== estado.altura) {
      alvo.width = estado.largura;
      alvo.height = estado.altura;
    }
  }
}

async function atualizarTudo() {
  await carregarEstado();
  await carregarImagem();
  renderizarSobreposicao();
}

/* ------------------------------------------------------------------ painel */

function descrever(primitivo) {
  const ponto = (p) => `(${p.x},${p.y})`;
  switch (primitivo.tipo) {
    case "ponto": return ponto(primitivo.p);
    case "reta":
    case "retangulo": return `${ponto(primitivo.p1)} ${ponto(primitivo.p2)}`;
    case "triangulo": return `${ponto(primitivo.p1)} ${ponto(primitivo.p2)} ${ponto(primitivo.p3)}`;
    case "circulo": return `centro ${ponto(primitivo.centro)} raio ${primitivo.raio}`;
    default: return "";
  }
}

/** Primitivo atualmente selecionado, ou null. */
function selecionado() {
  return estado.figura.find((p) => p.id === estado.selecionado) || null;
}

/** Mostra os dados da figura selecionada, para conferencia antes de remover. */
function renderizarSelecao() {
  const alvo = selecionado();
  semSelecaoEl.hidden = alvo !== null;
  detalhesEl.hidden = alvo === null;
  removerEl.hidden = alvo === null;
  detalhesEl.innerHTML = "";
  if (!alvo) return;

  const linhas = [
    ["id", alvo.id],
    ["tipo", alvo.tipo],
    ["esp", String(alvo.esp)],
    ["pontos", descrever(alvo)],
  ];
  for (const [rotulo, valor] of linhas) {
    detalhesEl.appendChild(Object.assign(document.createElement("dt"), { textContent: rotulo }));
    detalhesEl.appendChild(Object.assign(document.createElement("dd"), { textContent: valor }));
  }

  detalhesEl.appendChild(Object.assign(document.createElement("dt"), { textContent: "cor" }));
  const valorCor = document.createElement("dd");
  const amostra = document.createElement("span");
  amostra.className = "amostra";
  amostra.style.background = paraHex(alvo.cor);
  valorCor.append(amostra, paraHex(alvo.cor));
  detalhesEl.appendChild(valorCor);
}

function renderizarPainel() {
  renderizarSelecao();
  const total = estado.figura.length;
  if (total === 0) {
    resumoEl.textContent = "Nenhum primitivo na figura.";
  } else {
    const partes = Object.entries(estado.contagem || {})
      .map(([tipo, quantidade]) => `${quantidade} ${tipo}`)
      .join(", ");
    resumoEl.textContent = `${total} primitivo(s): ${partes}.`;
  }

  listaEl.innerHTML = "";
  for (const primitivo of estado.figura) {
    const item = document.createElement("li");

    const amostra = document.createElement("span");
    amostra.className = "amostra";
    amostra.style.background = paraHex(primitivo.cor);
    item.appendChild(amostra);

    const texto = document.createElement("span");
    texto.textContent = `${primitivo.id} esp=${primitivo.esp} ${descrever(primitivo)}`;
    item.appendChild(texto);

    if (primitivo.id === estado.selecionado) item.className = "selecionado";
    listaEl.appendChild(item);
  }
}

/* ------------------------------------------------------------------- cores */

/** Converte "#rrggbb" do seletor de cor para {r, g, b}. */
function corAtual() {
  const hex = corEl.value;
  return {
    r: parseInt(hex.slice(1, 3), 16),
    g: parseInt(hex.slice(3, 5), 16),
    b: parseInt(hex.slice(5, 7), 16),
  };
}

function paraHex(cor) {
  const canal = (v) => v.toString(16).padStart(2, "0");
  return `#${canal(cor.r)}${canal(cor.g)}${canal(cor.b)}`;
}

function espessuraAtual() {
  return Math.max(1, parseInt(espessuraEl.value, 10) || 1);
}

/* -------------------------------------------------------------- coordenadas */

/**
 * Converte a posicao do mouse para coordenadas de pixel da imagem.
 * O canvas pode estar reescalado pelo CSS, entao a razao entre a largura
 * intrinseca e a exibida precisa ser aplicada.
 */
function coordenadas(evento) {
  const area = sobreposicao.getBoundingClientRect();
  const x = Math.floor((evento.clientX - area.left) * (sobreposicao.width / area.width));
  const y = Math.floor((evento.clientY - area.top) * (sobreposicao.height / area.height));
  return {
    x: Math.min(Math.max(x, 0), sobreposicao.width - 1),
    y: Math.min(Math.max(y, 0), sobreposicao.height - 1),
  };
}

/* ------------------------------------------------------------------ desenho */

/*
 * Ferramentas com elastico: o primeiro clique ancora, o movimento do mouse
 * redesenha a previa na sobreposicao e o segundo clique confirma.
 *
 * A previa e tracada com a API 2D do navegador, e nao com os algoritmos do
 * backend. E um guia transitorio que nunca vira pixel da imagem: o desenho
 * definitivo continua vindo inteiro do Python. Fazer a previa no servidor
 * exigiria uma mensagem por movimento do mouse, ou seja o WebSocket que o
 * CLAUDE.md deixa para depois.
 */
const ELASTICOS = new Set(["reta", "circulo", "retangulo"]);

function limparSobreposicao() {
  contextoSobreposicao.clearRect(0, 0, sobreposicao.width, sobreposicao.height);
}

/** Redesenha a sobreposicao inteira: elastico e marcador da ancora. */
function renderizarSobreposicao() {
  limparSobreposicao();
  desenharSelecao();
  desenharElastico();
}

/**
 * Contorno tracejado ao redor da figura selecionada.
 * Fica na sobreposicao, entao a imagem rasterizada nao e alterada.
 */
function desenharSelecao() {
  const alvo = selecionado();
  if (!alvo || !alvo.caixa) return;

  const folga = Math.ceil(alvo.esp / 2) + 4;
  const [x0, y0, x1, y1] = alvo.caixa;
  const ctx = contextoSobreposicao;
  ctx.save();
  ctx.strokeStyle = "#2563eb";
  ctx.lineWidth = 1;
  ctx.setLineDash([6, 4]);
  ctx.strokeRect(
    x0 - folga + 0.5,
    y0 - folga + 0.5,
    x1 - x0 + folga * 2,
    y1 - y0 + folga * 2,
  );
  ctx.restore();
}

/** Traca a previa do primitivo entre a ancora e a posicao atual do cursor. */
function desenharElastico() {
  if (!ancora || !cursor) return;
  const ferramenta = ferramentaEl.value;
  if (!ELASTICOS.has(ferramenta)) return;

  const ctx = contextoSobreposicao;
  ctx.save();
  ctx.strokeStyle = corEl.value;
  ctx.lineWidth = espessuraAtual();
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.globalAlpha = 0.7;

  ctx.beginPath();
  if (ferramenta === "reta") {
    ctx.moveTo(ancora.x, ancora.y);
    ctx.lineTo(cursor.x, cursor.y);
  } else if (ferramenta === "circulo") {
    const raio = Math.round(Math.hypot(cursor.x - ancora.x, cursor.y - ancora.y));
    if (raio > 0) ctx.arc(ancora.x, ancora.y, raio, 0, Math.PI * 2);
  } else {
    ctx.rect(
      Math.min(ancora.x, cursor.x),
      Math.min(ancora.y, cursor.y),
      Math.abs(cursor.x - ancora.x),
      Math.abs(cursor.y - ancora.y),
    );
  }
  ctx.stroke();
  ctx.restore();

  desenharAncora();
}

/** Cruz discreta no ponto ancorado, para deixar claro onde o elastico prende. */
function desenharAncora() {
  const ctx = contextoSobreposicao;
  const braco = 6;
  ctx.save();
  ctx.strokeStyle = "#111827";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(ancora.x - braco, ancora.y);
  ctx.lineTo(ancora.x + braco, ancora.y);
  ctx.moveTo(ancora.x, ancora.y - braco);
  ctx.lineTo(ancora.x, ancora.y + braco);
  ctx.stroke();
  ctx.restore();
}

/* Limita o redesenho da previa a um por quadro, para que arrastar o mouse
   nao dispare dezenas de tracados por segundo. */
let quadroAgendado = false;

function agendarQuadro() {
  if (quadroAgendado) return;
  quadroAgendado = true;
  requestAnimationFrame(() => {
    quadroAgendado = false;
    renderizarSobreposicao();
  });
}

function cancelarPendentes() {
  const havia = ancora !== null || pendentes.length > 0;
  ancora = null;
  pendentes = [];
  limparSobreposicao();
  if (havia) registrar("Primitivo em andamento cancelado.");
}

/** Monta o payload em coordenadas de pixel esperado por /api/primitivo. */
function montarPayload(ferramenta, pontos) {
  const base = { tipo: ferramenta, cor: corAtual(), esp: espessuraAtual() };
  switch (ferramenta) {
    case "ponto": return { ...base, p: pontos[0] };
    case "reta":
    case "retangulo": return { ...base, p1: pontos[0], p2: pontos[1] };
    case "triangulo": return { ...base, p1: pontos[0], p2: pontos[1], p3: pontos[2] };
    case "circulo": return { ...base, centro: pontos[0], borda: pontos[1] };
    default: return null;
  }
}

async function criarPrimitivo(ferramenta, pontos) {
  const resposta = await enviarJson("/api/primitivo", montarPayload(ferramenta, pontos));
  if (!resposta) return;
  registrar(`Criado ${resposta.primitivo.id}: ${descrever(resposta.primitivo)}`);
  await atualizarTudo();
}

async function aoClicar(evento) {
  const ferramenta = ferramentaEl.value;
  const ponto = coordenadas(evento);

  if (ferramenta === "selecionar") {
    await selecionarEm(ponto);
    return;
  }

  if (ELASTICOS.has(ferramenta)) {
    if (ancora === null) {
      ancora = ponto;
      cursor = ponto;
      renderizarSobreposicao();
      registrar(`${ferramenta}: ancorado em (${ponto.x},${ponto.y}). Mova e clique para fechar.`);
      return;
    }
    const inicio = ancora;
    ancora = null;
    limparSobreposicao();
    await criarPrimitivo(ferramenta, [inicio, ponto]);
    return;
  }

  const necessarios = CLIQUES[ferramenta];
  if (!necessarios) return;

  pendentes.push(ponto);
  if (pendentes.length < necessarios) {
    const faltam = necessarios - pendentes.length;
    registrar(`${ferramenta}: ${pendentes.length} de ${necessarios} pontos (faltam ${faltam}).`);
    return;
  }

  const pontos = pendentes;
  pendentes = [];
  limparSobreposicao();
  await criarPrimitivo(ferramenta, pontos);
}

async function selecionarEm(ponto) {
  const resposta = await enviarJson("/api/selecionar", ponto);
  if (!resposta) return;
  estado.selecionado = resposta.selecionado;
  registrar(
    resposta.selecionado
      ? `Selecionado ${resposta.selecionado}: ${descrever(resposta.primitivo)}`
      : "Nenhuma figura sob o clique. Selecao limpa.",
  );
  renderizarPainel();
  renderizarSobreposicao();
}

async function removerSelecionada() {
  if (!estado.selecionado) return;
  const id = estado.selecionado;
  const resposta = await enviarJson(`/api/primitivo/${id}`, null, "DELETE");
  if (!resposta) return;
  registrar(`Removido ${id}.`);
  await atualizarTudo();
  renderizarSobreposicao();
}

function aoMover(evento) {
  cursor = coordenadas(evento);
  if (ancora !== null) agendarQuadro();
}

/* -------------------------------------------------------------- persistencia */

/** Entrega um blob ao usuario como download. */
function baixar(blob, nome) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = nome;
  document.body.appendChild(link);
  link.click();
  link.remove();
  /* A revogacao imediata pode cancelar o download em alguns navegadores. */
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function carimboDeTempo() {
  const agora = new Date();
  const doisDigitos = (v) => String(v).padStart(2, "0");
  return (
    `${agora.getFullYear()}${doisDigitos(agora.getMonth() + 1)}${doisDigitos(agora.getDate())}` +
    `-${doisDigitos(agora.getHours())}${doisDigitos(agora.getMinutes())}${doisDigitos(agora.getSeconds())}`
  );
}

/**
 * Exporta a figura em JSON e a imagem em PNG.
 *
 * O PNG sai do proprio canvas, que e copia byte a byte do buffer NumPy, entao
 * o resultado e o mesmo que gerar a imagem no servidor - sem precisar de uma
 * biblioteca de codificacao de imagem no backend.
 */
async function exportar() {
  const dados = await pedir("/api/figura/exportar");
  if (!dados) return;

  const nome = `figura-${carimboDeTempo()}`;
  baixar(
    new Blob([JSON.stringify(dados, null, 2)], { type: "application/json" }),
    `${nome}.json`,
  );
  tela.toBlob((imagem) => {
    if (imagem) baixar(imagem, `${nome}.png`);
    else registrar("Nao foi possivel gerar o PNG da imagem.", true);
  }, "image/png");

  registrar(`Exportados ${nome}.json e ${nome}.png (${estado.figura.length} primitivo(s)).`);
}

/** Le o arquivo escolhido e substitui a figura atual pelo seu conteudo. */
async function importarArquivo(arquivo) {
  let dados;
  try {
    dados = JSON.parse(await arquivo.text());
  } catch (erro) {
    registrar(`${arquivo.name}: JSON invalido (${erro.message})`, true);
    return;
  }

  const resposta = await enviarJson("/api/figura/importar", dados);
  if (!resposta) return;
  cancelarPendentes();
  registrar(`Importados ${resposta.importados} primitivo(s) de ${arquivo.name}.`);
  await atualizarTudo();
}

/* ------------------------------------------------------------------ eventos */

sobreposicao.addEventListener("click", aoClicar);
sobreposicao.addEventListener("mousemove", aoMover);

ferramentaEl.addEventListener("change", () => {
  cancelarPendentes();
  registrar(`Ferramenta: ${ferramentaEl.value}.`);
});

/* Mudar cor ou espessura com o elastico ativo atualiza a previa na hora. */
corEl.addEventListener("input", agendarQuadro);
espessuraEl.addEventListener("input", agendarQuadro);

removerEl.addEventListener("click", removerSelecionada);

document.getElementById("exportar").addEventListener("click", exportar);

document.getElementById("importar").addEventListener("click", () => arquivoEl.click());

arquivoEl.addEventListener("change", async () => {
  const arquivo = arquivoEl.files[0];
  /* Zera o campo para que escolher o mesmo arquivo de novo dispare o evento. */
  arquivoEl.value = "";
  if (arquivo) await importarArquivo(arquivo);
});

document.addEventListener("keydown", (evento) => {
  if (evento.key === "Escape") {
    cancelarPendentes();
    return;
  }
  /* Delete so remove fora de campos de texto, para nao atrapalhar a digitacao. */
  const digitando = ["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName);
  if ((evento.key === "Delete" || evento.key === "Backspace") && !digitando) {
    if (!estado.selecionado) return;
    evento.preventDefault();
    removerSelecionada();
  }
});

document.getElementById("redesenhar").addEventListener("click", async () => {
  const resposta = await enviarJson("/api/redesenhar", { tipo: filtroEl.value });
  if (!resposta) return;
  registrar(`Redesenhados ${resposta.desenhados} primitivo(s) (${filtroEl.value}).`);
  await atualizarTudo();
});

document.getElementById("limparTela").addEventListener("click", async () => {
  if (!(await enviarJson("/api/limpar", {}))) return;
  registrar("Tela limpa. A estrutura de dados foi preservada.");
  await atualizarTudo();
});

document.getElementById("limparTudo").addEventListener("click", async () => {
  if (!(await enviarJson("/api/limpar", { figura: true }))) return;
  cancelarPendentes();
  registrar("Tela e estrutura de dados limpas.");
  await atualizarTudo();
});

registrar("Interface iniciada.");
atualizarTudo();
