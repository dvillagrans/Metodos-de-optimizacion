#!/usr/bin/env python3
"""
Script simple para probar la generación de video
"""

import os
import sys
import subprocess

# Cambiar al directorio de animaciones
animation_dir = r"c:\Users\diego\workspace\metodos-optimizacion\manim_anim"
os.chdir(animation_dir)

# Verificar que manim esté instalado
try:
    result = subprocess.run([sys.executable, "-m", "manim", "--version"], 
                          capture_output=True, text=True)
    print(f"Manim version: {result.stdout.strip()}")
except Exception as e:
    print(f"Error checking Manim: {e}")
    sys.exit(1)

# Probar generar video 2D
print("Generando video 2D...")
cmd = [
    sys.executable,
    "-m", "manim",
    "simplex_2d_anim.py",
    "Simplex2DAnim",
    "-qm",  # Medium quality
    "--format", "mp4",
    "--media_dir=../output/videos",
    "--disable_caching"
]

print(f"Ejecutando: {' '.join(cmd)}")

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    
    print(f"Return code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    if result.stderr:
        print(f"Stderr: {result.stderr}")
    
    if result.returncode == 0:
        print("✅ Video generado exitosamente!")
    else:
        print("❌ Error al generar video")
        
except subprocess.TimeoutExpired:
    print("❌ Timeout - el proceso tomó demasiado tiempo")
except Exception as e:
    print(f"❌ Error: {e}")
