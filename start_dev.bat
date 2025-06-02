@echo off
echo 🚀 Iniciando servidor de desarrollo...
echo ⚡ Auto-reload activado
echo 🌐 Servidor corriendo en: http://localhost:5000
echo 🛑 Presiona Ctrl+C para detener
echo.

REM Verificar si existe el entorno virtual
if exist "metodos-optimizacion\Scripts\activate.bat" (
    echo 🐍 Activando entorno virtual...
    call metodos-optimizacion\Scripts\activate.bat
)

REM Instalar dependencias si no están
python -c "import watchdog" 2>nul || pip install watchdog

REM Ejecutar el servidor de desarrollo
python dev_server.py

pause
