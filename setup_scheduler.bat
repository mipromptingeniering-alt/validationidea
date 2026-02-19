@echo off
REM ============================================================
REM setup_scheduler.bat
REM Configura Windows Task Scheduler para ejecutar run_continuous.py
REM al inicio del sistema (automaticamente)
REM
REM INSTRUCCIONES: Clic derecho -> "Ejecutar como administrador"
REM ============================================================

SET PROJECT_DIR=C:\Users\juanj\Documents\validationidea
SET PYTHON_EXE=python
SET TASK_NAME=ValidationIdea-Auto

echo.
echo [1/3] Eliminando tarea anterior si existe...
schtasks /delete /tn "%TASK_NAME%" /f 2>nul
echo     OK

echo.
echo [2/3] Creando tarea automatica...
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "cmd /c cd /d %PROJECT_DIR% && %PYTHON_EXE% run_continuous.py >> data\system.log 2>&1" ^
    /sc onlogon ^
    /ru "%USERNAME%" ^
    /rl HIGHEST ^
    /f

echo.
echo [3/3] Verificando tarea creada...
schtasks /query /tn "%TASK_NAME%" /fo LIST

echo.
echo ============================================================
echo  COMPLETADO
echo  La tarea "%TASK_NAME%" se ejecutara al iniciar sesion en Windows
echo.
echo  Para iniciar AHORA sin reiniciar:
echo    cd %PROJECT_DIR%
echo    python run_continuous.py
echo.
echo  Para ver el log en tiempo real (PowerShell):
echo    Get-Content data\system.log -Wait
echo ============================================================
echo.
pause
