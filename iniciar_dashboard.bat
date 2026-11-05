@echo off
cd /d %~dp0
title Gestao de Ensaios M3 - http://localhost:8110
py -c "import openpyxl" 2>nul || py -m pip install --user openpyxl
powershell -NoProfile -ExecutionPolicy Bypass -Command "$d=[Environment]::GetFolderPath('Desktop'); $p=Join-Path $d 'Gestao de Ensaios M3.lnk'; if(!(Test-Path $p)){ $s=(New-Object -ComObject WScript.Shell).CreateShortcut($p); $s.TargetPath='%~dp0iniciar_dashboard.bat'; $s.WorkingDirectory='%~dp0'; $s.Save(); Write-Host 'Atalho criado na area de trabalho.' }" 2>nul
py atualizar.py
py app.py
pause
