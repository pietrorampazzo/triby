@echo off
title Disparador de Leads - MVP 10 Leads
cd /d "%~dp0"
echo ========================================================
echo Iniciando Disparador de Leads (MVP 10 Envios a cada 1 min)
echo ========================================================
.venv\Scripts\python.exe -u main.py --mode loop --limit 10
pause
