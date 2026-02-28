@echo off
title validationidea - Monitor Automatico
color 0A
echo ============================================
echo  VALIDATIONIDEA - Generador Automatico
echo  Genera ideas cada 30 minutos
echo  Cierra esta ventana para parar
echo ============================================
cd /d "C:\Users\juanj\Documents\validationidea"
:inicio
python run_monitor.py
echo.
echo ⚠️ Monitor parado. Reiniciando en 10 segundos...
timeout /t 10
goto inicio
