#!/usr/bin/env python3
"""
Servidor de desarrollo con auto-reload mejorado
Uso: python dev_server.py
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FlaskReloadHandler(FileSystemEventHandler):
    """Manejador de eventos para recargar Flask cuando cambian los archivos"""
    
    def __init__(self, process):
        self.process = process
        self.last_restart = 0
        self.restart_delay = 1  # Esperar 1 segundo entre reinicios
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Solo recargar para archivos Python y templates
        if event.src_path.endswith(('.py', '.html', '.js', '.css')):
            current_time = time.time()
            if current_time - self.last_restart > self.restart_delay:
                print(f"\n🔄 Detectado cambio en: {event.src_path}")
                print("🔄 Reiniciando servidor...")
                self.restart_server()
                self.last_restart = current_time
    
    def restart_server(self):
        """Reinicia el proceso del servidor Flask"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
        
        # Iniciar nuevo proceso
        self.process = subprocess.Popen([
            sys.executable, 'run.py'
        ], cwd=os.getcwd())

def main():
    """Función principal del servidor de desarrollo"""
    print("🚀 Iniciando servidor de desarrollo con auto-reload...")
    print("📁 Directorio de trabajo:", os.getcwd())
    print("🐍 Python:", sys.executable)
    print("=" * 50)
    
    # Verificar que existe run.py
    if not os.path.exists('run.py'):
        print("❌ Error: No se encontró run.py en el directorio actual")
        return
    
    # Iniciar el servidor Flask
    flask_process = subprocess.Popen([
        sys.executable, 'run.py'
    ], cwd=os.getcwd())
    
    # Configurar el observador de archivos
    event_handler = FlaskReloadHandler(flask_process)
    observer = Observer()
    
    # Observar directorios relevantes
    watch_dirs = ['app', 'manim_anim']
    for dir_name in watch_dirs:
        if os.path.exists(dir_name):
            observer.schedule(event_handler, dir_name, recursive=True)
            print(f"👀 Observando cambios en: {dir_name}/")
    
    # También observar archivos en el directorio raíz
    observer.schedule(event_handler, '.', recursive=False)
    print("👀 Observando cambios en archivos raíz")
    
    observer.start()
    
    print("\n✅ Servidor iniciado!")
    print("🌐 Dirección: http://localhost:5000")
    print("⚡ Auto-reload activado")
    print("🛑 Presiona Ctrl+C para detener")
    print("=" * 50)
    
    try:
        while True:
            time.sleep(1)
            # Verificar si el proceso Flask sigue corriendo
            if flask_process.poll() is not None:
                print("⚠️  El proceso Flask se detuvo inesperadamente")
                break
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servidor...")
        observer.stop()
        if flask_process.poll() is None:
            flask_process.terminate()
            flask_process.wait()
        print("✅ Servidor detenido")
    
    observer.join()

if __name__ == '__main__':
    main()
