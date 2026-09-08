"""Buffer de pixels RGBA da aplicacao.

A imagem e um array NumPy de shape (altura, largura, 4) e dtype uint8, que
mapeia diretamente para o ImageData do canvas HTML no frontend.
"""

from __future__ import annotations

import numpy as np

from .color import BRANCO, Cor

# Mascaras de disco ja calculadas, indexadas pela espessura.
# Evita recalcular a mesma mascara para cada pixel rasterizado de uma reta.
_CACHE_DISCO: dict[int, tuple[np.ndarray, np.ndarray]] = {}


def mascara_disco(esp: int) -> tuple[np.ndarray, np.ndarray]:
    """Retorna os deslocamentos (dy, dx) de um disco cheio de diametro `esp`.

    O disco e o "carimbo" usado para dar espessura ao traco: cada pixel
    rasterizado por um algoritmo pinta um disco em vez de um unico pixel.

    Espessuras impares ficam centradas no pixel; espessuras pares nao tem
    centro exato na grade, entao o disco e deslocado meio pixel para que a
    largura resultante seja exatamente `esp` (ficando um pixel mais para a
    direita e para baixo do que para a esquerda e para cima).
    """
    esp = max(1, int(esp))
    if esp in _CACHE_DISCO:
        return _CACHE_DISCO[esp]

    raio = esp / 2.0
    # Espessura par: o centro do disco cai entre pixels.
    deslocamento = 0.0 if esp % 2 == 1 else 0.5
    limite = int(np.ceil(raio))
    faixa = np.arange(-limite, limite + 1)
    dy, dx = np.meshgrid(faixa, faixa, indexing="ij")
    dentro = ((dx - deslocamento) ** 2 + (dy - deslocamento) ** 2) <= raio**2
    resultado = (dy[dentro].astype(np.intp), dx[dentro].astype(np.intp))
    _CACHE_DISCO[esp] = resultado
    return resultado


class Imagem:
    """Matriz de pixels RGBA sobre a qual os primitivos sao rasterizados."""

    def __init__(self, largura: int, altura: int, fundo: Cor = BRANCO) -> None:
        """Cria a imagem com as dimensoes dadas, preenchida com a cor de fundo."""
        if largura <= 0 or altura <= 0:
            raise ValueError("largura e altura devem ser positivas")
        self.largura = int(largura)
        self.altura = int(altura)
        self.fundo = fundo
        self.buffer = np.empty((self.altura, self.largura, 4), dtype=np.uint8)
        self.limpar()

    def limpar(self) -> None:
        """Preenche toda a imagem com a cor de fundo."""
        self.buffer[:, :] = self.fundo.para_rgba()

    def dentro(self, x: int, y: int) -> bool:
        """Informa se a coordenada cai dentro dos limites da imagem."""
        return 0 <= x < self.largura and 0 <= y < self.altura

    def set_pixel(self, x: int, y: int, cor: Cor) -> None:
        """Pinta um unico pixel, ignorando coordenadas fora da imagem."""
        if self.dentro(x, y):
            self.buffer[y, x] = cor.para_rgba()

    def get_pixel(self, x: int, y: int) -> Cor | None:
        """Le a cor de um pixel, ou None se estiver fora da imagem."""
        if not self.dentro(x, y):
            return None
        r, g, b, _ = self.buffer[y, x]
        return Cor(int(r), int(g), int(b))

    def carimbar(self, x: int, y: int, cor: Cor, esp: int = 1) -> None:
        """Pinta um disco de diametro `esp` centrado em (x, y).

        E o unico ponto do sistema que trata espessura: todos os algoritmos de
        rasterizacao chamam este metodo, o que garante tracos de largura
        uniforme e juntas arredondadas para retas, circulos, retangulos e
        triangulos com uma unica implementacao.
        """
        esp = max(1, int(esp))
        if esp == 1:
            self.set_pixel(x, y, cor)
            return

        dy, dx = mascara_disco(esp)
        ys = dy + int(y)
        xs = dx + int(x)
        visiveis = (xs >= 0) & (xs < self.largura) & (ys >= 0) & (ys < self.altura)
        self.buffer[ys[visiveis], xs[visiveis]] = cor.para_rgba()

    def para_bytes(self) -> bytes:
        """Retorna o buffer RGBA cru, pronto para virar um ImageData no cliente."""
        return self.buffer.tobytes()
