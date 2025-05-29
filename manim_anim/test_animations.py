#!/usr/bin/env python3
"""
Script de prueba para generar videos de animaciones de métodos de optimización
"""

import sys
import os
import json
import shutil

# Agregar el directorio del proyecto al path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

from app.manim_renderer import generate_manim_animation

def test_2d_animation():
    """Prueba la animación 2D del método Simplex"""
    print("🎬 Generando animación 2D del método Simplex...")
    
    # Cargar datos del problema 2D
    with open('test_problem_2d.json', 'r') as f:
        data = json.load(f)
    
    # Generar animación
    video_path = generate_manim_animation(
        c=data['c'],
        A=data['A'],
        b=data['b'],
        solution=data['solution'],
        z_opt=data['z_opt'],
        minimize=data['minimize'],
        method=data['method']
    )
    
    if video_path:
        print(f"✅ Video 2D generado exitosamente: {video_path}")
        return video_path
    else:
        print("❌ Error al generar video 2D")
        return None

def test_3d_animation():
    """Prueba la animación 3D del método Simplex"""
    print("🎬 Generando animación 3D del método Simplex...")
    
    # Cargar datos del problema 3D
    with open('test_problem_3d.json', 'r') as f:
        data = json.load(f)
    
    # Generar animación
    video_path = generate_manim_animation(
        c=data['c'],
        A=data['A'],
        b=data['b'],
        solution=data['solution'],
        z_opt=data['z_opt'],
        minimize=data['minimize'],
        method=data['method']
    )
    
    if video_path:
        print(f"✅ Video 3D generado exitosamente: {video_path}")
        return video_path
    else:
        print("❌ Error al generar video 3D")
        return None

def test_granm_animation():
    """Prueba la animación del método Gran M"""
    print("🎬 Generando animación del método Gran M...")
    
    # Crear datos de prueba para Gran M
    granm_data = {
        "c": [3.0, 5.0],
        "A": [[2.0, 1.0], [1.0, 2.0]],
        "b": [8.0, 7.0],
        "solution": [2.0, 2.5],
        "z_opt": 18.5,
        "minimize": False,
        "method": "granm",
        "artificial_variables": ["a1", "a2"],
        "tableau_history": [
            [["x1", "x2", "a1", "a2", "RHS"], [2, 1, 1, 0, 8], [1, 2, 0, 1, 7]],
            [["x1", "x2", "a1", "a2", "RHS"], [1, 0.5, 0.5, 0, 4], [0, 1.5, -0.5, 1, 3]]
        ]
    }
    
    video_path = generate_manim_animation(
        c=granm_data['c'],
        A=granm_data['A'],
        b=granm_data['b'],
        solution=granm_data['solution'],
        z_opt=granm_data['z_opt'],
        minimize=granm_data['minimize'],
        method=granm_data['method'],
        tableau_history=granm_data.get('tableau_history')
    )
    
    if video_path:
        print(f"✅ Video Gran M generado exitosamente: {video_path}")
        return video_path
    else:
        print("❌ Error al generar video Gran M")
        return None

def main():
    """Función principal para ejecutar todas las pruebas"""
    print("🚀 Iniciando pruebas de generación de videos de animaciones")
    print("=" * 60)
    
    # Cambiar al directorio de animaciones
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    videos_generated = []
    
    # Probar animación 2D
    video_2d = test_2d_animation()
    if video_2d:
        videos_generated.append(("2D Simplex", video_2d))
    
    print("-" * 60)
    
    # Probar animación 3D
    video_3d = test_3d_animation()
    if video_3d:
        videos_generated.append(("3D Simplex", video_3d))
    
    print("-" * 60)
    
    # Probar animación Gran M
    video_granm = test_granm_animation()
    if video_granm:
        videos_generated.append(("Gran M", video_granm))
    
    print("=" * 60)
    print("📊 Resumen de videos generados:")
    
    if videos_generated:
        for name, path in videos_generated:
            print(f"✅ {name}: {path}")
        
        print(f"\n🎉 ¡Se generaron {len(videos_generated)} videos exitosamente!")
        
        # Mostrar instrucciones para ver los videos
        print("\n📝 Para ver los videos:")
        print("1. Navega a la carpeta de output/videos")
        print("2. Abre los archivos .mp4 con tu reproductor de video favorito")
        print("3. También puedes encontrar archivos .gif para visualización rápida")
        
    else:
        print("❌ No se pudo generar ningún video")
        print("\n🔧 Posibles soluciones:")
        print("1. Verifica que Manim esté instalado: pip install manim")
        print("2. Verifica que FFmpeg esté instalado")
        print("3. Revisa los logs para más detalles del error")

if __name__ == "__main__":
    main()
