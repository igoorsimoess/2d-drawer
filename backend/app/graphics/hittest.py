"""Selecao de primitivos por proximidade do clique.

A distancia e calculada analiticamente a partir da geometria de cada tipo,
sem varrer o buffer de pixels. Isso mantem a selecao barata e independente da
resolucao da imagem.
"""

from __future__ import annotations

import math

from .figura import Circulo, Figura, Ponto, Primitivo, Reta, Retangulo, Triangulo
from .point import Ponto2D

# Folga minima em pixels, para que tracos finos continuem clicaveis.
TOLERANCIA_MINIMA = 4.0


def distancia_ponto_segmento(px: float, py: float, a: Ponto2D, b: Ponto2D) -> float:
    """Menor distancia entre o ponto (px, py) e o segmento AB."""
    dx = b.x - a.x
    dy = b.y - a.y
    if dx == 0 and dy == 0:
        return math.hypot(px - a.x, py - a.y)
    # Projecao escalar do ponto sobre o segmento, limitada ao intervalo [0, 1]
    # para que a distancia seja ate o segmento, e nao ate a reta infinita.
    t = ((px - a.x) * dx + (py - a.y) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (a.x + t * dx), py - (a.y + t * dy))


def _menor_distancia_ate_arestas(px: float, py: float, vertices: list[Ponto2D]) -> float:
    """Menor distancia do ponto ate o contorno fechado formado pelos vertices."""
    return min(
        distancia_ponto_segmento(px, py, vertices[i], vertices[(i + 1) % len(vertices)])
        for i in range(len(vertices))
    )


def distancia_ate(primitivo: Primitivo, px: float, py: float) -> float:
    """Distancia do ponto ate o contorno desenhado do primitivo."""
    if isinstance(primitivo, Ponto):
        return math.hypot(px - primitivo.p.x, py - primitivo.p.y)
    if isinstance(primitivo, Reta):
        return distancia_ponto_segmento(px, py, primitivo.p1, primitivo.p2)
    if isinstance(primitivo, Triangulo):
        return _menor_distancia_ate_arestas(
            px, py, [primitivo.p1, primitivo.p2, primitivo.p3]
        )
    if isinstance(primitivo, Retangulo):
        esquerda = min(primitivo.p1.x, primitivo.p2.x)
        direita = max(primitivo.p1.x, primitivo.p2.x)
        topo = min(primitivo.p1.y, primitivo.p2.y)
        base = max(primitivo.p1.y, primitivo.p2.y)
        cantos = [
            Ponto2D(esquerda, topo), Ponto2D(direita, topo),
            Ponto2D(direita, base), Ponto2D(esquerda, base),
        ]
        return _menor_distancia_ate_arestas(px, py, cantos)
    if isinstance(primitivo, Circulo):
        # O circulo e vazado: a distancia e ate a circunferencia, nao ate o centro.
        centro = math.hypot(px - primitivo.centro.x, py - primitivo.centro.y)
        return abs(centro - primitivo.raio)
    raise ValueError(f'tipo sem regra de selecao: "{primitivo.tipo}"')


def tolerancia(primitivo: Primitivo) -> float:
    """Folga aceita para considerar o clique como acerto.

    Acompanha a espessura do traco, com um minimo fixo para que primitivos
    de 1 pixel nao exijam precisao impossivel do usuario.
    """
    return max(primitivo.esp / 2.0, TOLERANCIA_MINIMA)


def encontrar(figura: Figura, px: float, py: float) -> str | None:
    """Retorna o id do primitivo atingido pelo clique, ou None.

    A busca vai do ultimo para o primeiro primitivo, de modo que a figura
    desenhada por cima e a selecionada quando varias se sobrepoem.
    """
    for primitivo in reversed(figura.primitivos):
        if distancia_ate(primitivo, px, py) <= tolerancia(primitivo):
            return primitivo.id
    return None
