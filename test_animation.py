#!/usr/bin/env python3
"""
Script simple para probar la generación de animaciones Manim
"""

import os
import json
import subprocess
import sys

def test_animation():
    # Crear datos de prueba
    test_data = {
        "c": [3.0, 4.0, 6.0],
        "A": [[1.0, 1.0, 1.0], [2.0, 1.0, 0.0], [0.0, 1.0, 2.0]], 
        "b": [10.0, 8.0, 7.0],
        "solution": [4.0, 0.0, 3.5],
        "z_opt": 33.0,
        "minimize": False
    }
    
    # Cambiar al directorio de animaciones
    animation_dir = "manim_anim"
    os.chdir(animation_dir)
    
    # Guardar datos de prueba
    with open("problem_data.json", "w") as f:
        json.dump(test_data, f, indent=2)
    
    print("Datos guardados en problem_data.json")
    
    # Ejecutar animación con mejor manejo de errores
    cmd = [
        sys.executable,
        "-m", "manim",
        "simplex_3d_anim.py",
        "Simplex3DAnim",
        "-ql",  # Calidad baja para mejor rendimiento
        "--format", "gif",
        "--disable_caching",
        "-v", "INFO"  # Verboso para debug
    ]
    
    print(f"Ejecutando: {' '.join(cmd)}")
    
    try:
        # Ejecutar con captura de salida
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos
        )
        
        print(f"Código de retorno: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        
        # Buscar archivos generados
        print("\nBuscando archivos generados...")
        for root, dirs, files in os.walk("media"):
            for file in files:
                if "Simplex3DAnim" in file:
                    full_path = os.path.join(root, file)
                    print(f"Encontrado: {full_path}")
        
    except subprocess.TimeoutExpired:
        print("La animación tardó demasiado tiempo (>5 minutos)")
    except Exception as e:
        print(f"Error ejecutando animación: {e}")

if __name__ == "__main__":
    test_animation()
