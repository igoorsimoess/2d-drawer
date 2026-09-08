"""Testes da conversao entre a Figura e o arquivo JSON de persistencia."""

import copy
import json
import pathlib

import pytest

from backend.app.graphics.color import Cor
from backend.app.graphics.figura import (
    TIPOS,
    Circulo,
    Figura,
    Ponto,
    Reta,
    Retangulo,
    Triangulo,
)
from backend.app.graphics.point import Ponto2D
from backend.app.graphics.serializacao import figura_para_json, json_para_figura

LARGURA, ALTURA = 800, 600
EXEMPLO = pathlib.Path(__file__).parent / "dados" / "figura_exemplo.json"
VERDE = Cor(0, 102, 102)


@pytest.fixture
def exemplo() -> dict:
    """JSON de referencia do enunciado."""
    return json.loads(EXEMPLO.read_text())


@pytest.fixture
def figura_completa() -> Figura:
    """Figura com um primitivo de cada tipo."""
    figura = Figura()
    figura.adicionar(Ponto(Ponto2D(130, 416), VERDE, 50))
    figura.adicionar(Reta(Ponto2D(535, 260), Ponto2D(535, 290), Cor(79, 56, 7), 12))
    figura.adicionar(Triangulo(Ponto2D(406, 293), Ponto2D(667, 296), Ponto2D(536, 427), Cor(255, 153, 153), 6))
    figura.adicionar(Retangulo(Ponto2D(91, 379), Ponto2D(300, 446), VERDE, 18))
    figura.adicionar(Circulo(Ponto2D(197, 192), Ponto2D(514, 300), Cor(102, 0, 255), 10))
    return figura


class TestExportacao:
    def test_estrutura_tem_a_raiz_figura_e_todos_os_tipos(self, figura_completa):
        dados = figura_para_json(figura_completa, LARGURA, ALTURA)
        assert set(dados) == {"figura"}
        assert set(dados["figura"]) == set(TIPOS)

    def test_figura_vazia_gera_listas_vazias(self):
        dados = figura_para_json(Figura(), LARGURA, ALTURA)
        assert all(dados["figura"][tipo] == [] for tipo in TIPOS)

    def test_ponto_carrega_x_e_y_no_proprio_item(self, figura_completa):
        item = figura_para_json(figura_completa, LARGURA, ALTURA)["figura"]["ponto"][0]
        assert set(item) == {"x", "y", "cor", "esp", "id"}
        assert item["id"] == "ponto_1"

    def test_circulo_exporta_raio_como_ponto(self, figura_completa):
        """No formato, "raio" e um ponto sobre a circunferencia."""
        item = figura_para_json(figura_completa, LARGURA, ALTURA)["figura"]["circulo"][0]
        assert set(item["raio"]) == {"x", "y"}
        assert set(item["centro"]) == {"x", "y"}

    def test_coordenadas_normalizadas_entre_zero_e_um(self, figura_completa):
        item = figura_para_json(figura_completa, LARGURA, ALTURA)["figura"]["reta"][0]
        for chave in ("p1", "p2"):
            assert 0.0 <= item[chave]["x"] <= 1.0
            assert 0.0 <= item[chave]["y"] <= 1.0

    def test_arredonda_em_tres_casas(self, figura_completa):
        dados = figura_para_json(figura_completa, LARGURA, ALTURA)
        for item in dados["figura"]["triangulo"]:
            for chave in ("p1", "p2", "p3"):
                for eixo in ("x", "y"):
                    valor = item[chave][eixo]
                    assert round(valor, 3) == valor

    def test_serializavel_por_json(self, figura_completa):
        json.dumps(figura_para_json(figura_completa, LARGURA, ALTURA))


class TestIdaEVolta:
    def test_figura_para_json_e_de_volta_preserva_os_pixels(self, figura_completa):
        """Este e o sentido exato: pixel -> arquivo -> pixel nao perde nada."""
        dados = figura_para_json(figura_completa, LARGURA, ALTURA)
        recuperada = json_para_figura(dados, LARGURA, ALTURA)
        assert len(recuperada) == len(figura_completa)
        for original, volta in zip(figura_completa, recuperada):
            assert volta.tipo == original.tipo
            assert volta.id == original.id
            assert volta.cor == original.cor
            assert volta.esp == original.esp
            assert volta.pontos() == original.pontos()

    def test_json_para_figura_e_de_volta_fica_dentro_de_um_pixel(self, exemplo):
        """No sentido inverso ha quantizacao: valores arbitrarios encaixam na grade.

        Um valor normalizado qualquer nao cai exatamente sobre um pixel, entao
        a volta pode diferir por ate meio pixel, ou seja 1/(largura-1).
        """
        figura = json_para_figura(exemplo, LARGURA, ALTURA)
        volta = figura_para_json(figura, LARGURA, ALTURA)
        tolerancia = 1.0 / (LARGURA - 1)
        for tipo in TIPOS:
            for antes, depois in zip(exemplo["figura"][tipo], volta["figura"][tipo]):
                assert antes["id"] == depois["id"]
                assert antes["esp"] == depois["esp"]
                assert antes["cor"] == depois["cor"]
                for chave, valor in antes.items():
                    if isinstance(valor, dict) and "x" in valor:
                        assert abs(valor["x"] - depois[chave]["x"]) <= tolerancia
                        assert abs(valor["y"] - depois[chave]["y"]) <= tolerancia


class TestImportacaoDoExemplo:
    def test_importa_o_exemplo_do_enunciado(self, exemplo):
        figura = json_para_figura(exemplo, LARGURA, ALTURA)
        assert figura.contagem_por_tipo() == {
            "ponto": 3, "reta": 1, "triangulo": 3, "retangulo": 1, "circulo": 3,
        }

    def test_preserva_os_ids_do_arquivo(self, exemplo):
        figura = json_para_figura(exemplo, LARGURA, ALTURA)
        assert [p.id for p in figura] == [
            "ponto_1", "ponto_2", "ponto_3", "reta_1",
            "triangulo_1", "triangulo_2", "triangulo_3",
            "retangulo_1", "circulo_1", "circulo_2", "circulo_3",
        ]

    def test_novo_primitivo_nao_colide_com_os_ids_importados(self, exemplo):
        figura = json_para_figura(exemplo, LARGURA, ALTURA)
        novo = figura.adicionar(Reta(Ponto2D(0, 0), Ponto2D(1, 1), VERDE))
        assert novo.id == "reta_2"

    def test_raio_do_circulo_vem_da_distancia_ate_o_ponto(self, exemplo):
        figura = json_para_figura(exemplo, LARGURA, ALTURA)
        circulo = figura.obter("circulo_3")
        assert circulo.raio == round(circulo.centro.distancia(circulo.borda))
        assert circulo.raio > 0

    def test_chaves_de_tipo_ausentes_viram_listas_vazias(self):
        figura = json_para_figura({"figura": {"ponto": []}}, LARGURA, ALTURA)
        assert len(figura) == 0


class TestValidacao:
    @pytest.mark.parametrize(
        "entrada,trecho",
        [
            ([], "objeto JSON"),
            ({}, '"figura"'),
            ({"figura": []}, '"figura"'),
            ({"figura": {"hexagono": []}}, "desconhecido"),
            ({"figura": {"reta": {}}}, "deve ser uma lista"),
        ],
    )
    def test_estrutura_invalida(self, entrada, trecho):
        with pytest.raises(ValueError, match=trecho):
            json_para_figura(entrada, LARGURA, ALTURA)

    def test_erro_identifica_tipo_e_indice(self, exemplo):
        """A mensagem precisa dizer qual item do arquivo esta errado."""
        quebrado = copy.deepcopy(exemplo)
        del quebrado["figura"]["triangulo"][1]["p2"]
        with pytest.raises(ValueError, match=r"triangulo\[1\].*p2"):
            json_para_figura(quebrado, LARGURA, ALTURA)

    def test_cor_ausente(self, exemplo):
        quebrado = copy.deepcopy(exemplo)
        del quebrado["figura"]["reta"][0]["cor"]
        with pytest.raises(ValueError, match=r'reta\[0\].*"cor"'):
            json_para_figura(quebrado, LARGURA, ALTURA)

    def test_espessura_ausente(self, exemplo):
        quebrado = copy.deepcopy(exemplo)
        del quebrado["figura"]["circulo"][0]["esp"]
        with pytest.raises(ValueError, match=r'circulo\[0\].*"esp"'):
            json_para_figura(quebrado, LARGURA, ALTURA)

    def test_item_que_nao_e_objeto(self):
        with pytest.raises(ValueError, match=r"ponto\[0\]"):
            json_para_figura({"figura": {"ponto": ["x"]}}, LARGURA, ALTURA)

    def test_canal_de_cor_invalido(self, exemplo):
        quebrado = copy.deepcopy(exemplo)
        quebrado["figura"]["reta"][0]["cor"]["r"] = 999
        with pytest.raises(ValueError, match=r"reta\[0\]"):
            json_para_figura(quebrado, LARGURA, ALTURA)

    def test_espessura_zero_degenera_para_um(self, exemplo):
        ajustado = copy.deepcopy(exemplo)
        ajustado["figura"]["reta"][0]["esp"] = 0
        figura = json_para_figura(ajustado, LARGURA, ALTURA)
        assert figura.obter("reta_1").esp == 1

    def test_id_precisa_ser_texto(self, exemplo):
        quebrado = copy.deepcopy(exemplo)
        quebrado["figura"]["reta"][0]["id"] = 7
        with pytest.raises(ValueError, match=r"reta\[0\].*id"):
            json_para_figura(quebrado, LARGURA, ALTURA)
