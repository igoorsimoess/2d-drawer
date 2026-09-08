"""Rasterizacao de retas pelo algoritmo de Bresenham."""

from __future__ import annotations

from ..color import Cor
from ..image import Imagem
from ..point import Ponto2D


def desenhar_reta(imagem: Imagem, p1: Ponto2D, p2: Ponto2D, cor: Cor, esp: int = 1) -> None:
    """Desenha a reta de p1 ate p2 usando somente aritmetica inteira.

    O algoritmo de Bresenham decide, a cada passo, qual o proximo pixel mais
    proximo da reta ideal, acumulando o erro em vez de usar ponto flutuante.
    A espessura vem do carimbo de disco da Imagem.
    """
    x0, y0 = p1.x, p1.y
    x1, y1 = p2.x, p2.y

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    erro = dx - dy

    while True:
        imagem.carimbar(x0, y0, cor, esp)
        if x0 == x1 and y0 == y1:
            break
        erro2 = 2 * erro
        if erro2 > -dy:
            erro -= dy
            x0 += sx
        if erro2 < dx:
            erro += dx
            y0 += sy
