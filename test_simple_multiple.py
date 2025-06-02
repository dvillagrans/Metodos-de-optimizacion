#!/usr/bin/env python3
"""
Script simple para probar detección de soluciones múltiples
"""

import numpy as np
import sys
import os

# Agregar el directorio app al path
sys.path.append(os.path.join(os.path.dirname(__file__)))

def test_simple():
    """
    Problema con soluciones múltiples conocidas:
    Maximizar: z = 2x1 + 2x2
    Sujeto a:
    x1 + x2 <= 6
    2x1 + x2 <= 10
    x1, x2 >= 0
    """
    print("Probando detección de soluciones múltiples...")
    print("Problema: Maximizar z = 2x₁ + 2x₂")
    print("Restricciones: x₁ + x₂ ≤ 6, 2x₁ + x₂ ≤ 10")
    
    try:
        from app.solvers.simplex_solver import simplex
        from app.routes import detect_multiple_solutions
        
        c = [2.0, 2.0]
        A = [[1.0, 1.0], [2.0, 1.0]]
        b = [6.0, 10.0]
        minimize = False
          # Resolver
        if True:  # track_iterations=True
            solution, z_opt, tableau_history, pivot_history = simplex(c, A, b, minimize, track_iterations=True)
        else:
            solution, z_opt = simplex(c, A, b, minimize, track_iterations=False)
            tableau_history = None
        
        final_tableau = tableau_history[-1]
        
        print(f"Solución base: x₁={solution[0]:.4f}, x₂={solution[1]:.4f}")
        print(f"Valor óptimo: z={z_opt:.4f}")
        print()
        
        # Mostrar tableau final
        print("Tableau final:")
        print(final_tableau)
        print()
        
        # Analizar costos reducidos
        print("Costos reducidos (fila Z, columnas de variables originales):")
        z_row = final_tableau[0, :len(c)]
        for j, cost in enumerate(z_row):
            print(f"  x{j+1}: {cost:.6f}")
        print()
        
        # Detectar soluciones múltiples
        print("Detectando soluciones múltiples...")
        multi_info = detect_multiple_solutions(final_tableau, len(c), c, minimize)
        
        print(f"¿Tiene soluciones múltiples? {multi_info['has_multiple_solutions']}")
        print(f"Variables candidatas: {multi_info['variables_with_zero_cost']}")
        print(f"Número de alternativas: {len(multi_info['alternative_solutions'])}")
        
        if multi_info['alternative_solutions']:
            print("\nSoluciones alternativas:")
            for i, alt in enumerate(multi_info['alternative_solutions']):
                print(f"  {i+1}. Variable x{alt['entering_var']+1} entra")
                sol_str = ", ".join([f"x{j+1}={val:.4f}" for j, val in enumerate(alt['solution'])])
                print(f"     Solución: {sol_str}")
                z_alt = sum(c[j] * alt['solution'][j] for j in range(len(c)))
                print(f"     Valor: z={z_alt:.4f}")
        
        return multi_info
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_simple()
