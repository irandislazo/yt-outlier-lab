@echo off
chcp 65001 >nul
echo ══════════════════════════════════════════════════════════
echo  YT OUTLIER LAB — Compilando con cx_Freeze
echo ══════════════════════════════════════════════════════════
echo.

REM Limpiar build anterior
if exist "build" rmdir /s /q "build"

REM Compilar
python setup.py build_exe

if errorlevel 1 (
    echo.
    echo ❌ ERROR en la compilación.
    echo Revisa el mensaje de arriba.
    pause
    exit /b 1
)

echo.
echo ══════════════════════════════════════════════════════════
echo  ✅ COMPILACIÓN COMPLETA
echo ══════════════════════════════════════════════════════════
echo.
echo  Ejecutable en: build\exe.win-amd64-3.11\YT-Outlier-Lab.exe
echo.
echo  Para probar:
echo  1. Copia tu .env a esa carpeta
echo  2. Ejecuta YT-Outlier-Lab.exe
echo  3. Si hay error, revisa error_log.txt en esa carpeta
echo.
pause