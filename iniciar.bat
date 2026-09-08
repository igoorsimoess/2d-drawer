@echo off
title Desenhador2D
echo ========================================
echo         Desenhador2D - Servidor
echo ========================================
echo.

cd /d "%~dp0"

echo Verificando o uv...
where uv >nul 2>nul
if errorlevel 1 (
    echo ERRO: 'uv' nao encontrado no PATH.
    echo Instale com: powershell -c "irm https://astral.sh/uv/install.ps1 ^| iex"
    pause
    exit /b 1
)

echo Sincronizando dependencias...
uv sync
if errorlevel 1 (
    echo ERRO: falha ao sincronizar as dependencias.
    pause
    exit /b 1
)

echo.
echo Iniciando servidor em http://127.0.0.1:8000
echo Pressione Ctrl+C para encerrar.
echo.

start http://127.0.0.1:8000

uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

pause
