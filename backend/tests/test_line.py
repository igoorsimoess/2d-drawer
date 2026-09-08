"""Testes do algoritmo de Bresenham."""

import pytest

from backend.app.graphics.algorithms.line import desenhar_reta
from backend.app.graphics.image import Imagem
from backend.app.graphics.point import Ponto2D

from .conftest import TINTA, pixels_pintados


def test_reta_horizontal(imagem):
    desenhar_reta(imagem, Ponto2D(2, 5), Ponto2D(8, 5), TINTA)
    assert pixels_pintados(imagem) == {(x, 5) for x in range(2, 9)}


def test_reta_vertical(imagem):
    desenhar_reta(imagem, Ponto2D(4, 1), Ponto2D(4, 6), TINTA)
    assert pixels_pintados(imagem) == {(4, y) for y in range(1, 7)}


def test_diagonal_perfeita(imagem):
    desenhar_reta(imagem, Ponto2D(0, 0), Ponto2D(5, 5), TINTA)
    assert pixels_pintados(imagem) == {(i, i) for i in range(6)}


def test_ponto_degenerado(imagem):
    """Uma reta de um ponto a ele mesmo pinta exatamente um pixel."""
    desenhar_reta(imagem, Ponto2D(3, 3), Ponto2D(3, 3), TINTA)
    assert pixels_pintados(imagem) == {(3, 3)}


def test_inverter_a_direcao_mantem_extremos_e_quantidade(imagem):
    """Bresenham inteiro nao e simetrico: nos empates o desempate segue a origem.

    Trocar A por B pode deslocar pixels intermediarios em um pixel, mas a
    quantidade de pixels e os dois extremos precisam ser os mesmos.
    """
    outra = Imagem(21, 21)
    a, b = Ponto2D(1, 2), Ponto2D(15, 9)
    desenhar_reta(imagem, a, b, TINTA)
    desenhar_reta(outra, b, a, TINTA)
    ida, volta = pixels_pintados(imagem), pixels_pintados(outra)
    assert len(ida) == len(volta)
    for extremo in ((a.x, a.y), (b.x, b.y)):
        assert extremo in ida and extremo in volta


def test_inclinacao_suave_conhecida(imagem):
    """Caso classico de Bresenham com dx > dy, comparado pixel a pixel."""
    desenhar_reta(imagem, Ponto2D(0, 0), Ponto2D(6, 3), TINTA)
    assert pixels_pintados(imagem) == {(0, 0), (1, 0), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3)}


def test_um_pixel_por_coluna_quando_dx_maior(imagem):
    """Com dx > dy, cada coluna do intervalo recebe exatamente um pixel."""
    desenhar_reta(imagem, Ponto2D(0, 0), Ponto2D(20, 7), TINTA)
    pintados = pixels_pintados(imagem)
    for x in range(21):
        assert len([p for p in pintados if p[0] == x]) == 1


@pytest.mark.parametrize(
    "destino",
    [Ponto2D(20, 0), Ponto2D(0, 20), Ponto2D(20, 20), Ponto2D(0, 0)],
)
def test_recorte_fora_da_imagem_nao_quebra(destino):
    """Retas que saem da imagem sao recortadas sem levantar excecao."""
    img = Imagem(21, 21)
    desenhar_reta(img, Ponto2D(-30, -30), destino, TINTA)
    assert len(pixels_pintados(img)) > 0
