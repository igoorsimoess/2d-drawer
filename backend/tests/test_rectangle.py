"""Testes do retangulo e do triangulo, compostos por retas de Bresenham."""

from backend.app.graphics.algorithms.rectangle import desenhar_retangulo
from backend.app.graphics.algorithms.triangle import desenhar_triangulo
from backend.app.graphics.image import Imagem
from backend.app.graphics.point import Ponto2D

from .conftest import TINTA, pixels_pintados


def contorno_esperado(x0, y0, x1, y1):
    """Conjunto de pixels do contorno de um retangulo alinhado aos eixos."""
    horizontais = {(x, y) for x in range(x0, x1 + 1) for y in (y0, y1)}
    verticais = {(x, y) for y in range(y0, y1 + 1) for x in (x0, x1)}
    return horizontais | verticais


def test_contorno_completo(imagem):
    desenhar_retangulo(imagem, Ponto2D(2, 3), Ponto2D(9, 8), TINTA)
    assert pixels_pintados(imagem) == contorno_esperado(2, 3, 9, 8)


def test_interior_permanece_vazio(imagem):
    desenhar_retangulo(imagem, Ponto2D(2, 2), Ponto2D(10, 10), TINTA)
    assert (6, 6) not in pixels_pintados(imagem)


def test_cantos_em_qualquer_ordem_dao_o_mesmo_resultado():
    """O elastico pode ser arrastado em qualquer direcao."""
    esperado = contorno_esperado(2, 3, 9, 8)
    for a, b in [
        (Ponto2D(2, 3), Ponto2D(9, 8)),
        (Ponto2D(9, 8), Ponto2D(2, 3)),
        (Ponto2D(9, 3), Ponto2D(2, 8)),
        (Ponto2D(2, 8), Ponto2D(9, 3)),
    ]:
        img = Imagem(21, 21)
        desenhar_retangulo(img, a, b, TINTA)
        assert pixels_pintados(img) == esperado


def test_retangulo_degenerado_vira_reta(imagem):
    desenhar_retangulo(imagem, Ponto2D(3, 5), Ponto2D(8, 5), TINTA)
    assert pixels_pintados(imagem) == {(x, 5) for x in range(3, 9)}


def test_triangulo_tem_os_tres_vertices(imagem):
    vertices = [Ponto2D(2, 2), Ponto2D(15, 4), Ponto2D(8, 16)]
    desenhar_triangulo(imagem, *vertices, TINTA)
    pintados = pixels_pintados(imagem)
    for v in vertices:
        assert (v.x, v.y) in pintados


def test_triangulo_e_fechado(imagem):
    """Cada aresta liga dois vertices, entao o contorno nao tem falhas."""
    a, b, c = Ponto2D(2, 2), Ponto2D(14, 2), Ponto2D(8, 14)
    desenhar_triangulo(imagem, a, b, c, TINTA)
    pintados = pixels_pintados(imagem)
    assert {(x, 2) for x in range(2, 15)}.issubset(pintados)
    assert (8, 8) not in pintados
