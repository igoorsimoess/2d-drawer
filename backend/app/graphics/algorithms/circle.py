"""Rasterizacao de circunferencias pelo algoritmo Midpoint."""

from __future__ import annotations

from ..color import Cor
from ..image import Imagem
from ..point import Ponto2D


def desenhar_circulo(
    imagem: Imagem, centro: Ponto2D, raio: int, cor: Cor, esp: int = 1
) -> None:
    """Desenha a circunferencia de centro e raio dados.

    O algoritmo Midpoint calcula apenas o primeiro octante e reflete cada
    pixel nas oito posicoes simetricas, usando somente aritmetica inteira.
    """
    raio = int(raio)
    if raio < 0:
        raise ValueError("o raio nao pode ser negativo")
    if raio == 0:
        imagem.carimbar(centro.x, centro.y, cor, esp)
        return

    x = 0
    y = raio
    decisao = 1 - raio
    _refletir_octantes(imagem, centro, x, y, cor, esp)
    while x < y:
        x += 1
        if decisao < 0:
            decisao += 2 * x + 1
        else:
            y -= 1
            decisao += 2 * (x - y) + 1
        _refletir_octantes(imagem, centro, x, y, cor, esp)


def _refletir_octantes(
    imagem: Imagem, centro: Ponto2D, x: int, y: int, cor: Cor, esp: int
) -> None:
    """Pinta as oito posicoes simetricas correspondentes a (x, y)."""
    xc, yc = centro.x, centro.y
    for px, py in (
        (xc + x, yc + y), (xc - x, yc + y), (xc + x, yc - y), (xc - x, yc - y),
        (xc + y, yc + x), (xc - y, yc + x), (xc + y, yc - x), (xc - y, yc - x),
    ):
        imagem.carimbar(px, py, cor, esp)
