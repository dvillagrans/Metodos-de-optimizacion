#!/usr/bin/env python3
"""
Crear un problema específico donde haya una variable no básica con costo reducido 0
"""

import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

def test_forced_multiple_solutions():
    """
    Problema diseñado para tener variables no básicas con costo reducido 0:
    Maximizar: z = 6x1 + 4x2 + 0x3
    Sujeto a:
    2x1 + x2 + x3 <= 8
    x1 + x2 <= 4
    x1, x2, x3 >= 0
    
    x3 debería ser no básica con costo reducido 0
    """
    print("Problema con x3 diseñada para ser no básica con costo 0:")
    print("Maximizar z = 6x₁ + 4x₂ + 0x₃")
    print("Restricciones: 2x₁ + x₂ + x₃ ≤ 8, x₁ + x₂ ≤ 4")
    
    try:
        from app.solvers.simplex_solver import simplex
        from app.routes import detect_multiple_solutions
        
        c = [6.0, 4.0, 0.0]  # x3 tiene coeficiente 0
        A = [[2.0, 1.0, 1.0], 
             [1.0, 1.0, 0.0]]
        b = [8.0, 4.0]
        minimize = False
        
        solution, z_opt, tableau_history, pivot_history = simplex(c, A, b, minimize, track_iterations=True)
        final_tableau = tableau_history[-1]
        
        print(f"Solución: x₁={solution[0]:.4f}, x₂={solution[1]:.4f}, x₃={solution[2]:.4f}")
        print(f"Valor óptimo: z={z_opt:.4f}")
        print()
        
        print("Tableau final:")
        print(final_tableau)
        print()
        
        # Analizar todas las variables
        print("Análisis detallado:")
        for j in range(len(c)):
            col = final_tableau[1:, j]
            is_basic = (np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0, atol=1e-8))
            cost = final_tableau[0, j]
            print(f"  x{j+1}: básica={is_basic}, costo_reducido={cost:.6f}")
        
        # Detectar soluciones múltiples
        multi_info = detect_multiple_solutions(final_tableau, len(c), c, minimize)
        
        print(f"\n¿Tiene soluciones múltiples? {multi_info['has_multiple_solutions']}")
        print(f"Variables candidatas: {multi_info['variables_with_zero_cost']}")
        
        if multi_info['alternative_solutions']:
            print("\nSoluciones alternativas encontradas:")
            for i, alt in enumerate(multi_info['alternative_solutions']):
                print(f"  {i+1}. Variable x{alt['entering_var']+1} entra")
                sol_str = ", ".join([f"x{j+1}={val:.4f}" for j, val in enumerate(alt['solution'])])
                print(f"     Nueva solución: {sol_str}")
        
        return multi_info
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_degeneracy_example():
    """
    Ejemplo con degeneración que puede llevar a soluciones múltiples:
    Maximizar: z = 2x1 + 3x2
    Sujeto a:
    x1 + 2x2 <= 6
    2x1 + x2 <= 6  
    x1 <= 2
    x2 <= 2
    x1, x2 >= 0
    """
    print("\n" + "="*50)
    print("Ejemplo con restricciones redundantes:")
    print("Maximizar z = 2x₁ + 3x₂")
    
    try:
        from app.solvers.simplex_solver import simplex
        from app.routes import detect_multiple_solutions
        
        c = [2.0, 3.0]
        A = [[1.0, 2.0], 
             [2.0, 1.0],
             [1.0, 0.0],
             [0.0, 1.0]]
        b = [6.0, 6.0, 2.0, 2.0]
        minimize = False
        
        solution, z_opt, tableau_history, pivot_history = simplex(c, A, b, minimize, track_iterations=True)
        final_tableau = tableau_history[-1]
        
        print(f"Solución: x₁={solution[0]:.4f}, x₂={solution[1]:.4f}")
        print(f"Valor óptimo: z={z_opt:.4f}")
        
        # Detectar soluciones múltiples
        multi_info = detect_multiple_solutions(final_tableau, len(c), c, minimize)
        print(f"¿Soluciones múltiples? {multi_info['has_multiple_solutions']}")
        print(f"Variables candidatas: {multi_info['variables_with_zero_cost']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_forced_multiple_solutions()
    test_degeneracy_example()
