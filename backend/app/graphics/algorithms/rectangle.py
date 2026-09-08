"""Rasterizacao de retangulos alinhados aos eixos."""

from __future__ import annotations

from ..color import Cor
from ..image import Imagem
from ..point import Ponto2D
from .line import desenhar_reta


def desenhar_retangulo(
    imagem: Imagem, p1: Ponto2D, p2: Ponto2D, cor: Cor, esp: int = 1
) -> None:
    """Desenha o retangulo definido por dois cantos opostos.

    Os cantos podem vir em qualquer ordem: a normalizacao por min/max permite
    que o usuario arraste o elastico em qualquer direcao.
    """
    esquerda = min(p1.x, p2.x)
    direita = max(p1.x, p2.x)
    topo = min(p1.y, p2.y)
    base = max(p1.y, p2.y)

    superior_esq = Ponto2D(esquerda, topo)
    superior_dir = Ponto2D(direita, topo)
    inferior_esq = Ponto2D(esquerda, base)
    inferior_dir = Ponto2D(direita, base)

    desenhar_reta(imagem, superior_esq, superior_dir, cor, esp)
    desenhar_reta(imagem, superior_dir, inferior_dir, cor, esp)
    desenhar_reta(imagem, inferior_dir, inferior_esq, cor, esp)
    desenhar_reta(imagem, inferior_esq, superior_esq, cor, esp)
