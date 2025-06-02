import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.solvers.dosfases_solver import dosfases_solver

def debug_dosfases_detailed():
    """
    Debug detallado del problema con el método Dos Fases
    """
    print("🔍 DEBUG DETALLADO - MÉTODO DOS FASES")
    print("=" * 60)
    
    # Problema que sabemos que es infactible
    c = [2, 3, 4]  # MAX Z = 2x₁ + 3x₂ + 4x₃
    A = [
        [1, 1, 1],   # x₁ + x₂ + x₃ ≤ 30
        [2, 1, 0],   # 2x₁ + x₂ ≥ 40  <- ESTA ES EL PROBLEMA
        [0, 3, 2]    # 3x₂ + 2x₃ ≤ 60
    ]
    b = [30, 40, 60]
    
    print("Problema original:")
    print("  MAX Z = 2x₁ + 3x₂ + 4x₃")
    print("  s.a.  x₁ + x₂ + x₃ ≤ 30")
    print("       2x₁ + x₂     ≥ 40  ← Restricción problemática")
    print("       3x₂ + 2x₃    ≤ 60")
    print("       x₁,x₂,x₃ ≥ 0")
    print()
    
    print("🚨 PROBLEMA IDENTIFICADO:")
    print("  El solver actual NO maneja restricciones ≥ correctamente")
    print("  Está tratando 2x₁ + x₂ ≥ 40 como si fuera 2x₁ + x₂ ≤ 40")
    print()
    
    # Intentar ejecutar el solver y capturar el resultado
    try:
        result = dosfases_solver(c, A, b, eq_constraints=[], track_iterations=True)
        solution, optimal_value, tableau_history, pivot_history = result
        
        print("❌ RESULTADO INCORRECTO DEL SOLVER:")
        print(f"  Solución: [{solution[0]:.3f}, {solution[1]:.3f}, {solution[2]:.3f}]")
        print(f"  Valor óptimo: {optimal_value:.3f}")
        print()
        
        # Verificar manualmente la solución
        x1, x2, x3 = solution
        constraint1 = x1 + x2 + x3      # ≤ 30
        constraint2 = 2*x1 + x2         # ≥ 40
        constraint3 = 3*x2 + 2*x3       # ≤ 60
        
        print("📊 VERIFICACIÓN MANUAL:")
        print(f"  Restricción 1: {constraint1:.3f} ≤ 30 {'✓' if constraint1 <= 30.001 else '✗'}")
        print(f"  Restricción 2: {constraint2:.3f} ≥ 40 {'✓' if constraint2 >= 39.999 else '✗'}")
        print(f"  Restricción 3: {constraint3:.3f} ≤ 60 {'✓' if constraint3 <= 60.001 else '✗'}")
        print()
        
        if constraint2 < 39.999:
            print("🚨 CONFIRMADO: El solver está violando la restricción ≥")
            print("   Esto demuestra que NO está manejando restricciones ≥ correctamente")
        
        print("📋 ANÁLISIS DEL TABLEAU FINAL:")
        if tableau_history:
            final_tableau = tableau_history[-1]
            print(f"  Tableau final shape: {final_tableau.shape}")
            print(f"  Última fila de costos: {final_tableau[0, :]}")
            print(f"  Valores RHS: {final_tableau[1:, -1]}")
        
    except Exception as e:
        print(f"❌ Error en el solver: {str(e)}")
    
    print()
    print("🔧 SOLUCIÓN REQUERIDA:")
    print("  1. Modificar el solver para manejar restricciones ≥")
    print("  2. Convertir 2x₁ + x₂ ≥ 40 a -2x₁ - x₂ ≤ -40")
    print("  3. Agregar variables artificiales para restricciones ≥")
    print("  4. Manejar correctamente los valores negativos en b")

if __name__ == "__main__":
    debug_dosfases_detailed()
