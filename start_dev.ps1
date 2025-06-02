# Script de desarrollo para Flask con auto-reload
Write-Host "🚀 Iniciando servidor de desarrollo..." -ForegroundColor Green
Write-Host "⚡ Auto-reload activado" -ForegroundColor Yellow
Write-Host "🌐 Servidor corriendo en: http://localhost:5000" -ForegroundColor Cyan
Write-Host "🛑 Presiona Ctrl+C para detener" -ForegroundColor Red
Write-Host ""

# Verificar si existe el entorno virtual
if (Test-Path "metodos-optimizacion\Scripts\Activate.ps1") {
    Write-Host "🐍 Activando entorno virtual..." -ForegroundColor Blue
    & "metodos-optimizacion\Scripts\Activate.ps1"
}

# Verificar e instalar dependencias
try {
    python -c "import watchdog" 2>$null
} catch {
    Write-Host "📦 Instalando watchdog..." -ForegroundColor Yellow
    pip install watchdog
}

# Ejecutar el servidor de desarrollo
try {
    python dev_server.py
} catch {
    Write-Host "❌ Error al iniciar el servidor" -ForegroundColor Red
    Write-Host "💡 Verifica que tengas Python y Flask instalados" -ForegroundColor Yellow
}

Read-Host "Presiona Enter para salir"
