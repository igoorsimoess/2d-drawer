"""Testes da selecao de primitivos por proximidade."""

import pytest

from backend.app.graphics.color import Cor
from backend.app.graphics.figura import Circulo, Figura, Ponto, Reta, Retangulo, Triangulo
from backend.app.graphics.hittest import (
    TOLERANCIA_MINIMA,
    distancia_ate,
    distancia_ponto_segmento,
    encontrar,
    tolerancia,
)
from backend.app.graphics.point import Ponto2D

AZUL = Cor(0, 0, 255)


class TestDistanciaPontoSegmento:
    def test_ponto_sobre_o_segmento(self):
        a, b = Ponto2D(0, 0), Ponto2D(10, 0)
        assert distancia_ponto_segmento(5, 0, a, b) == pytest.approx(0.0)

    def test_distancia_perpendicular(self):
        a, b = Ponto2D(0, 0), Ponto2D(10, 0)
        assert distancia_ponto_segmento(5, 3, a, b) == pytest.approx(3.0)

    def test_limita_ao_segmento_e_nao_a_reta_infinita(self):
        """Alem do extremo, a distancia e ate o extremo, nao a projecao."""
        a, b = Ponto2D(0, 0), Ponto2D(10, 0)
        assert distancia_ponto_segmento(20, 0, a, b) == pytest.approx(10.0)

    def test_segmento_degenerado(self):
        a = Ponto2D(4, 4)
        assert distancia_ponto_segmento(4, 7, a, a) == pytest.approx(3.0)


class TestDistanciaPorTipo:
    def test_ponto(self):
        primitivo = Ponto(Ponto2D(10, 10), AZUL)
        assert distancia_ate(primitivo, 13, 14) == pytest.approx(5.0)

    def test_reta(self):
        primitivo = Reta(Ponto2D(0, 0), Ponto2D(10, 0), AZUL)
        assert distancia_ate(primitivo, 5, 4) == pytest.approx(4.0)

    def test_retangulo_por_dentro_mede_ate_a_aresta(self):
        """O retangulo e vazado: um clique no centro esta longe do contorno."""
        primitivo = Retangulo(Ponto2D(0, 0), Ponto2D(100, 100), AZUL)
        assert distancia_ate(primitivo, 50, 50) == pytest.approx(50.0)

    def test_retangulo_com_cantos_invertidos(self):
        invertido = Retangulo(Ponto2D(100, 100), Ponto2D(0, 0), AZUL)
        assert distancia_ate(invertido, 0, 50) == pytest.approx(0.0)

    def test_circulo_mede_ate_a_circunferencia(self):
        primitivo = Circulo(Ponto2D(50, 50), Ponto2D(70, 50), AZUL)
        assert distancia_ate(primitivo, 50, 50) == pytest.approx(20.0)
        assert distancia_ate(primitivo, 70, 50) == pytest.approx(0.0)
        assert distancia_ate(primitivo, 75, 50) == pytest.approx(5.0)

    def test_triangulo_mede_ate_a_aresta_mais_proxima(self):
        primitivo = Triangulo(Ponto2D(0, 0), Ponto2D(20, 0), Ponto2D(10, 20), AZUL)
        assert distancia_ate(primitivo, 10, 3) == pytest.approx(3.0)


class TestTolerancia:
    def test_traco_fino_usa_o_minimo(self):
        assert tolerancia(Reta(Ponto2D(0, 0), Ponto2D(1, 1), AZUL, esp=1)) == TOLERANCIA_MINIMA

    def test_traco_grosso_usa_metade_da_espessura(self):
        assert tolerancia(Reta(Ponto2D(0, 0), Ponto2D(1, 1), AZUL, esp=20)) == 10.0


class TestEncontrar:
    @pytest.fixture
    def figura(self):
        figura = Figura()
        figura.adicionar(Reta(Ponto2D(10, 10), Ponto2D(90, 10), AZUL))
        figura.adicionar(Circulo(Ponto2D(50, 50), Ponto2D(70, 50), AZUL))
        figura.adicionar(Retangulo(Ponto2D(10, 80), Ponto2D(60, 95), AZUL))
        figura.adicionar(Ponto(Ponto2D(95, 95), AZUL))
        figura.adicionar(Triangulo(Ponto2D(70, 70), Ponto2D(95, 70), Ponto2D(82, 88), AZUL))
        return figura

    @pytest.mark.parametrize(
        "px,py,esperado",
        [
            (50, 10, "reta_1"),
            (50, 30, "circulo_1"),
            (10, 88, "retangulo_1"),
            (95, 95, "ponto_1"),
            (82, 70, "triangulo_1"),
        ],
    )
    def test_acerta_cada_tipo(self, figura, px, py, esperado):
        assert encontrar(figura, px, py) == esperado

    def test_clique_no_vazio_nao_seleciona(self, figura):
        assert encontrar(figura, 5, 45) is None

    def test_clique_dentro_do_circulo_nao_seleciona(self, figura):
        """Nenhum primitivo e preenchido, entao o miolo nao e clicavel."""
        assert encontrar(figura, 50, 50) is None

    def test_erro_por_pouco_nao_seleciona(self):
        figura = Figura()
        figura.adicionar(Reta(Ponto2D(0, 50), Ponto2D(100, 50), AZUL, esp=1))
        assert encontrar(figura, 50, 53) == "reta_1"
        assert encontrar(figura, 50, 60) is None

    def test_espessura_maior_amplia_a_area_clicavel(self):
        figura = Figura()
        figura.adicionar(Reta(Ponto2D(0, 50), Ponto2D(100, 50), AZUL, esp=30))
        assert encontrar(figura, 50, 62) == "reta_1"

    def test_ultimo_desenhado_ganha_na_sobreposicao(self):
        """Duas figuras no mesmo lugar: vence a que foi desenhada por cima."""
        figura = Figura()
        figura.adicionar(Reta(Ponto2D(0, 50), Ponto2D(100, 50), AZUL))
        de_cima = figura.adicionar(Reta(Ponto2D(0, 50), Ponto2D(100, 50), AZUL))
        assert encontrar(figura, 50, 50) == de_cima.id

    def test_figura_vazia(self):
        assert encontrar(Figura(), 10, 10) is None

    def test_remover_o_de_cima_revela_o_de_baixo(self):
        figura = Figura()
        debaixo = figura.adicionar(Reta(Ponto2D(0, 50), Ponto2D(100, 50), AZUL))
        de_cima = figura.adicionar(Reta(Ponto2D(0, 50), Ponto2D(100, 50), AZUL))
        figura.remover(de_cima.id)
        assert encontrar(figura, 50, 50) == debaixo.id
