"""Utilitarios compartilhados pelos testes."""

import numpy as np
import pytest

from backend.app.graphics.color import BRANCO, Cor
from backend.app.graphics.image import Imagem

TINTA = Cor(0, 0, 0)


@pytest.fixture
def imagem():
    """Imagem pequena e quadrada, suficiente para inspecionar pixel a pixel."""
    return Imagem(21, 21)


def pixels_pintados(imagem: Imagem) -> set[tuple[int, int]]:
    """Conjunto de coordenadas (x, y) que diferem da cor de fundo."""
    fundo = np.array(BRANCO.para_rgba(), dtype=np.uint8)
    diferentes = np.any(imagem.buffer != fundo, axis=2)
    ys, xs = np.nonzero(diferentes)
    return set(zip(xs.tolist(), ys.tolist()))
