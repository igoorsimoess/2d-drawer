"""Conversao entre o espaco normalizado do arquivo JSON e o espaco de pixels.

O arquivo de persistencia guarda as coordenadas normalizadas no intervalo
[0, 1], o que torna a figura independente da resolucao da imagem. Aqui ficam
as duas conversoes e a convencao de arredondamento usada na exportacao.
"""

from __future__ import annotations

from ..point import Ponto2D

# Casas decimais gravadas no arquivo JSON, como no formato de referencia.
CASAS_DECIMAIS = 3


def normalizar(x_px: int, y_px: int, largura: int, altura: int) -> tuple[float, float]:
    """Converte pixels para o intervalo [0, 1].

    A convencao e x = x_px / (largura - 1), de modo que o primeiro pixel vira
    0.0 e o ultimo vira 1.0, sem estourar os limites do buffer na volta.
    """
    if largura <= 1 or altura <= 1:
        raise ValueError("largura e altura devem ser maiores que 1")
    return (x_px / (largura - 1), y_px / (altura - 1))


def desnormalizar(x: float, y: float, largura: int, altura: int) -> tuple[int, int]:
    """Converte coordenadas normalizadas para pixels.

    Valores fora de [0, 1] nao sao truncados: eles produzem coordenadas fora
    da imagem, que sao recortadas na hora da rasterizacao. Isso preserva a
    geometria original de figuras que extrapolam a area visivel.
    """
    if largura <= 1 or altura <= 1:
        raise ValueError("largura e altura devem ser maiores que 1")
    return (round(x * (largura - 1)), round(y * (altura - 1)))


def ponto_para_json(ponto: Ponto2D, largura: int, altura: int) -> dict:
    """Serializa um ponto em pixels como par normalizado e arredondado."""
    x, y = normalizar(ponto.x, ponto.y, largura, altura)
    return {"x": round(x, CASAS_DECIMAIS), "y": round(y, CASAS_DECIMAIS)}


def ponto_de_json(dados: object, largura: int, altura: int, campo: str = "ponto") -> Ponto2D:
    """Le um par normalizado do JSON e devolve o ponto em pixels."""
    if not isinstance(dados, dict):
        raise ValueError(f'"{campo}" deve ser um objeto com x e y')
    try:
        x = float(dados["x"])
        y = float(dados["y"])
    except KeyError as erro:
        raise ValueError(f'"{campo}" sem a coordenada {erro}') from erro
    except (TypeError, ValueError) as erro:
        raise ValueError(f'"{campo}" invalido: {erro}') from erro
    return Ponto2D(*desnormalizar(x, y, largura, altura))
