@echo off
title Disparador de Leads & Monitor - Modo Contínuo (1 min)
cd /d "%~dp0"
echo ========================================================
echo Iniciando Disparador de Leads (Modo Loop a cada 1 min)
echo ========================================================
.venv\Scripts\python.exe main.py --mode loop
pause
