"""Ponto de entrada da aplicacao FastAPI do Desenhador2D."""

from fastapi import FastAPI

app = FastAPI(title="Desenhador2D")


@app.get("/saude")
async def saude() -> dict:
    """Endpoint trivial usado para verificar se o servidor subiu."""
    return {"ok": True}
