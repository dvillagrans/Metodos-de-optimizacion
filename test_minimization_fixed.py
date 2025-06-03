#!/usr/bin/env python3
"""
Test específico para el problema de minimización que mencionas.

Minimizar: Z = 3x1 + 2x2 + 3x3
Sujeto a:
x1 + 4x2 + x3 >= 7  (Restricción 1)
2x1 + x2 + x3 >= 10 (Restricción 2) 
x1, x2, x3 >= 0     (No negatividad)

Respuesta esperada: z = 3.5, x1 = 0, x2 = 1.75, x3 = 0
"""

import numpy as np
import sys
import os

# Agregar el path para importar los módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from solvers.simplex_solver import simplex, SimplexError
from solvers.dosfases_solver import dosfases_solver

def test_minimization_problem():
    print("=== TEST DE MINIMIZACIÓN ===")
    print("Problema:")
    print("Minimizar: Z = 3x1 + 2x2 + 3x3")
    print("Sujeto a:")
    print("x1 + 4x2 + x3 >= 7")
    print("2x1 + x2 + x3 >= 10")
    print("x1, x2, x3 >= 0")
    print()
      # Coeficientes de la función objetivo
    c = [3, 2, 3]
    
    # Matriz de restricciones (en su forma original)
    A = [
        [1, 4, 1],   # x1 + 4x2 + x3 >= 7
        [2, 1, 1]    # 2x1 + x2 + x3 >= 10
    ]
    b = [7, 10]
    
    # Especificar que ambas restricciones son de tipo >=
    ge_constraints = [0, 1]  # ambas restricciones son >=
    
    print("Matriz A (original):")
    print(np.array(A))
    print("Vector b:")
    print(np.array(b))
    print("Restricciones >=:", ge_constraints)
    print()
    
    # Como tenemos restricciones >=, usamos dos fases
    try:
        print("--- Usando Método de Dos Fases ---")
        solution, z_opt, iterations, pivots = dosfases_solver(
            c, A, b, 
            ge_constraints=ge_constraints, 
            minimize=True, 
            track_iterations=True
        )
        
        print(f"Solución óptima:")
        for i, val in enumerate(solution):
            print(f"x{i+1} = {val:.6f}")
        print(f"Valor óptimo de Z = {z_opt:.6f}")
        print(f"Iteraciones: {len(iterations)}")
        print()
        
        # Verificar restricciones originales
        print("--- Verificación de restricciones ---")
        x1, x2, x3 = solution[:3]
        
        # Restricción 1: x1 + 4x2 + x3 >= 7
        r1_value = x1 + 4*x2 + x3
        print(f"x1 + 4x2 + x3 = {x1:.6f} + 4*{x2:.6f} + {x3:.6f} = {r1_value:.6f}")
        print(f"¿>= 7? {r1_value >= 7 - 1e-6}")
        
        # Restricción 2: 2x1 + x2 + x3 >= 10
        r2_value = 2*x1 + x2 + x3
        print(f"2x1 + x2 + x3 = 2*{x1:.6f} + {x2:.6f} + {x3:.6f} = {r2_value:.6f}")
        print(f"¿>= 10? {r2_value >= 10 - 1e-6}")
        
        # Valor de la función objetivo
        z_check = 3*x1 + 2*x2 + 3*x3
        print(f"Z = 3x1 + 2x2 + 3x3 = 3*{x1:.6f} + 2*{x2:.6f} + 3*{x3:.6f} = {z_check:.6f}")
        
        print()
        print("--- Comparación con resultado esperado ---")
        print("Esperado: z = 3.5, x1 = 0, x2 = 1.75, x3 = 0")
        print(f"Obtenido: z = {z_opt:.6f}, x1 = {x1:.6f}, x2 = {x2:.6f}, x3 = {x3:.6f}")
        
    except Exception as e:
        print(f"Error en dos fases: {e}")
        import traceback
        traceback.print_exc()

def test_manual_solution():
    """
    Verificar manualmente algunas soluciones posibles
    """
    print("\n=== VERIFICACIÓN MANUAL ===")
    
    print("Probando diferentes puntos factibles:")
    
    # Punto 1: x1=0, x2=2.5, x3=0
    x1, x2, x3 = 0, 2.5, 0
    print(f"\nPunto 1: x1={x1}, x2={x2}, x3={x3}")
    r1_value = x1 + 4*x2 + x3
    r2_value = 2*x1 + x2 + x3
    z_value = 3*x1 + 2*x2 + 3*x3
    print(f"Restricción 1: {r1_value} >= 7? {r1_value >= 7}")
    print(f"Restricción 2: {r2_value} >= 10? {r2_value >= 10}")
    print(f"Función objetivo: {z_value}")
    
    # Punto 2: x1=0, x2=0, x3=10
    x1, x2, x3 = 0, 0, 10
    print(f"\nPunto 2: x1={x1}, x2={x2}, x3={x3}")
    r1_value = x1 + 4*x2 + x3
    r2_value = 2*x1 + x2 + x3
    z_value = 3*x1 + 2*x2 + 3*x3
    print(f"Restricción 1: {r1_value} >= 7? {r1_value >= 7}")
    print(f"Restricción 2: {r2_value} >= 10? {r2_value >= 10}")
    print(f"Función objetivo: {z_value}")
    
    # Punto 3: x1=5, x2=0, x3=0
    x1, x2, x3 = 5, 0, 0
    print(f"\nPunto 3: x1={x1}, x2={x2}, x3={x3}")
    r1_value = x1 + 4*x2 + x3
    r2_value = 2*x1 + x2 + x3
    z_value = 3*x1 + 2*x2 + 3*x3
    print(f"Restricción 1: {r1_value} >= 7? {r1_value >= 7}")
    print(f"Restricción 2: {r2_value} >= 10? {r2_value >= 10}")
    print(f"Función objetivo: {z_value}")

if __name__ == "__main__":
    test_minimization_problem()
    test_manual_solution()
