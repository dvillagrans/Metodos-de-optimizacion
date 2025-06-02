#!/usr/bin/env python3
"""
Otro ejemplo para probar detección de soluciones múltiples
"""

import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

def test_alternative_example():
    """
    Problema clásico con soluciones múltiples:
    Maximizar: z = x1 + x2
    Sujeto a:
    x1 + 2x2 <= 4
    2x1 + x2 <= 4
    x1, x2 >= 0
    
    Los puntos óptimos son (0,2), (2,0) y todos los puntos en la línea entre ellos
    """
    print("Problema con soluciones múltiples evidentes:")
    print("Maximizar z = x₁ + x₂")
    print("Restricciones: x₁ + 2x₂ ≤ 4, 2x₁ + x₂ ≤ 4")
    
    try:
        from app.solvers.simplex_solver import simplex
        from app.routes import detect_multiple_solutions
        
        c = [1.0, 1.0]  # Coeficientes iguales
        A = [[1.0, 2.0], [2.0, 1.0]]
        b = [4.0, 4.0]
        minimize = False
        
        # Resolver
        solution, z_opt, tableau_history, pivot_history = simplex(c, A, b, minimize, track_iterations=True)
        final_tableau = tableau_history[-1]
        
        print(f"Solución base: x₁={solution[0]:.4f}, x₂={solution[1]:.4f}")
        print(f"Valor óptimo: z={z_opt:.4f}")
        print()
        
        print("Tableau final:")
        print(final_tableau)
        print()
        
        # Analizar cada columna para ver cuáles son básicas
        print("Análisis de variables:")
        for j in range(len(c)):
            col = final_tableau[1:, j]
            is_basic = (np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0, atol=1e-8))
            cost = final_tableau[0, j]
            print(f"  x{j+1}: columna={col}, básica={is_basic}, costo_reducido={cost:.6f}")
        print()
        
        # Analizar variables de holgura también
        print("Variables de holgura:")
        for j in range(len(c), final_tableau.shape[1]-1):
            col = final_tableau[1:, j]
            is_basic = (np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0, atol=1e-8))
            cost = final_tableau[0, j]
            print(f"  s{j-len(c)+1}: columna={col}, básica={is_basic}, costo_reducido={cost:.6f}")
        print()
        
        # Detectar soluciones múltiples
        multi_info = detect_multiple_solutions(final_tableau, len(c), c, minimize)
        
        print(f"¿Tiene soluciones múltiples? {multi_info['has_multiple_solutions']}")
        print(f"Variables candidatas: {multi_info['variables_with_zero_cost']}")
        print(f"Número de alternativas: {len(multi_info['alternative_solutions'])}")
        
        return multi_info
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_textbook_example():
    """
    Ejemplo de libro de texto conocido por tener soluciones múltiples:
    Maximizar: z = 3x1 + 2x2
    Sujeto a:
    x1 + x2 <= 4
    2x1 + x2 <= 6
    x1, x2 >= 0
    """
    print("\n" + "="*50)
    print("Ejemplo de libro de texto:")
    print("Maximizar z = 3x₁ + 2x₂")
    print("Restricciones: x₁ + x₂ ≤ 4, 2x₁ + x₂ ≤ 6")
    
    try:
        from app.solvers.simplex_solver import simplex
        from app.routes import detect_multiple_solutions
        
        c = [3.0, 2.0]
        A = [[1.0, 1.0], [2.0, 1.0]]
        b = [4.0, 6.0]
        minimize = False
        
        solution, z_opt, tableau_history, pivot_history = simplex(c, A, b, minimize, track_iterations=True)
        final_tableau = tableau_history[-1]
        
        print(f"Solución: x₁={solution[0]:.4f}, x₂={solution[1]:.4f}")
        print(f"Valor óptimo: z={z_opt:.4f}")
        
        # Verificar costos reducidos
        print("\nCostos reducidos:")
        z_row = final_tableau[0, :-1]
        for j, cost in enumerate(z_row):
            if j < len(c):
                print(f"  x{j+1}: {cost:.6f}")
            else:
                print(f"  s{j-len(c)+1}: {cost:.6f}")
        
        multi_info = detect_multiple_solutions(final_tableau, len(c), c, minimize)
        print(f"\n¿Soluciones múltiples? {multi_info['has_multiple_solutions']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_alternative_example()
    test_textbook_example()
