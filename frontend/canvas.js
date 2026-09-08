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

/* Quantos cliques cada ferramenta precisa para fechar um primitivo. */
const CLIQUES = { ponto: 1, reta: 2, circulo: 2, retangulo: 2, triangulo: 3 };

let estado = { largura: 800, altura: 600, figura: [], selecionado: null };
let pendentes = [];

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
  return pedir(rota, {
    method: metodo,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  });
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

function renderizarPainel() {
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

function limparSobreposicao() {
  contextoSobreposicao.clearRect(0, 0, sobreposicao.width, sobreposicao.height);
}

function cancelarPendentes() {
  if (pendentes.length > 0) registrar("Primitivo em andamento cancelado.");
  pendentes = [];
  limparSobreposicao();
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
  const necessarios = CLIQUES[ferramenta];
  if (!necessarios) return;

  pendentes.push(coordenadas(evento));
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

/* ------------------------------------------------------------------ eventos */

sobreposicao.addEventListener("click", aoClicar);

ferramentaEl.addEventListener("change", () => {
  cancelarPendentes();
  registrar(`Ferramenta: ${ferramentaEl.value}.`);
});

document.addEventListener("keydown", (evento) => {
  if (evento.key === "Escape") cancelarPendentes();
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
