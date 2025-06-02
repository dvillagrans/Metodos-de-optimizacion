#!/usr/bin/env python3
"""
Prueba adicional del solver Dos Fases corregido con un problema factible que tiene restricciones ≥.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.solvers.dosfases_solver import dosfases_solver, InfeasibleError

def test_feasible_ge_problem():
    print("=== PRUEBA CON PROBLEMA FACTIBLE CON RESTRICCIONES ≥ ===")
    print("Problema:")
    print("MAX Z = x₁ + x₂")
    print("Sujeto a:")
    print("  x₁ + x₂ ≤ 6    (restricción 0)")
    print("  x₁ ≥ 2         (restricción 1)")  
    print("  x₂ ≥ 1         (restricción 2)")
    print("  x₁, x₂ ≥ 0")
    print()
    
    # Definir el problema
    c = [1, 1]  # MAX Z = x₁ + x₂
    A = [
        [1, 1],   # x₁ + x₂ ≤ 6
        [1, 0],   # x₁ ≥ 2
        [0, 1]    # x₂ ≥ 1
    ]
    b = [6, 2, 1]
    
    # Restricciones: 0 es ≤, 1 y 2 son ≥
    eq_constraints = []
    ge_constraints = [1, 2]
    minimize = False
    
    print("Definición en el solver:")
    print(f"c = {c}")
    print(f"A = {A}")
    print(f"b = {b}")
    print(f"eq_constraints = {eq_constraints}")
    print(f"ge_constraints = {ge_constraints}")
    print()
    
    try:
        print("Ejecutando solver...")
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
        
        # Verificar restricciones
        print("VERIFICACIÓN DE RESTRICCIONES:")
        x1, x2 = solution
        
        # Restricción 0: x₁ + x₂ ≤ 6
        r0 = x1 + x2
        print(f"Restricción 0: {x1:.3f} + {x2:.3f} = {r0:.3f} ≤ 6? {r0 <= 6.001}")
        
        # Restricción 1: x₁ ≥ 2
        print(f"Restricción 1: {x1:.3f} ≥ 2? {x1 >= 1.999}")
        
        # Restricción 2: x₂ ≥ 1
        print(f"Restricción 2: {x2:.3f} ≥ 1? {x2 >= 0.999}")
        
        # No negatividad
        print(f"No negatividad: x₁={x1:.3f}≥0? {x1 >= -0.001}, x₂={x2:.3f}≥0? {x2 >= -0.001}")
        
        # La solución óptima esperada es [5, 1] con Z = 6
        print(f"Solución esperada: [5, 1] con Z = 6")
        print(f"¿Es la solución óptima? x₁+x₂ = {x1+x2:.3f}, esperado = 6")
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

def test_another_ge_problem():
    print("\n=== PRUEBA CON OTRO PROBLEMA CON ≥ ===")
    print("Problema:")
    print("MAX Z = 3x₁ + 2x₂")
    print("Sujeto a:")
    print("  x₁ + x₂ ≤ 10   (restricción 0)")
    print("  2x₁ + x₂ ≥ 8   (restricción 1)")  
    print("  x₁, x₂ ≥ 0")
    print()
    
    c = [3, 2]
    A = [
        [1, 1],   # x₁ + x₂ ≤ 10
        [2, 1]    # 2x₁ + x₂ ≥ 8
    ]
    b = [10, 8]
    
    eq_constraints = []
    ge_constraints = [1]
    minimize = False
    
    try:
        solution, optimal_value = dosfases_solver(
            c, A, b, 
            eq_constraints=eq_constraints, 
            ge_constraints=ge_constraints,
            minimize=minimize
        )
        
        print(f"Solución: {solution}")
        print(f"Valor óptimo: {optimal_value}")
        
        # Verificar
        x1, x2 = solution
        r0 = x1 + x2
        r1 = 2*x1 + x2
        
        print(f"Verificación:")
        print(f"  x₁ + x₂ = {r0:.3f} ≤ 10? {r0 <= 10.001}")
        print(f"  2x₁ + x₂ = {r1:.3f} ≥ 8? {r1 >= 7.999}")
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_feasible_ge_problem()
    test_another_ge_problem()
