@echo off
title Teste de Conexao Google Workspace
cd /d "%~dp0"
.venv\Scripts\python.exe main.py --test
pause
