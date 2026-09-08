"""Testes do algoritmo Midpoint de circunferencia."""

import math

import pytest

from backend.app.graphics.algorithms.circle import desenhar_circulo
from backend.app.graphics.image import Imagem
from backend.app.graphics.point import Ponto2D

from .conftest import TINTA, pixels_pintados

CENTRO = Ponto2D(10, 10)


def test_raio_zero_pinta_o_centro(imagem):
    desenhar_circulo(imagem, CENTRO, 0, TINTA)
    assert pixels_pintados(imagem) == {(10, 10)}


def test_raio_negativo_e_rejeitado(imagem):
    with pytest.raises(ValueError):
        desenhar_circulo(imagem, CENTRO, -1, TINTA)


def test_pontos_cardeais_sempre_presentes(imagem):
    raio = 7
    desenhar_circulo(imagem, CENTRO, raio, TINTA)
    pintados = pixels_pintados(imagem)
    for ponto in [
        (CENTRO.x + raio, CENTRO.y), (CENTRO.x - raio, CENTRO.y),
        (CENTRO.x, CENTRO.y + raio), (CENTRO.x, CENTRO.y - raio),
    ]:
        assert ponto in pintados


@pytest.mark.parametrize("raio", [1, 2, 3, 5, 8])
def test_todo_pixel_fica_a_um_raio_do_centro(raio):
    """Cada pixel pintado deve estar a menos de um pixel da circunferencia ideal."""
    img = Imagem(41, 41)
    centro = Ponto2D(20, 20)
    desenhar_circulo(img, centro, raio, TINTA)
    for x, y in pixels_pintados(img):
        distancia = math.hypot(x - centro.x, y - centro.y)
        assert abs(distancia - raio) < 1.0


@pytest.mark.parametrize("raio", [2, 4, 7])
def test_simetria_nos_oito_octantes(raio):
    """O conjunto pintado deve ser invariante as reflexoes em x, y e na diagonal."""
    img = Imagem(41, 41)
    centro = Ponto2D(20, 20)
    desenhar_circulo(img, centro, raio, TINTA)
    relativos = {(x - centro.x, y - centro.y) for x, y in pixels_pintados(img)}
    assert relativos == {(-dx, dy) for dx, dy in relativos}
    assert relativos == {(dx, -dy) for dx, dy in relativos}
    assert relativos == {(dy, dx) for dx, dy in relativos}


def test_circulo_e_vazado(imagem):
    """O algoritmo desenha o contorno, nao o disco: o centro fica limpo."""
    desenhar_circulo(imagem, CENTRO, 6, TINTA)
    assert (CENTRO.x, CENTRO.y) not in pixels_pintados(imagem)


def test_recorte_quando_o_circulo_extrapola_a_imagem():
    """Circulo maior que a imagem e recortado sem levantar excecao."""
    img = Imagem(21, 21)
    desenhar_circulo(img, Ponto2D(0, 0), 15, TINTA)
    assert len(pixels_pintados(img)) > 0
