#!/usr/bin/env python3
"""
Ejemplo conocido que definitivamente tiene soluciones múltiples
"""

import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

def test_true_multiple_solutions():
    """
    Problema clásico de programación lineal con soluciones múltiples:
    Maximizar: z = 3x1 + 3x2
    Sujeto a:
    x1 + 2x2 <= 8  
    2x1 + x2 <= 8
    x1, x2 >= 0
    
    Este problema tiene múltiples soluciones óptimas en los puntos (0,4), (4,0) 
    y todos los puntos en la línea entre ellos.
    """
    print("Ejemplo clásico con soluciones múltiples:")
    print("Maximizar z = 3x₁ + 3x₂")
    print("Restricciones: x₁ + 2x₂ ≤ 8, 2x₁ + x₂ ≤ 8")
    
    try:
        from app.solvers.simplex_solver import simplex
        from app.routes import detect_multiple_solutions
        
        c = [3.0, 3.0]  # Coeficientes idénticos = posibles soluciones múltiples
        A = [[1.0, 2.0], 
             [2.0, 1.0]]
        b = [8.0, 8.0]
        minimize = False
        
        solution, z_opt, tableau_history, pivot_history = simplex(c, A, b, minimize, track_iterations=True)
        final_tableau = tableau_history[-1]
        
        print(f"Solución encontrada: x₁={solution[0]:.4f}, x₂={solution[1]:.4f}")
        print(f"Valor óptimo: z={z_opt:.4f}")
        print()
        
        print("Tableau final:")
        print(final_tableau)
        print()
        
        # Mostrar información detallada de cada variable
        print("Estado de las variables:")
        n_vars = len(c)
        tol = 1e-8
        
        for j in range(final_tableau.shape[1] - 1):  # Todas las columnas excepto RHS
            col = final_tableau[1:, j]
            is_basic = (np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0, atol=tol))
            cost = final_tableau[0, j]
            
            if j < n_vars:
                var_name = f"x{j+1}"
            else:
                var_name = f"s{j-n_vars+1}"
            
            print(f"  {var_name}: básica={is_basic}, costo_reducido={cost:.6f}")
        print()
        
        # Verificar manualmente la condición de soluciones múltiples
        print("Verificación manual de soluciones múltiples:")
        has_multiple = False
        candidates = []
        
        z_row = final_tableau[0, :-1]
        for j in range(n_vars):
            col = final_tableau[1:, j]
            is_basic = (np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0, atol=tol))
            zero_cost = np.isclose(z_row[j], 0.0, atol=tol)
            
            print(f"  x{j+1}: básica={is_basic}, costo_cero={zero_cost}")
            
            if not is_basic and zero_cost:
                has_multiple = True
                candidates.append(j)
        
        print(f"Manual: ¿Soluciones múltiples? {has_multiple}")
        print(f"Manual: Variables candidatas: {candidates}")
        print()
        
        # Usar el detector automático
        multi_info = detect_multiple_solutions(final_tableau, len(c), c, minimize)
        
        print(f"Detector automático:")
        print(f"¿Tiene soluciones múltiples? {multi_info['has_multiple_solutions']}")
        print(f"Variables candidatas: {multi_info['variables_with_zero_cost']}")
        print(f"Número de alternativas: {len(multi_info['alternative_solutions'])}")
        
        if multi_info['alternative_solutions']:
            print("\nSoluciones alternativas:")
            for i, alt in enumerate(multi_info['alternative_solutions']):
                print(f"  {i+1}. Variable x{alt['entering_var']+1} entra")
                sol_str = ", ".join([f"x{j+1}={val:.4f}" for j, val in enumerate(alt['solution'])])
                print(f"     Solución: {sol_str}")
                
                # Verificar que el valor objetivo sea igual
                z_alt = sum(c[j] * alt['solution'][j] for j in range(len(c)))
                print(f"     Valor: z={z_alt:.4f} (debería ser {z_opt:.4f})")
        
        return multi_info
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_simple_2var():
    """
    Ejemplo muy simple de 2 variables donde forzamos soluciones múltiples
    """
    print("\n" + "="*60)
    print("Ejemplo simple forzando soluciones múltiples:")
    print("Maximizar z = 1x₁ + 1x₂") 
    print("Restricciones: x₁ + x₂ ≤ 2")
    
    try:
        from app.solvers.simplex_solver import simplex
        from app.routes import detect_multiple_solutions
        
        c = [1.0, 1.0]  # Exactamente iguales
        A = [[1.0, 1.0]]  # Una sola restricción
        b = [2.0]
        minimize = False
        
        solution, z_opt, tableau_history, pivot_history = simplex(c, A, b, minimize, track_iterations=True)
        final_tableau = tableau_history[-1]
        
        print(f"Solución: x₁={solution[0]:.4f}, x₂={solution[1]:.4f}")
        print(f"Valor óptimo: z={z_opt:.4f}")
        print("\nTableau final:")
        print(final_tableau)
        
        multi_info = detect_multiple_solutions(final_tableau, len(c), c, minimize)
        print(f"\n¿Soluciones múltiples? {multi_info['has_multiple_solutions']}")
        print(f"Variables candidatas: {multi_info['variables_with_zero_cost']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_true_multiple_solutions()
    test_simple_2var()
