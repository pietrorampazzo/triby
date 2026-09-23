@echo off
title Disparador de Leads - Disparo Unico / Cron
cd /d "%~dp0"
.venv\Scripts\python.exe main.py --mode once
