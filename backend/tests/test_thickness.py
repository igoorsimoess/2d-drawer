"""Testes da espessura (esp) aplicada pelos algoritmos de rasterizacao."""

import pytest

from backend.app.graphics.algorithms.circle import desenhar_circulo
from backend.app.graphics.algorithms.line import desenhar_reta
from backend.app.graphics.algorithms.rectangle import desenhar_retangulo
from backend.app.graphics.algorithms.triangle import desenhar_triangulo
from backend.app.graphics.color import Cor
from backend.app.graphics.image import Imagem
from backend.app.graphics.point import Ponto2D

from .conftest import TINTA, pixels_pintados


@pytest.mark.parametrize("esp", [1, 2, 3, 4, 5, 8, 11])
def test_reta_horizontal_tem_a_largura_pedida(esp):
    """A secao transversal de uma reta horizontal deve medir esp pixels."""
    img = Imagem(81, 81)
    desenhar_reta(img, Ponto2D(20, 40), Ponto2D(60, 40), TINTA, esp)
    coluna = sorted(y for x, y in pixels_pintados(img) if x == 40)
    assert len(coluna) == esp
    assert coluna == list(range(coluna[0], coluna[0] + esp))


@pytest.mark.parametrize("esp", [1, 2, 3, 4, 5, 8, 11])
def test_reta_vertical_tem_a_largura_pedida(esp):
    img = Imagem(81, 81)
    desenhar_reta(img, Ponto2D(40, 20), Ponto2D(40, 60), TINTA, esp)
    linha = sorted(x for x, y in pixels_pintados(img) if y == 40)
    assert len(linha) == esp
    assert linha == list(range(linha[0], linha[0] + esp))


def test_espessura_maior_pinta_mais_pixels():
    """Monotonicidade: aumentar esp nunca reduz a area pintada."""
    anterior = 0
    for esp in range(1, 12):
        img = Imagem(81, 81)
        desenhar_reta(img, Ponto2D(10, 10), Ponto2D(70, 45), TINTA, esp)
        atual = len(pixels_pintados(img))
        assert atual > anterior
        anterior = atual


def test_espessura_nao_deixa_falhas_na_diagonal():
    """Um traco grosso na diagonal deve ser continuo, sem pixels isolados."""
    img = Imagem(81, 81)
    desenhar_reta(img, Ponto2D(10, 10), Ponto2D(70, 70), TINTA, 5)
    pintados = pixels_pintados(img)
    for x, y in pintados:
        vizinhos = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        assert any(v in pintados for v in vizinhos)


@pytest.mark.parametrize("esp", [1, 3, 6])
def test_circulo_com_espessura_mantem_o_centro_vazio(esp):
    """Mesmo grosso, o contorno nao deve fechar o miolo de um circulo grande."""
    img = Imagem(81, 81)
    desenhar_circulo(img, Ponto2D(40, 40), 25, TINTA, esp)
    assert (40, 40) not in pixels_pintados(img)


@pytest.mark.parametrize("esp", [2, 4, 7])
def test_retangulo_com_espessura_engrossa_as_arestas(esp):
    img = Imagem(81, 81)
    desenhar_retangulo(img, Ponto2D(20, 20), Ponto2D(60, 60), TINTA, esp)
    coluna = sorted(y for x, y in pixels_pintados(img) if x == 40)
    superior = [y for y in coluna if y < 40]
    assert len(superior) == esp


def test_triangulo_com_espessura_nao_levanta_excecao():
    img = Imagem(81, 81)
    desenhar_triangulo(
        img, Ponto2D(10, 10), Ponto2D(70, 20), Ponto2D(40, 70), TINTA, 9
    )
    assert len(pixels_pintados(img)) > 0


def test_espessura_grande_e_recortada_na_borda():
    """esp muito maior que a imagem nao pode estourar o buffer."""
    img = Imagem(21, 21)
    desenhar_reta(img, Ponto2D(10, 10), Ponto2D(10, 10), TINTA, 60)
    assert len(pixels_pintados(img)) == 21 * 21


def test_cor_do_traco_e_respeitada():
    img = Imagem(21, 21)
    cor = Cor(0, 102, 102)
    desenhar_reta(img, Ponto2D(2, 2), Ponto2D(18, 2), cor, 3)
    assert img.get_pixel(10, 2) == cor
