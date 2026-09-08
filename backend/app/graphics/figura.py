"""Modelo de dominio: a Figura e os primitivos que a compoem.

A Figura e a estrutura de dados (ED) da aplicacao. Ela guarda os primitivos em
coordenadas de pixel e sabe se redesenhar sobre uma Imagem. A conversao para o
formato normalizado do arquivo JSON fica em `serializacao.py`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Iterator

from .algorithms.circle import desenhar_circulo
from .algorithms.line import desenhar_reta
from .algorithms.rectangle import desenhar_retangulo
from .algorithms.triangle import desenhar_triangulo
from .color import Cor
from .image import Imagem
from .point import Ponto2D

TIPOS = ("ponto", "reta", "triangulo", "retangulo", "circulo")


def sanitizar_espessura(esp: object) -> int:
    """Converte a espessura para inteiro maior ou igual a 1.

    Espessura zero ou negativa nao tem representacao visual, entao degenera
    para o traco de 1 pixel em vez de rejeitar a figura inteira.
    """
    try:
        return max(1, int(esp))
    except (TypeError, ValueError) as erro:
        raise ValueError(f'"esp" invalida: {esp!r}') from erro


class Primitivo(ABC):
    """Base dos primitivos desenhaveis, com cor, espessura e identificador."""

    tipo: ClassVar[str]

    def __init__(self, cor: Cor, esp: int = 1, id: str | None = None) -> None:
        self.cor = cor
        self.esp = sanitizar_espessura(esp)
        self.id = id

    @abstractmethod
    def desenhar(self, imagem: Imagem) -> None:
        """Rasteriza o primitivo sobre a imagem."""

    @abstractmethod
    def pontos(self) -> list[Ponto2D]:
        """Pontos de controle, usados para calcular a caixa envolvente."""

    @abstractmethod
    def _params(self) -> dict:
        """Parametros especificos do tipo, em coordenadas de pixel."""

    def caixa(self) -> tuple[int, int, int, int]:
        """Caixa envolvente (x_min, y_min, x_max, y_max) em pixels."""
        xs = [p.x for p in self.pontos()]
        ys = [p.y for p in self.pontos()]
        return (min(xs), min(ys), max(xs), max(ys))

    def para_dict(self) -> dict:
        """Resumo em coordenadas de pixel, usado pela interface.

        Inclui a caixa envolvente para que o destaque de selecao no cliente
        nao precise reimplementar a geometria de cada tipo.
        """
        return {
            "id": self.id,
            "tipo": self.tipo,
            "cor": self.cor.para_dict(),
            "esp": self.esp,
            "caixa": list(self.caixa()),
            **self._params(),
        }


class Ponto(Primitivo):
    """Um unico ponto carimbado com a espessura informada."""

    tipo = "ponto"

    def __init__(self, p: Ponto2D, cor: Cor, esp: int = 1, id: str | None = None) -> None:
        super().__init__(cor, esp, id)
        self.p = p

    def desenhar(self, imagem: Imagem) -> None:
        imagem.carimbar(self.p.x, self.p.y, self.cor, self.esp)

    def pontos(self) -> list[Ponto2D]:
        return [self.p]

    def _params(self) -> dict:
        return {"p": self.p.para_dict()}


class Reta(Primitivo):
    """Segmento de reta entre dois pontos."""

    tipo = "reta"

    def __init__(
        self, p1: Ponto2D, p2: Ponto2D, cor: Cor, esp: int = 1, id: str | None = None
    ) -> None:
        super().__init__(cor, esp, id)
        self.p1 = p1
        self.p2 = p2

    def desenhar(self, imagem: Imagem) -> None:
        desenhar_reta(imagem, self.p1, self.p2, self.cor, self.esp)

    def pontos(self) -> list[Ponto2D]:
        return [self.p1, self.p2]

    def _params(self) -> dict:
        return {"p1": self.p1.para_dict(), "p2": self.p2.para_dict()}


class Triangulo(Primitivo):
    """Contorno de triangulo definido por tres vertices."""

    tipo = "triangulo"

    def __init__(
        self, p1: Ponto2D, p2: Ponto2D, p3: Ponto2D, cor: Cor,
        esp: int = 1, id: str | None = None,
    ) -> None:
        super().__init__(cor, esp, id)
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3

    def desenhar(self, imagem: Imagem) -> None:
        desenhar_triangulo(imagem, self.p1, self.p2, self.p3, self.cor, self.esp)

    def pontos(self) -> list[Ponto2D]:
        return [self.p1, self.p2, self.p3]

    def _params(self) -> dict:
        return {
            "p1": self.p1.para_dict(),
            "p2": self.p2.para_dict(),
            "p3": self.p3.para_dict(),
        }


class Retangulo(Primitivo):
    """Retangulo alinhado aos eixos, definido por dois cantos opostos."""

    tipo = "retangulo"

    def __init__(
        self, p1: Ponto2D, p2: Ponto2D, cor: Cor, esp: int = 1, id: str | None = None
    ) -> None:
        super().__init__(cor, esp, id)
        self.p1 = p1
        self.p2 = p2

    def desenhar(self, imagem: Imagem) -> None:
        desenhar_retangulo(imagem, self.p1, self.p2, self.cor, self.esp)

    def pontos(self) -> list[Ponto2D]:
        return [self.p1, self.p2]

    def _params(self) -> dict:
        return {"p1": self.p1.para_dict(), "p2": self.p2.para_dict()}


class Circulo(Primitivo):
    """Circunferencia definida pelo centro e por um ponto sobre a borda.

    O ponto da borda e guardado tal como foi clicado, e nao apenas o raio
    resultante, porque o formato do arquivo JSON persiste esse ponto. Assim a
    exportacao seguida de importacao reproduz exatamente a mesma figura.
    """

    tipo = "circulo"

    def __init__(
        self, centro: Ponto2D, borda: Ponto2D, cor: Cor,
        esp: int = 1, id: str | None = None,
    ) -> None:
        super().__init__(cor, esp, id)
        self.centro = centro
        self.borda = borda

    @property
    def raio(self) -> int:
        """Raio em pixels, dado pela distancia entre o centro e a borda."""
        return round(self.centro.distancia(self.borda))

    def desenhar(self, imagem: Imagem) -> None:
        desenhar_circulo(imagem, self.centro, self.raio, self.cor, self.esp)

    def pontos(self) -> list[Ponto2D]:
        """Extremos da circunferencia, e nao os pontos de controle.

        A caixa envolvente precisa cobrir o circulo desenhado; o ponto da
        borda sozinho nao descreve essa area.
        """
        raio = self.raio
        return [
            Ponto2D(self.centro.x - raio, self.centro.y - raio),
            Ponto2D(self.centro.x + raio, self.centro.y + raio),
        ]

    def _params(self) -> dict:
        return {
            "centro": self.centro.para_dict(),
            "borda": self.borda.para_dict(),
            "raio": self.raio,
        }


class Figura:
    """Colecao ordenada de primitivos - a estrutura de dados da aplicacao."""

    def __init__(self) -> None:
        self.primitivos: list[Primitivo] = []
        self._contadores: dict[str, int] = {tipo: 0 for tipo in TIPOS}

    def __len__(self) -> int:
        return len(self.primitivos)

    def __iter__(self) -> Iterator[Primitivo]:
        return iter(self.primitivos)

    def proximo_id(self, tipo: str) -> str:
        """Gera o proximo identificador sequencial do tipo (ex.: reta_3)."""
        if tipo not in self._contadores:
            raise ValueError(f'tipo desconhecido "{tipo}"')
        self._contadores[tipo] += 1
        return f"{tipo}_{self._contadores[tipo]}"

    def adicionar(self, primitivo: Primitivo) -> Primitivo:
        """Insere o primitivo, atribuindo um id sequencial se ainda nao tiver."""
        if primitivo.id is None:
            primitivo.id = self.proximo_id(primitivo.tipo)
        else:
            self._registrar_id(primitivo.tipo, primitivo.id)
        self.primitivos.append(primitivo)
        return primitivo

    def _registrar_id(self, tipo: str, id: str) -> None:
        """Avanca o contador para que ids importados nao colidam com os novos."""
        prefixo = f"{tipo}_"
        if id.startswith(prefixo):
            sufixo = id[len(prefixo):]
            if sufixo.isdigit():
                self._contadores[tipo] = max(self._contadores[tipo], int(sufixo))

    def obter(self, id: str) -> Primitivo | None:
        """Busca um primitivo pelo identificador."""
        for primitivo in self.primitivos:
            if primitivo.id == id:
                return primitivo
        return None

    def remover(self, id: str) -> bool:
        """Remove o primitivo de id dado. Retorna se algo foi removido."""
        alvo = self.obter(id)
        if alvo is None:
            return False
        self.primitivos.remove(alvo)
        return True

    def limpar(self) -> None:
        """Esvazia a figura e reinicia os contadores de id."""
        self.primitivos.clear()
        self._contadores = {tipo: 0 for tipo in TIPOS}

    def desenhar(self, imagem: Imagem, tipo: str = "all") -> int:
        """Rasteriza os primitivos, opcionalmente filtrando por tipo.

        Retorna quantos primitivos foram desenhados. Nao limpa a imagem: quem
        chama decide se quer redesenhar sobre o que ja existe.
        """
        if tipo != "all" and tipo not in TIPOS:
            raise ValueError(f'tipo desconhecido "{tipo}"')
        desenhados = 0
        for primitivo in self.primitivos:
            if tipo == "all" or primitivo.tipo == tipo:
                primitivo.desenhar(imagem)
                desenhados += 1
        return desenhados

    def listar(self) -> list[dict]:
        """Resumo de todos os primitivos, para a interface."""
        return [primitivo.para_dict() for primitivo in self.primitivos]

    def contagem_por_tipo(self) -> dict[str, int]:
        """Quantidade de primitivos de cada tipo presente na figura."""
        contagem: dict[str, int] = {}
        for primitivo in self.primitivos:
            contagem[primitivo.tipo] = contagem.get(primitivo.tipo, 0) + 1
        return contagem


def primitivo_de_payload(dados: object) -> Primitivo:
    """Constroi um primitivo a partir de um payload em coordenadas de pixel.

    E o formato simetrico ao de `Primitivo.para_dict`: o que a API devolve em
    /api/estado e o que ela aceita em /api/primitivo, sem o id. Nao confundir
    com o formato do arquivo, que usa coordenadas normalizadas e fica em
    `serializacao.py`.
    """
    if not isinstance(dados, dict):
        raise ValueError("o payload deve ser um objeto")

    tipo = dados.get("tipo")
    if not tipo:
        raise ValueError('campo obrigatorio "tipo" ausente')
    if tipo not in TIPOS:
        raise ValueError(f'tipo desconhecido "{tipo}"')

    cor = Cor.de_dict(dados["cor"]) if "cor" in dados else Cor(0, 0, 0)
    esp = sanitizar_espessura(dados.get("esp", 1))

    def ler(campo: str) -> Ponto2D:
        if campo not in dados:
            raise ValueError(f'campo obrigatorio "{campo}" ausente')
        return Ponto2D.de_dict(dados[campo], campo)

    if tipo == "ponto":
        return Ponto(ler("p"), cor, esp)
    if tipo == "reta":
        return Reta(ler("p1"), ler("p2"), cor, esp)
    if tipo == "triangulo":
        return Triangulo(ler("p1"), ler("p2"), ler("p3"), cor, esp)
    if tipo == "retangulo":
        return Retangulo(ler("p1"), ler("p2"), cor, esp)
    return Circulo(ler("centro"), ler("borda"), cor, esp)
