"""Ponto bidimensional em coordenadas de pixel."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Ponto2D:
    """Par (x, y) inteiro, ja no espaco de pixels da imagem."""

    x: int
    y: int

    def __post_init__(self) -> None:
        """Garante que as coordenadas sejam inteiras."""
        for nome in ("x", "y"):
            valor = getattr(self, nome)
            if not isinstance(valor, int) or isinstance(valor, bool):
                raise ValueError(f'coordenada "{nome}" deve ser inteira')

    def distancia(self, outro: "Ponto2D") -> float:
        """Distancia euclidiana ate outro ponto."""
        return math.hypot(self.x - outro.x, self.y - outro.y)

    def para_dict(self) -> dict:
        """Serializa o ponto em coordenadas de pixel."""
        return {"x": self.x, "y": self.y}

    @classmethod
    def de_dict(cls, dados: object, campo: str = "ponto") -> "Ponto2D":
        """Constroi um Ponto2D a partir de um dicionario {"x":..,"y":..}."""
        if not isinstance(dados, dict):
            raise ValueError(f'"{campo}" deve ser um objeto com x e y')
        try:
            return cls(int(round(float(dados["x"]))), int(round(float(dados["y"]))))
        except KeyError as erro:
            raise ValueError(f'"{campo}" sem a coordenada {erro}') from erro
        except (TypeError, ValueError) as erro:
            raise ValueError(f'"{campo}" invalido: {erro}') from erro
