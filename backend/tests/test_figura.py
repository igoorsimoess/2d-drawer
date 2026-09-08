"""Testes da estrutura de dados Figura e dos primitivos."""

import pytest

from backend.app.graphics.color import Cor
from backend.app.graphics.figura import (
    Circulo,
    Figura,
    Ponto,
    Reta,
    Retangulo,
    Triangulo,
    sanitizar_espessura,
)
from backend.app.graphics.image import Imagem
from backend.app.graphics.point import Ponto2D

from .conftest import pixels_pintados

AZUL = Cor(0, 0, 255)
VERMELHO = Cor(255, 0, 0)


def nova_reta(**kwargs):
    return Reta(Ponto2D(1, 1), Ponto2D(9, 9), AZUL, **kwargs)


class TestEspessura:
    @pytest.mark.parametrize("entrada,esperado", [(5, 5), (1, 1), (0, 1), (-4, 1), ("7", 7)])
    def test_sanitiza(self, entrada, esperado):
        assert sanitizar_espessura(entrada) == esperado

    def test_rejeita_valor_sem_conversao(self):
        with pytest.raises(ValueError):
            sanitizar_espessura("grosso")

    def test_primitivo_guarda_espessura_sanitizada(self):
        assert nova_reta(esp=0).esp == 1


class TestIdsSequenciais:
    def test_numera_por_tipo(self):
        figura = Figura()
        assert figura.adicionar(nova_reta()).id == "reta_1"
        assert figura.adicionar(nova_reta()).id == "reta_2"
        assert figura.adicionar(Ponto(Ponto2D(0, 0), AZUL)).id == "ponto_1"
        assert figura.adicionar(nova_reta()).id == "reta_3"

    def test_id_explicito_e_preservado(self):
        figura = Figura()
        assert figura.adicionar(nova_reta(id="reta_7")).id == "reta_7"

    def test_contador_avanca_apos_id_importado(self):
        """Ids vindos de um arquivo nao podem colidir com os proximos gerados."""
        figura = Figura()
        figura.adicionar(nova_reta(id="reta_9"))
        assert figura.adicionar(nova_reta()).id == "reta_10"

    def test_id_nao_numerado_nao_afeta_o_contador(self):
        figura = Figura()
        figura.adicionar(nova_reta(id="reta_personalizada"))
        assert figura.adicionar(nova_reta()).id == "reta_1"

    def test_limpar_reinicia_a_numeracao(self):
        figura = Figura()
        figura.adicionar(nova_reta())
        figura.limpar()
        assert len(figura) == 0
        assert figura.adicionar(nova_reta()).id == "reta_1"

    def test_tipo_desconhecido_no_proximo_id(self):
        with pytest.raises(ValueError):
            Figura().proximo_id("hexagono")


class TestBuscaERemocao:
    def test_obter_e_remover(self):
        figura = Figura()
        reta = figura.adicionar(nova_reta())
        assert figura.obter(reta.id) is reta
        assert figura.remover(reta.id) is True
        assert len(figura) == 0
        assert figura.obter(reta.id) is None

    def test_remover_id_inexistente_retorna_falso(self):
        assert Figura().remover("reta_99") is False

    def test_remocao_preserva_a_ordem_dos_demais(self):
        figura = Figura()
        a, b, c = (figura.adicionar(nova_reta()) for _ in range(3))
        figura.remover(b.id)
        assert [p.id for p in figura] == [a.id, c.id]


class TestDesenho:
    def test_desenha_todos_os_tipos(self):
        figura = Figura()
        figura.adicionar(Ponto(Ponto2D(2, 2), AZUL))
        figura.adicionar(Reta(Ponto2D(5, 5), Ponto2D(15, 5), AZUL))
        figura.adicionar(Circulo(Ponto2D(30, 30), Ponto2D(38, 30), AZUL))
        figura.adicionar(Retangulo(Ponto2D(40, 5), Ponto2D(50, 15), AZUL))
        figura.adicionar(Triangulo(Ponto2D(20, 20), Ponto2D(28, 20), Ponto2D(24, 28), AZUL))
        imagem = Imagem(60, 60)
        assert figura.desenhar(imagem) == 5
        assert len(pixels_pintados(imagem)) > 0

    def test_filtro_por_tipo(self):
        figura = Figura()
        figura.adicionar(nova_reta())
        figura.adicionar(nova_reta())
        figura.adicionar(Ponto(Ponto2D(2, 2), AZUL))
        imagem = Imagem(20, 20)
        assert figura.desenhar(imagem, "reta") == 2
        assert figura.desenhar(imagem, "ponto") == 1
        assert figura.desenhar(imagem, "circulo") == 0

    def test_filtro_com_tipo_invalido(self):
        with pytest.raises(ValueError):
            Figura().desenhar(Imagem(10, 10), "hexagono")

    def test_desenhar_nao_limpa_a_imagem(self):
        """Quem chama decide quando limpar; desenhar apenas sobrepoe."""
        imagem = Imagem(20, 20)
        imagem.set_pixel(19, 19, VERMELHO)
        Figura().desenhar(imagem)
        assert imagem.get_pixel(19, 19) == VERMELHO


class TestCirculo:
    def test_raio_vem_da_distancia_ate_a_borda(self):
        circulo = Circulo(Ponto2D(10, 10), Ponto2D(13, 14), AZUL)
        assert circulo.raio == 5

    def test_borda_e_preservada_para_a_exportacao(self):
        circulo = Circulo(Ponto2D(10, 10), Ponto2D(13, 14), AZUL)
        assert circulo.borda == Ponto2D(13, 14)

    def test_caixa_cobre_a_circunferencia_inteira(self):
        """A caixa envolvente usa os extremos do circulo, nao o ponto da borda."""
        circulo = Circulo(Ponto2D(20, 20), Ponto2D(30, 20), AZUL)
        assert circulo.caixa() == (10, 10, 30, 30)


class TestResumo:
    def test_caixa_da_reta(self):
        assert Reta(Ponto2D(9, 1), Ponto2D(1, 9), AZUL).caixa() == (1, 1, 9, 9)

    def test_para_dict_traz_id_tipo_cor_e_esp(self):
        figura = Figura()
        reta = figura.adicionar(nova_reta(esp=4))
        dados = reta.para_dict()
        assert dados["id"] == "reta_1"
        assert dados["tipo"] == "reta"
        assert dados["esp"] == 4
        assert dados["cor"] == {"r": 0, "g": 0, "b": 255}
        assert dados["p1"] == {"x": 1, "y": 1}

    def test_contagem_por_tipo(self):
        figura = Figura()
        figura.adicionar(nova_reta())
        figura.adicionar(nova_reta())
        figura.adicionar(Ponto(Ponto2D(0, 0), AZUL))
        assert figura.contagem_por_tipo() == {"reta": 2, "ponto": 1}

    def test_listar_devolve_um_resumo_por_primitivo(self):
        figura = Figura()
        figura.adicionar(nova_reta())
        figura.adicionar(Ponto(Ponto2D(0, 0), AZUL))
        assert [d["tipo"] for d in figura.listar()] == ["reta", "ponto"]
