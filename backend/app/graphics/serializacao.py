"""Conversao entre a Figura em memoria e o arquivo JSON de persistencia.

O formato e fixo, definido pelo enunciado: um objeto raiz "figura" com uma
lista por tipo de primitivo, coordenadas normalizadas em [0, 1], cor RGB,
espessura em pixels e um id sequencial por tipo.

    {"figura": {
        "ponto":     [{"x":..,"y":..,"cor":{..},"esp":..,"id":"ponto_1"}],
        "reta":      [{"p1":{..},"p2":{..},"cor":{..},"esp":..,"id":"reta_1"}],
        "triangulo": [{"p1":{..},"p2":{..},"p3":{..},...}],
        "retangulo": [{"p1":{..},"p2":{..},...}],
        "circulo":   [{"centro":{..},"raio":{..},...}]
    }}

Observacoes sobre o formato:

- "raio" do circulo e um ponto sobre a circunferencia, e nao um escalar: o
  raio efetivo e a distancia entre "centro" e "raio".
- No "ponto", x e y ficam no proprio item, sem objeto aninhado.
- Como os primitivos sao agrupados por tipo, a ordem de insercao entre tipos
  diferentes nao sobrevive ao arquivo. Na importacao a figura e remontada na
  ordem dos tipos.
"""

from __future__ import annotations

from .color import Cor
from .figura import (
    TIPOS,
    Circulo,
    Figura,
    Ponto,
    Primitivo,
    Reta,
    Retangulo,
    Triangulo,
    sanitizar_espessura,
)
from .transforms.viewport import ponto_de_json, ponto_para_json


def figura_para_json(figura: Figura, largura: int, altura: int) -> dict:
    """Serializa a figura no formato do arquivo, com coordenadas normalizadas."""
    grupos: dict[str, list[dict]] = {tipo: [] for tipo in TIPOS}
    for primitivo in figura:
        grupos[primitivo.tipo].append(_item_para_json(primitivo, largura, altura))
    return {"figura": grupos}


def _item_para_json(primitivo: Primitivo, largura: int, altura: int) -> dict:
    """Serializa um primitivo isolado, conforme as chaves do seu tipo."""
    comuns = {"cor": primitivo.cor.para_dict(), "esp": primitivo.esp, "id": primitivo.id}

    if isinstance(primitivo, Ponto):
        # No formato de referencia o ponto carrega x e y direto no item.
        return {**ponto_para_json(primitivo.p, largura, altura), **comuns}
    if isinstance(primitivo, Reta):
        return {
            "p1": ponto_para_json(primitivo.p1, largura, altura),
            "p2": ponto_para_json(primitivo.p2, largura, altura),
            **comuns,
        }
    if isinstance(primitivo, Triangulo):
        return {
            "p1": ponto_para_json(primitivo.p1, largura, altura),
            "p2": ponto_para_json(primitivo.p2, largura, altura),
            "p3": ponto_para_json(primitivo.p3, largura, altura),
            **comuns,
        }
    if isinstance(primitivo, Retangulo):
        return {
            "p1": ponto_para_json(primitivo.p1, largura, altura),
            "p2": ponto_para_json(primitivo.p2, largura, altura),
            **comuns,
        }
    if isinstance(primitivo, Circulo):
        return {
            "centro": ponto_para_json(primitivo.centro, largura, altura),
            "raio": ponto_para_json(primitivo.borda, largura, altura),
            **comuns,
        }
    raise ValueError(f'primitivo nao serializavel: "{primitivo.tipo}"')


def json_para_figura(dados: object, largura: int, altura: int) -> Figura:
    """Reconstroi a Figura a partir do conteudo do arquivo JSON.

    Levanta ValueError com uma mensagem que identifica o tipo e o indice do
    item problematico, para que a interface possa mostrar o motivo exato.
    """
    if not isinstance(dados, dict):
        raise ValueError("o arquivo deve conter um objeto JSON")
    if "figura" not in dados:
        raise ValueError('o arquivo deve ter a chave raiz "figura"')

    corpo = dados["figura"]
    if not isinstance(corpo, dict):
        raise ValueError('"figura" deve ser um objeto com uma lista por tipo')

    desconhecidos = sorted(set(corpo) - set(TIPOS))
    if desconhecidos:
        raise ValueError(f"tipo(s) desconhecido(s): {', '.join(desconhecidos)}")

    figura = Figura()
    for tipo in TIPOS:
        itens = corpo.get(tipo, [])
        if not isinstance(itens, list):
            raise ValueError(f'"{tipo}" deve ser uma lista')
        for indice, item in enumerate(itens):
            try:
                figura.adicionar(_item_de_json(tipo, item, largura, altura))
            except ValueError as erro:
                raise ValueError(f"{tipo}[{indice}]: {erro}") from erro
    return figura


def _item_de_json(tipo: str, item: object, largura: int, altura: int) -> Primitivo:
    """Constroi um primitivo a partir de um item do arquivo."""
    if not isinstance(item, dict):
        raise ValueError("cada item deve ser um objeto")

    cor, esp, id = _ler_comuns(item)
    ler = lambda campo: ponto_de_json(_exigir(item, campo), largura, altura, campo)

    if tipo == "ponto":
        p = ponto_de_json(item, largura, altura, "ponto")
        return Ponto(p, cor, esp, id)
    if tipo == "reta":
        return Reta(ler("p1"), ler("p2"), cor, esp, id)
    if tipo == "triangulo":
        return Triangulo(ler("p1"), ler("p2"), ler("p3"), cor, esp, id)
    if tipo == "retangulo":
        return Retangulo(ler("p1"), ler("p2"), cor, esp, id)
    if tipo == "circulo":
        # "raio" e um ponto sobre a circunferencia, nao um escalar.
        return Circulo(ler("centro"), ler("raio"), cor, esp, id)
    raise ValueError(f'tipo desconhecido "{tipo}"')


def _exigir(item: dict, campo: str) -> object:
    """Le um campo obrigatorio do item, com mensagem clara quando falta."""
    if campo not in item:
        raise ValueError(f'campo obrigatorio "{campo}" ausente')
    return item[campo]


def _ler_comuns(item: dict) -> tuple[Cor, int, str | None]:
    """Le cor, espessura e id, comuns a todos os tipos."""
    cor = Cor.de_dict(_exigir(item, "cor"))
    esp = sanitizar_espessura(_exigir(item, "esp"))
    id = item.get("id")
    if id is not None and not isinstance(id, str):
        raise ValueError('"id" deve ser texto')
    return cor, esp, id
