"""Testes das rotas REST, com TestClient e sem servidor no ar."""

import json
import pathlib

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.api.routes import ALTURA, LARGURA, estado
from backend.app.main import app

EXEMPLO = pathlib.Path(__file__).parent / "dados" / "figura_exemplo.json"
VERMELHO = {"r": 255, "g": 0, "b": 0}


@pytest.fixture
def cliente():
    """Cliente HTTP com o estado da aplicacao reiniciado a cada teste."""
    estado.reiniciar()
    with TestClient(app) as cliente:
        yield cliente
    estado.reiniciar()


def criar_reta(cliente, esp=3, **pontos):
    payload = {
        "tipo": "reta",
        "p1": pontos.get("p1", {"x": 100, "y": 100}),
        "p2": pontos.get("p2", {"x": 300, "y": 100}),
        "cor": VERMELHO,
        "esp": esp,
    }
    return cliente.post("/api/primitivo", json=payload)


class TestPaginaEEstado:
    def test_raiz_serve_o_frontend(self, cliente):
        assert cliente.get("/").status_code == 200

    def test_estado_inicial(self, cliente):
        dados = cliente.get("/api/estado").json()
        assert dados == {
            "largura": LARGURA, "altura": ALTURA,
            "figura": [], "contagem": {}, "selecionado": None,
        }


class TestImagem:
    def test_tamanho_do_buffer(self, cliente):
        resposta = cliente.get("/api/imagem")
        assert resposta.status_code == 200
        assert len(resposta.content) == LARGURA * ALTURA * 4

    def test_cabecalhos_com_dimensoes_e_sem_cache(self, cliente):
        resposta = cliente.get("/api/imagem")
        assert resposta.headers["x-largura"] == str(LARGURA)
        assert resposta.headers["x-altura"] == str(ALTURA)
        assert resposta.headers["cache-control"] == "no-store"

    def test_imagem_comeca_branca(self, cliente):
        buffer = np.frombuffer(cliente.get("/api/imagem").content, dtype=np.uint8)
        assert np.all(buffer == 255)

    def test_imagem_muda_apos_desenhar(self, cliente):
        antes = cliente.get("/api/imagem").content
        criar_reta(cliente)
        assert cliente.get("/api/imagem").content != antes


class TestCriacao:
    def test_cria_e_devolve_o_id(self, cliente):
        resposta = criar_reta(cliente)
        assert resposta.status_code == 200
        assert resposta.json()["primitivo"]["id"] == "reta_1"

    @pytest.mark.parametrize(
        "payload",
        [
            {"tipo": "ponto", "p": {"x": 50, "y": 50}},
            {"tipo": "reta", "p1": {"x": 1, "y": 1}, "p2": {"x": 9, "y": 9}},
            {"tipo": "retangulo", "p1": {"x": 1, "y": 1}, "p2": {"x": 9, "y": 9}},
            {"tipo": "triangulo", "p1": {"x": 1, "y": 1}, "p2": {"x": 9, "y": 1}, "p3": {"x": 5, "y": 9}},
            {"tipo": "circulo", "centro": {"x": 50, "y": 50}, "borda": {"x": 70, "y": 50}},
        ],
    )
    def test_aceita_todos_os_tipos(self, cliente, payload):
        resposta = cliente.post("/api/primitivo", json={**payload, "cor": VERMELHO, "esp": 2})
        assert resposta.status_code == 200

    @pytest.mark.parametrize(
        "payload,trecho",
        [
            ({}, "tipo"),
            ({"tipo": "hexagono"}, "desconhecido"),
            ({"tipo": "reta", "p1": {"x": 1, "y": 1}}, "p2"),
            ({"tipo": "reta", "p1": {"x": 1, "y": 1}, "p2": {"x": 2}}, "p2"),
            ({"tipo": "ponto", "p": {"x": 1, "y": 1}, "cor": {"r": 300, "g": 0, "b": 0}}, "cor"),
        ],
    )
    def test_payload_invalido_devolve_400_com_motivo(self, cliente, payload, trecho):
        resposta = cliente.post("/api/primitivo", json=payload)
        assert resposta.status_code == 400
        assert resposta.json()["ok"] is False
        assert trecho in resposta.json()["erro"]

    def test_estado_reflete_o_primitivo_criado(self, cliente):
        criar_reta(cliente)
        dados = cliente.get("/api/estado").json()
        assert dados["contagem"] == {"reta": 1}
        assert len(dados["figura"]) == 1


class TestSelecao:
    def test_seleciona_ao_clicar_sobre_o_traco(self, cliente):
        criar_reta(cliente)
        resposta = cliente.post("/api/selecionar", json={"x": 200, "y": 100}).json()
        assert resposta["selecionado"] == "reta_1"
        assert resposta["primitivo"]["tipo"] == "reta"

    def test_clique_no_vazio_limpa_a_selecao(self, cliente):
        criar_reta(cliente)
        cliente.post("/api/selecionar", json={"x": 200, "y": 100})
        resposta = cliente.post("/api/selecionar", json={"x": 700, "y": 500}).json()
        assert resposta["selecionado"] is None
        assert resposta["primitivo"] is None

    def test_selecao_aparece_no_estado(self, cliente):
        criar_reta(cliente)
        cliente.post("/api/selecionar", json={"x": 200, "y": 100})
        assert cliente.get("/api/estado").json()["selecionado"] == "reta_1"

    def test_coordenadas_invalidas(self, cliente):
        for payload in [{}, {"x": 1}, {"x": "a", "y": 1}]:
            resposta = cliente.post("/api/selecionar", json=payload)
            assert resposta.status_code == 400


class TestRemocao:
    def test_remove_e_apaga_da_imagem(self, cliente):
        branco = cliente.get("/api/imagem").content
        criar_reta(cliente)
        assert cliente.delete("/api/primitivo/reta_1").status_code == 200
        assert cliente.get("/api/estado").json()["figura"] == []
        assert cliente.get("/api/imagem").content == branco

    def test_remover_inexistente_devolve_404(self, cliente):
        resposta = cliente.delete("/api/primitivo/reta_99")
        assert resposta.status_code == 404
        assert resposta.json()["ok"] is False

    def test_remover_o_selecionado_limpa_a_selecao(self, cliente):
        criar_reta(cliente)
        cliente.post("/api/selecionar", json={"x": 200, "y": 100})
        cliente.delete("/api/primitivo/reta_1")
        assert cliente.get("/api/estado").json()["selecionado"] is None

    def test_remocao_preserva_os_demais(self, cliente):
        criar_reta(cliente)
        criar_reta(cliente, p1={"x": 100, "y": 300}, p2={"x": 300, "y": 300})
        cliente.delete("/api/primitivo/reta_1")
        assert [p["id"] for p in cliente.get("/api/estado").json()["figura"]] == ["reta_2"]


class TestRedesenharELimpar:
    def test_filtro_por_tipo(self, cliente):
        criar_reta(cliente)
        cliente.post("/api/primitivo", json={
            "tipo": "ponto", "p": {"x": 400, "y": 400}, "cor": VERMELHO, "esp": 5,
        })
        assert cliente.post("/api/redesenhar", json={"tipo": "reta"}).json()["desenhados"] == 1
        assert cliente.post("/api/redesenhar", json={"tipo": "all"}).json()["desenhados"] == 2

    def test_tipo_invalido_no_redesenho(self, cliente):
        assert cliente.post("/api/redesenhar", json={"tipo": "hexagono"}).status_code == 400

    def test_limpar_preserva_a_figura(self, cliente):
        """Comportamento historico: limpar a tela nao apaga a estrutura de dados."""
        criar_reta(cliente)
        branco = np.full(LARGURA * ALTURA * 4, 255, dtype=np.uint8).tobytes()
        assert cliente.post("/api/limpar", json={}).json()["figura_limpa"] is False
        assert cliente.get("/api/imagem").content == branco
        assert len(cliente.get("/api/estado").json()["figura"]) == 1

    def test_limpar_com_figura_esvazia_tudo(self, cliente):
        criar_reta(cliente)
        assert cliente.post("/api/limpar", json={"figura": True}).json()["figura_limpa"] is True
        assert cliente.get("/api/estado").json()["figura"] == []

    def test_redesenhar_apos_limpar_recupera_a_imagem(self, cliente):
        criar_reta(cliente)
        com_reta = cliente.get("/api/imagem").content
        cliente.post("/api/limpar", json={})
        cliente.post("/api/redesenhar", json={"tipo": "all"})
        assert cliente.get("/api/imagem").content == com_reta


class TestExportarEImportar:
    def test_exporta_no_formato_do_arquivo(self, cliente):
        criar_reta(cliente)
        dados = cliente.get("/api/figura/exportar").json()
        assert set(dados) == {"figura"}
        assert dados["figura"]["reta"][0]["id"] == "reta_1"

    def test_importa_o_exemplo_do_enunciado(self, cliente):
        exemplo = json.loads(EXEMPLO.read_text())
        resposta = cliente.post("/api/figura/importar", json=exemplo).json()
        assert resposta["importados"] == 11
        assert resposta["desenhados"] == 11

    def test_importar_substitui_a_figura_anterior(self, cliente):
        criar_reta(cliente)
        cliente.post("/api/figura/importar", json=json.loads(EXEMPLO.read_text()))
        contagem = cliente.get("/api/estado").json()["contagem"]
        assert contagem["reta"] == 1
        assert contagem["circulo"] == 3

    def test_ciclo_exportar_limpar_importar_reproduz_a_imagem(self, cliente):
        """Requisito de persistencia: o arquivo tem de reconstruir o desenho."""
        criar_reta(cliente, esp=7)
        cliente.post("/api/primitivo", json={
            "tipo": "circulo", "centro": {"x": 400, "y": 300},
            "borda": {"x": 500, "y": 300}, "cor": {"r": 0, "g": 102, "b": 102}, "esp": 4,
        })
        original = cliente.get("/api/imagem").content
        arquivo = cliente.get("/api/figura/exportar").json()

        cliente.post("/api/limpar", json={"figura": True})
        assert cliente.get("/api/imagem").content != original

        cliente.post("/api/figura/importar", json=arquivo)
        assert cliente.get("/api/imagem").content == original

    def test_importar_json_invalido_preserva_a_figura_atual(self, cliente):
        criar_reta(cliente)
        antes = cliente.get("/api/imagem").content
        resposta = cliente.post("/api/figura/importar", json={"figura": {"reta": [{}]}})
        assert resposta.status_code == 400
        assert "reta[0]" in resposta.json()["erro"]
        assert len(cliente.get("/api/estado").json()["figura"]) == 1
        assert cliente.get("/api/imagem").content == antes

    def test_importar_sem_a_chave_raiz(self, cliente):
        resposta = cliente.post("/api/figura/importar", json={"reta": []})
        assert resposta.status_code == 400
        assert "figura" in resposta.json()["erro"]


class TestCaixaEnvolvente:
    """A caixa vai no /api/estado para o cliente destacar a selecao."""

    def test_todo_primitivo_traz_a_caixa(self, cliente):
        criar_reta(cliente)
        primitivo = cliente.get("/api/estado").json()["figura"][0]
        assert primitivo["caixa"] == [100, 100, 300, 100]

    def test_caixa_do_circulo_cobre_a_circunferencia(self, cliente):
        cliente.post("/api/primitivo", json={
            "tipo": "circulo", "centro": {"x": 400, "y": 300},
            "borda": {"x": 450, "y": 300}, "cor": VERMELHO, "esp": 1,
        })
        primitivo = cliente.get("/api/estado").json()["figura"][0]
        assert primitivo["caixa"] == [350, 250, 450, 350]

    def test_caixa_vem_na_resposta_da_selecao(self, cliente):
        criar_reta(cliente)
        resposta = cliente.post("/api/selecionar", json={"x": 200, "y": 100}).json()
        assert resposta["primitivo"]["caixa"] == [100, 100, 300, 100]
