"""Testes do nucleo grafico: Cor, Ponto2D e Imagem."""

import numpy as np
import pytest

from backend.app.graphics.color import BRANCO, Cor
from backend.app.graphics.image import Imagem, mascara_disco
from backend.app.graphics.point import Ponto2D


class TestCor:
    def test_para_rgba_sempre_opaca(self):
        assert Cor(10, 20, 30).para_rgba() == (10, 20, 30, 255)

    @pytest.mark.parametrize("canais", [(-1, 0, 0), (0, 256, 0), (0, 0, 300)])
    def test_rejeita_canal_fora_do_intervalo(self, canais):
        with pytest.raises(ValueError):
            Cor(*canais)

    def test_de_dict_ida_e_volta(self):
        original = Cor(0, 102, 102)
        assert Cor.de_dict(original.para_dict()) == original

    def test_de_dict_sem_canal_avisa_qual(self):
        with pytest.raises(ValueError, match="canal"):
            Cor.de_dict({"r": 1, "g": 2})

    def test_de_dict_rejeita_nao_objeto(self):
        with pytest.raises(ValueError):
            Cor.de_dict([1, 2, 3])


class TestPonto2D:
    def test_distancia_euclidiana(self):
        assert Ponto2D(0, 0).distancia(Ponto2D(3, 4)) == pytest.approx(5.0)

    def test_rejeita_coordenada_nao_inteira(self):
        with pytest.raises(ValueError):
            Ponto2D(1.5, 2)

    def test_de_dict_arredonda(self):
        assert Ponto2D.de_dict({"x": 2.6, "y": 3.2}) == Ponto2D(3, 3)


class TestMascaraDisco:
    @pytest.mark.parametrize("esp", range(1, 21))
    def test_largura_resultante_e_exatamente_esp(self, esp):
        """A largura do carimbo deve bater com a espessura pedida."""
        dy, dx = mascara_disco(esp)
        assert dx.max() - dx.min() + 1 == esp
        assert dy.max() - dy.min() + 1 == esp

    def test_espessura_um_e_um_unico_pixel(self):
        dy, dx = mascara_disco(1)
        assert len(dx) == 1 and dx[0] == 0 and dy[0] == 0

    def test_disco_e_redondo_e_nao_quadrado(self):
        """Os cantos de um disco de espessura 5 nao devem ser pintados."""
        dy, dx = mascara_disco(5)
        pontos = set(zip(dx.tolist(), dy.tolist()))
        assert (0, 0) in pontos
        assert (2, 2) not in pontos

    def test_espessura_invalida_degenera_para_um(self):
        for esp in (0, -3):
            dy, dx = mascara_disco(esp)
            assert len(dx) == 1


class TestImagem:
    def test_comeca_toda_com_a_cor_de_fundo(self):
        img = Imagem(4, 3)
        assert np.all(img.buffer == np.array(BRANCO.para_rgba(), dtype=np.uint8))

    def test_dimensoes_do_buffer(self):
        img = Imagem(64, 48)
        assert img.buffer.shape == (48, 64, 4)
        assert img.buffer.dtype == np.uint8

    def test_rejeita_dimensao_nao_positiva(self):
        with pytest.raises(ValueError):
            Imagem(0, 10)

    def test_set_e_get_pixel(self):
        img = Imagem(8, 8)
        img.set_pixel(3, 5, Cor(255, 0, 0))
        assert img.get_pixel(3, 5) == Cor(255, 0, 0)

    def test_set_pixel_fora_dos_limites_e_ignorado(self):
        """Escrever fora da imagem nao pode levantar excecao nem alterar nada."""
        img = Imagem(4, 4)
        antes = img.buffer.copy()
        for x, y in [(-1, 0), (0, -1), (4, 0), (0, 4), (99, 99)]:
            img.set_pixel(x, y, Cor(255, 0, 0))
        assert np.array_equal(img.buffer, antes)
        assert img.get_pixel(-1, 0) is None

    def test_carimbo_pinta_o_numero_certo_de_pixels(self):
        img = Imagem(40, 40)
        _, dx = mascara_disco(7)
        img.carimbar(20, 20, Cor(0, 0, 0), 7)
        pintados = int(np.count_nonzero(np.all(img.buffer[:, :, :3] == 0, axis=2)))
        assert pintados == len(dx)

    def test_carimbo_e_recortado_na_borda(self):
        """Um carimbo grande no canto so pinta a parte visivel, sem estourar."""
        img = Imagem(10, 10)
        img.carimbar(0, 0, Cor(0, 0, 0), 9)
        assert img.get_pixel(0, 0) == Cor(0, 0, 0)
        assert img.get_pixel(9, 9) == BRANCO

    def test_carimbo_totalmente_fora_nao_altera_nada(self):
        img = Imagem(10, 10)
        antes = img.buffer.copy()
        img.carimbar(-50, -50, Cor(0, 0, 0), 3)
        assert np.array_equal(img.buffer, antes)

    def test_limpar_restaura_o_fundo(self):
        img = Imagem(10, 10)
        img.carimbar(5, 5, Cor(1, 2, 3), 5)
        img.limpar()
        assert np.all(img.buffer == np.array(BRANCO.para_rgba(), dtype=np.uint8))

    def test_para_bytes_tem_o_tamanho_esperado(self):
        img = Imagem(64, 48)
        assert len(img.para_bytes()) == 64 * 48 * 4
