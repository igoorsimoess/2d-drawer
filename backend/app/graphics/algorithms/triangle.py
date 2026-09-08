"""Rasterizacao de triangulos a partir de tres vertices."""

from __future__ import annotations

from ..color import Cor
from ..image import Imagem
from ..point import Ponto2D
from .line import desenhar_reta


def desenhar_triangulo(
    imagem: Imagem, p1: Ponto2D, p2: Ponto2D, p3: Ponto2D, cor: Cor, esp: int = 1
) -> None:
    """Desenha o contorno do triangulo como tres retas de Bresenham."""
    desenhar_reta(imagem, p1, p2, cor, esp)
    desenhar_reta(imagem, p2, p3, cor, esp)
    desenhar_reta(imagem, p3, p1, cor, esp)
