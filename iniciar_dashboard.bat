@echo off
cd /d %~dp0
title Gestao de Ensaios M3 - http://localhost:8110
py -c "import openpyxl" 2>nul || py -m pip install --user openpyxl
py atualizar.py
py app.py
pause
