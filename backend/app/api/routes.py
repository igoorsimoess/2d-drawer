"""Rotas REST do Desenhador2D.

A comunicacao e REST, como previsto no CLAUDE.md ("REST initially, WebSocket
later"). O buffer de pixels trafega como bytes crus em /api/imagem, e nao como
JSON: 800x600x4 sao quase dois milhoes de numeros, inviaveis de serializar a
cada desenho.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import APIRouter, Body, Response
from fastapi.responses import JSONResponse

from ..graphics import hittest
from ..graphics.figura import Figura, primitivo_de_payload
from ..graphics.image import Imagem
from ..graphics.serializacao import figura_para_json, json_para_figura

LARGURA = 800
ALTURA = 600

roteador = APIRouter(prefix="/api")


@dataclass
class Estado:
    """Estado unico da aplicacao: a imagem, a figura e a selecao corrente.

    A aplicacao e local e de usuario unico, entao um estado de modulo basta;
    nao ha sessoes nem persistencia em banco.
    """

    imagem: Imagem = field(default_factory=lambda: Imagem(LARGURA, ALTURA))
    figura: Figura = field(default_factory=Figura)
    selecionado: str | None = None

    def redesenhar(self, tipo: str = "all") -> int:
        """Limpa a imagem e redesenha a figura, opcionalmente filtrada por tipo."""
        self.imagem.limpar()
        return self.figura.desenhar(self.imagem, tipo)

    def reiniciar(self) -> None:
        """Volta ao estado inicial. Usado pelos testes."""
        self.imagem = Imagem(LARGURA, ALTURA)
        self.figura = Figura()
        self.selecionado = None


estado = Estado()


def erro(mensagem: str, codigo: int = 400) -> JSONResponse:
    """Resposta padronizada de erro."""
    return JSONResponse({"ok": False, "erro": mensagem}, status_code=codigo)


@roteador.get("/estado")
async def obter_estado() -> dict:
    """Dimensoes da imagem, primitivos da figura e id selecionado."""
    return {
        "largura": estado.imagem.largura,
        "altura": estado.imagem.altura,
        "figura": estado.figura.listar(),
        "contagem": estado.figura.contagem_por_tipo(),
        "selecionado": estado.selecionado,
    }


@roteador.get("/imagem")
async def obter_imagem() -> Response:
    """Buffer RGBA cru, pronto para virar um ImageData no canvas."""
    return Response(
        content=estado.imagem.para_bytes(),
        media_type="application/octet-stream",
        headers={
            "X-Largura": str(estado.imagem.largura),
            "X-Altura": str(estado.imagem.altura),
            "Cache-Control": "no-store",
        },
    )


@roteador.post("/primitivo")
async def criar_primitivo(payload: dict = Body(...)):
    """Cria um primitivo em coordenadas de pixel e o desenha sobre a imagem."""
    try:
        primitivo = primitivo_de_payload(payload)
    except ValueError as excecao:
        return erro(str(excecao))
    estado.figura.adicionar(primitivo)
    # Desenha so o novo primitivo: nao ha motivo para redesenhar tudo.
    primitivo.desenhar(estado.imagem)
    return {"ok": True, "primitivo": primitivo.para_dict()}


@roteador.delete("/primitivo/{id}")
async def remover_primitivo(id: str):
    """Remove o primitivo e redesenha a figura sem ele."""
    if not estado.figura.remover(id):
        return erro(f'primitivo "{id}" nao encontrado', codigo=404)
    if estado.selecionado == id:
        estado.selecionado = None
    estado.redesenhar()
    return {"ok": True, "removido": id}


@roteador.post("/selecionar")
async def selecionar(payload: dict = Body(...)):
    """Seleciona o primitivo atingido pelo clique, ou limpa a selecao."""
    try:
        x = float(payload["x"])
        y = float(payload["y"])
    except (KeyError, TypeError, ValueError):
        return erro('informe "x" e "y" numericos')

    estado.selecionado = hittest.encontrar(estado.figura, x, y)
    encontrado = (
        estado.figura.obter(estado.selecionado).para_dict()
        if estado.selecionado
        else None
    )
    return {"ok": True, "selecionado": estado.selecionado, "primitivo": encontrado}


@roteador.post("/redesenhar")
async def redesenhar(payload: dict = Body(default={})):
    """Limpa a imagem e redesenha a figura, com filtro opcional por tipo."""
    tipo = payload.get("tipo", "all")
    try:
        desenhados = estado.redesenhar(tipo)
    except ValueError as excecao:
        return erro(str(excecao))
    return {"ok": True, "desenhados": desenhados}


@roteador.post("/limpar")
async def limpar(payload: dict = Body(default={})):
    """Limpa a imagem. Com "figura": true, tambem esvazia a estrutura de dados."""
    estado.imagem.limpar()
    if payload.get("figura"):
        estado.figura.limpar()
        estado.selecionado = None
    return {"ok": True, "figura_limpa": bool(payload.get("figura"))}


@roteador.get("/figura/exportar")
async def exportar() -> dict:
    """Figura no formato JSON de persistencia, com coordenadas normalizadas."""
    return figura_para_json(estado.figura, estado.imagem.largura, estado.imagem.altura)


@roteador.post("/figura/importar")
async def importar(payload: dict = Body(...)):
    """Substitui a figura pelo conteudo do arquivo e redesenha.

    Em caso de erro a figura atual e preservada: a nova so e adotada depois
    de ser lida por inteiro sem falhas.
    """
    try:
        nova = json_para_figura(payload, estado.imagem.largura, estado.imagem.altura)
    except ValueError as excecao:
        return erro(str(excecao))
    estado.figura = nova
    estado.selecionado = None
    desenhados = estado.redesenhar()
    return {"ok": True, "importados": len(nova), "desenhados": desenhados}
