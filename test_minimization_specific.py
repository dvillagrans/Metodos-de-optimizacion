#!/usr/bin/env python3
"""
Test específico para el problema de minimización que mencionas.

Minimizar: Z = 3x1 + 2x2 + 3x3
Sujeto a:
x1 + 4x2 + x3 >= 7  (Restricción 1)
2x1 + x2 + x3 >= 10 (Restricción 2) 
x1, x2, x3 >= 0     (No negatividad)

Respuesta esperada: z = 3.5, x1 = 0, x2 = 1.75, x3 = 0, x4 = 0.25, x5 = 8.25
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
    
    # Para restricciones >=, necesitamos convertir a <=
    # x1 + 4x2 + x3 >= 7  →  -x1 - 4x2 - x3 <= -7
    # 2x1 + x2 + x3 >= 10 →  -2x1 - x2 - x3 <= -10
    A = [
        [-1, -4, -1],  # -x1 - 4x2 - x3 <= -7
        [-2, -1, -1]   # -2x1 - x2 - x3 <= -10
    ]
    b = [-7, -10]
    
    print("Matriz A (convertida a <=):")
    print(np.array(A))
    print("Vector b:")
    print(np.array(b))
    print()
    
    # Como tenemos valores negativos en b, necesitamos usar dos fases    try:
        print("--- Usando Método de Dos Fases ---")
        solution, z_opt, iterations = dosfases_solver(c, A, b, minimize=True, track_iterations=True)
        
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

def test_alternative_formulation():
    """
    Probar formulación alternativa usando variables de holgura negativas
    """
    print("\n=== FORMULACIÓN ALTERNATIVA ===")
    
    # Para x1 + 4x2 + x3 >= 7, agregamos variable de holgura s1
    # x1 + 4x2 + x3 - s1 = 7, donde s1 >= 0
    # Para 2x1 + x2 + x3 >= 10, agregamos variable de holgura s2  
    # 2x1 + x2 + x3 - s2 = 10, donde s2 >= 0
    
    # Minimizar: Z = 3x1 + 2x2 + 3x3 + 0s1 + 0s2
    c = [3, 2, 3, 0, 0]
    
    # Sistema de ecuaciones:
    # x1 + 4x2 + x3 - s1 = 7
    # 2x1 + x2 + x3 - s2 = 10
    A = [
        [1, 4, 1, -1, 0],   # x1 + 4x2 + x3 - s1 = 7
        [2, 1, 1, 0, -1]    # 2x1 + x2 + x3 - s2 = 10
    ]
    b = [7, 10]
    
    print("Matriz A (forma estándar):")
    print(np.array(A))
    print("Vector b:")
    print(np.array(b))
    print()
    
    try:        print("--- Usando Método de Dos Fases (formulación estándar) ---")
        solution, z_opt, iterations = dosfases_solver(c, A, b, minimize=True, track_iterations=True)
        
        print(f"Solución óptima:")
        variables = ['x1', 'x2', 'x3', 's1', 's2']
        for i, val in enumerate(solution):
            if i < len(variables):
                print(f"{variables[i]} = {val:.6f}")
            else:
                print(f"var{i+1} = {val:.6f}")
                
        print(f"Valor óptimo de Z = {z_opt:.6f}")
        
    except Exception as e:
        print(f"Error en formulación alternativa: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_minimization_problem()
    test_alternative_formulation()
