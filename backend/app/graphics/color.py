"""Representacao de cor RGB usada pelos primitivos."""

from __future__ import annotations

from dataclasses import dataclass

CANAL_MINIMO = 0
CANAL_MAXIMO = 255


@dataclass(frozen=True)
class Cor:
    """Cor RGB opaca, com cada canal no intervalo [0, 255]."""

    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        """Valida os tres canais na construcao."""
        for nome in ("r", "g", "b"):
            valor = getattr(self, nome)
            if not isinstance(valor, int) or isinstance(valor, bool):
                raise ValueError(f'canal "{nome}" deve ser inteiro')
            if not CANAL_MINIMO <= valor <= CANAL_MAXIMO:
                raise ValueError(
                    f'canal "{nome}" deve estar entre {CANAL_MINIMO} e {CANAL_MAXIMO}'
                )

    def para_rgba(self) -> tuple[int, int, int, int]:
        """Retorna a cor como tupla RGBA, sempre totalmente opaca."""
        return (self.r, self.g, self.b, CANAL_MAXIMO)

    def para_dict(self) -> dict:
        """Serializa a cor no formato usado pelo arquivo JSON da figura."""
        return {"r": self.r, "g": self.g, "b": self.b}

    @classmethod
    def de_dict(cls, dados: object) -> "Cor":
        """Constroi uma Cor a partir de um dicionario {"r":..,"g":..,"b":..}.

        Levanta ValueError com mensagem descritiva quando o dicionario e
        invalido, para que a API possa devolver o motivo ao cliente.
        """
        if not isinstance(dados, dict):
            raise ValueError('"cor" deve ser um objeto com r, g e b')
        try:
            return cls(int(dados["r"]), int(dados["g"]), int(dados["b"]))
        except KeyError as erro:
            raise ValueError(f'"cor" sem o canal {erro}') from erro
        except (TypeError, ValueError) as erro:
            raise ValueError(f'"cor" invalida: {erro}') from erro


PRETO = Cor(0, 0, 0)
BRANCO = Cor(255, 255, 255)
