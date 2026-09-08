"""Ponto de entrada da aplicacao FastAPI do Desenhador2D."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import roteador

# Resolvido a partir do arquivo, e nao do diretorio de trabalho, para que o
# servidor suba corretamente independente de onde o comando foi executado.
FRONTEND = Path(__file__).resolve().parents[2] / "frontend"

app = FastAPI(title="Desenhador2D")
app.include_router(roteador)
app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/")
async def index() -> FileResponse:
    """Serve a pagina principal."""
    return FileResponse(FRONTEND / "index.html")
