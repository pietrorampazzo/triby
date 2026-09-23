@echo off
title Disparo para Grupos WhatsApp - Barsi
cd /d "%~dp0"
echo ========================================================
echo Disparo para Grupos WhatsApp - Barsi
echo ========================================================
echo.
echo Escolha uma opcao:
echo [1] Disparar AGORA para os 13 grupos (Mensagem do template)
echo [2] Simulacao de Teste (DRY-RUN - sem enviar mensagens reais)
echo [3] Listar grupos cadastrados
echo [4] Sair
echo.
set /p opt="Digite a opcao [1-4]: "

if "%opt%"=="1" (
    echo.
    echo Iniciando disparo real com intervalo anti-spam...
    node disparo_barsi.js
    pause
    exit /b
)

if "%opt%"=="2" (
    echo.
    echo Rodando simulacao dry-run...
    node disparo_barsi.js --dry-run
    pause
    exit /b
)

if "%opt%"=="3" (
    echo.
    node disparo_barsi.js --list
    pause
    exit /b
)

echo Saindo...
