"""Testes da conversao entre coordenadas normalizadas e pixels."""

import pytest

from backend.app.graphics.point import Ponto2D
from backend.app.graphics.transforms.viewport import (
    CASAS_DECIMAIS,
    desnormalizar,
    normalizar,
    ponto_de_json,
    ponto_para_json,
)

LARGURA, ALTURA = 800, 600


def test_extremos_mapeiam_para_os_cantos():
    assert normalizar(0, 0, LARGURA, ALTURA) == (0.0, 0.0)
    assert normalizar(LARGURA - 1, ALTURA - 1, LARGURA, ALTURA) == (1.0, 1.0)
    assert desnormalizar(0.0, 0.0, LARGURA, ALTURA) == (0, 0)
    assert desnormalizar(1.0, 1.0, LARGURA, ALTURA) == (LARGURA - 1, ALTURA - 1)


def test_ida_e_volta_exata_em_toda_a_imagem():
    """Com 3 casas decimais, a volta deve reproduzir o pixel original.

    O erro maximo de arredondamento e 0.0005 * 799 = 0.4 pixel, menor que
    meio pixel, entao a reconversao cai sempre no mesmo pixel.
    """
    for x_px in range(0, LARGURA, 7):
        for y_px in range(0, ALTURA, 11):
            x, y = normalizar(x_px, y_px, LARGURA, ALTURA)
            arredondado = (round(x, CASAS_DECIMAIS), round(y, CASAS_DECIMAIS))
            assert desnormalizar(*arredondado, LARGURA, ALTURA) == (x_px, y_px)


def test_ponto_para_json_arredonda_em_tres_casas():
    dados = ponto_para_json(Ponto2D(123, 456), LARGURA, ALTURA)
    assert dados == {"x": 0.154, "y": 0.761}


def test_ponto_de_json_ida_e_volta():
    original = Ponto2D(500, 300)
    dados = ponto_para_json(original, LARGURA, ALTURA)
    assert ponto_de_json(dados, LARGURA, ALTURA) == original


def test_valores_fora_do_intervalo_nao_sao_truncados():
    """Figuras que extrapolam a area visivel preservam sua geometria."""
    assert desnormalizar(1.25, -0.25, LARGURA, ALTURA) == (999, -150)


def test_dimensoes_degeneradas_sao_rejeitadas():
    for largura, altura in [(1, 600), (800, 1), (0, 0)]:
        with pytest.raises(ValueError):
            normalizar(0, 0, largura, altura)
        with pytest.raises(ValueError):
            desnormalizar(0.0, 0.0, largura, altura)


def test_ponto_de_json_reporta_campo_ausente():
    with pytest.raises(ValueError, match="p1"):
        ponto_de_json({"x": 0.5}, LARGURA, ALTURA, campo="p1")


def test_ponto_de_json_rejeita_nao_objeto():
    with pytest.raises(ValueError, match="p2"):
        ponto_de_json("0.5,0.5", LARGURA, ALTURA, campo="p2")
