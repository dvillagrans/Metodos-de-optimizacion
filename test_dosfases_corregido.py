#!/usr/bin/env python3
"""
Prueba del solver Dos Fases corregido con el problema específico del usuario:
MAX Z = 2x₁ + 3x₂ + 4x₃
Sujeto a:
  x₁ + x₂ + x₃ ≤ 30   (restricción 0)
  2x₁ + x₂ ≥ 40       (restricción 1)  
  3x₂ + 2x₃ ≤ 60      (restricción 2)
  x₁, x₂, x₃ ≥ 0

Este problema es INFACTIBLE debido a que las restricciones 0 y 1 son contradictorias.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.solvers.dosfases_solver import dosfases_solver

def test_specific_problem():
    print("=== PRUEBA DEL SOLVER DOS FASES CORREGIDO ===")
    print("Problema del usuario:")
    print("MAX Z = 2x₁ + 3x₂ + 4x₃")
    print("Sujeto a:")
    print("  x₁ + x₂ + x₃ ≤ 30   (restricción 0)")
    print("  2x₁ + x₂ ≥ 40       (restricción 1)")  
    print("  3x₂ + 2x₃ ≤ 60      (restricción 2)")
    print("  x₁, x₂, x₃ ≥ 0")
    print()
    
    # Definir el problema
    c = [2, 3, 4]  # Función objetivo
    A = [
        [1, 1, 1],   # x₁ + x₂ + x₃ ≤ 30
        [2, 1, 0],   # 2x₁ + x₂ ≥ 40
        [0, 3, 2]    # 3x₂ + 2x₃ ≤ 60
    ]
    b = [30, 40, 60]
    
    # Restricciones: 0 y 2 son ≤, 1 es ≥
    eq_constraints = []  # No hay restricciones de igualdad
    ge_constraints = [1]  # Restricción 1 es ≥
    minimize = False  # Maximizar
    
    print("Definición del problema en el solver:")
    print(f"c = {c}")
    print(f"A = {A}")
    print(f"b = {b}")
    print(f"eq_constraints = {eq_constraints}")
    print(f"ge_constraints = {ge_constraints}")
    print(f"minimize = {minimize}")
    print()    try:
        print("Ejecutando solver de Dos Fases...")
        solution, optimal_value = dosfases_solver(
            c, A, b, 
            eq_constraints=eq_constraints, 
            ge_constraints=ge_constraints,
            minimize=minimize
        )
        
        print("RESULTADO:")
        print(f"Solución: {solution}")
        print(f"Valor óptimo: {optimal_value}")
        print()
        
        if solution is None:
            print("✓ CORRECTO: El solver detectó que el problema es INFACTIBLE")
            print("Esto es el resultado esperado, ya que las restricciones son contradictorias.")
            return
        
        # Verificar si la solución satisface las restricciones originales
        print("VERIFICACIÓN DE RESTRICCIONES:")
        x1, x2, x3 = solution
        
        # Restricción 0: x₁ + x₂ + x₃ ≤ 30
        r0 = x1 + x2 + x3
        print(f"Restricción 0: {x1:.3f} + {x2:.3f} + {x3:.3f} = {r0:.3f} ≤ 30? {r0 <= 30.001}")
        
        # Restricción 1: 2x₁ + x₂ ≥ 40
        r1 = 2*x1 + x2
        print(f"Restricción 1: 2*{x1:.3f} + {x2:.3f} = {r1:.3f} ≥ 40? {r1 >= 39.999}")
        
        # Restricción 2: 3x₂ + 2x₃ ≤ 60
        r2 = 3*x2 + 2*x3
        print(f"Restricción 2: 3*{x2:.3f} + 2*{x3:.3f} = {r2:.3f} ≤ 60? {r2 <= 60.001}")
        
        # No negatividad
        print(f"No negatividad: x₁={x1:.3f}≥0? {x1 >= -0.001}, x₂={x2:.3f}≥0? {x2 >= -0.001}, x₃={x3:.3f}≥0? {x3 >= -0.001}")
        
        if r0 <= 30.001 and r1 >= 39.999 and r2 <= 60.001 and x1 >= -0.001 and x2 >= -0.001 and x3 >= -0.001:
            print("✓ La solución satisface todas las restricciones")
            print(f"  Pero esto indica que el problema SÍ tiene solución factible.")
        else:
            print("✗ La solución NO satisface todas las restricciones")
            print("  Esto indica un error en el solver o la solución devuelta.")
            
    except Exception as e:
        print(f"✗ ERROR INESPERADO: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_specific_problem()
