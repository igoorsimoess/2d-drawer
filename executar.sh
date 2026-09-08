#!/usr/bin/env bash
#
# Inicia o servidor do Desenhador2D.
#
# Cada passo e explicito e informa o que esta fazendo, para que seja possivel
# executar as operacoes manualmente caso algo falhe.

set -u

HOST="${HOST:-127.0.0.1}"
PORTA="${PORTA:-8000}"

cd "$(dirname "$0")" || exit 1

echo "==> Verificando o uv"
if ! command -v uv >/dev/null 2>&1; then
    echo "ERRO: 'uv' nao encontrado no PATH."
    echo "Instale com: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
echo "    $(uv --version)"

echo "==> Sincronizando dependencias (uv sync)"
if ! uv sync; then
    echo "ERRO: falha ao sincronizar as dependencias."
    exit 1
fi

echo "==> Verificando se a porta ${PORTA} esta livre"
if lsof -i ":${PORTA}" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "ERRO: a porta ${PORTA} ja esta em uso."
    echo "Descubra o processo com: lsof -i :${PORTA} -sTCP:LISTEN"
    echo "Ou use outra porta com:  PORTA=8001 ./executar.sh"
    exit 1
fi

echo "==> Iniciando o servidor em http://${HOST}:${PORTA}"
echo "    Pressione Ctrl+C para encerrar."
exec uv run uvicorn backend.app.main:app --host "${HOST}" --port "${PORTA}" --reload
