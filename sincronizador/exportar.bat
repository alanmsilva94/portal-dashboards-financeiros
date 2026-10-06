@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Convertendo os Excel em JSON (pasta dados_para_drive)...
python exportar_para_drive.py %*
echo.
echo Pronto. Agora envie o conteudo de cada subpasta de dados_para_drive para a pasta de mesmo nome
echo em Dashboards_Portal_dados no Google Drive (drive.google.com). Veja o README.
pause
