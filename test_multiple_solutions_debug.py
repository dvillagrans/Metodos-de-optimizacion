#!/usr/bin/env python3
"""
Script para debug de detección de soluciones múltiples
"""

import numpy as np
import sys
import os

# Agregar el directorio app al path para importar los módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.solvers.simplex_solver import simplex
from app.routes import detect_multiple_solutions, generate_alternative_solutions

def test_multiple_solutions():
    """
    Problema clásico con soluciones múltiples:
    Maximizar: z = 2x1 + 2x2
    Sujeto a:
    x1 + x2 <= 6
    2x1 + x2 <= 10  
    x1, x2 >= 0
    
    Ambos puntos (4,2) y (2,4) dan z=12
    """
    print("=" * 60)
    print("PRUEBA DE DETECCIÓN DE SOLUCIONES MÚLTIPLES")
    print("=" * 60)
    
    # Definir el problema
    c = [2.0, 2.0]  # Coeficientes iguales → múltiples soluciones
    A = [[1.0, 1.0], 
         [2.0, 1.0]]
    b = [6.0, 10.0]
    minimize = False
    
    print(f"Función objetivo: {'Minimizar' if minimize else 'Maximizar'} z = {c[0]}x₁ + {c[1]}x₂")
    print("Restricciones:")
    for i, (row, rhs) in enumerate(zip(A, b)):
        constraint = " + ".join([f"{coef}x{j+1}" for j, coef in enumerate(row)])
        print(f"  {constraint} <= {rhs}")
    print()
    
    try:        # Resolver con Simplex
        print("1. Resolviendo con Simplex...")
        result = simplex(c, A, b, minimize, track_iterations=True)
        
        solution = result['solution']
        z_opt = result['optimal_value'] 
        tableau_history = result['tableau_history']
        
        print(f"Solución encontrada: x₁ = {solution[0]:.4f}, x₂ = {solution[1]:.4f}")
        print(f"Valor óptimo: z = {z_opt:.4f}")
        print()
        
        # Mostrar tableau final
        print("2. Tableau final:")
        final_tableau = tableau_history[-1]
        print(final_tableau)
        print()
        
        # Analizar la fila Z para detectar costos reducidos cero
        print("3. Análisis de costos reducidos (fila Z):")
        z_row = final_tableau[0, :-1]
        for j, cost in enumerate(z_row):
            print(f"  Variable x{j+1}: costo reducido = {cost:.6f}")
        print()
        
        # Detectar soluciones múltiples
        print("4. Detectando soluciones múltiples...")
        multi_info = detect_multiple_solutions(final_tableau, len(c), c, minimize)
        
        print(f"¿Tiene soluciones múltiples? {multi_info['has_multiple_solutions']}")
        print(f"Variables candidatas: {multi_info['variables_with_zero_cost']}")
        print(f"Número de soluciones alternativas: {len(multi_info['alternative_solutions'])}")
        print()
        
        # Mostrar soluciones alternativas
        if multi_info['alternative_solutions']:
            print("5. Soluciones alternativas encontradas:")
            for i, alt_sol in enumerate(multi_info['alternative_solutions']):
                print(f"  Solución {i+1}:")
                print(f"    Variable que entra: x{alt_sol['entering_var']+1}")
                print(f"    Fila de pivote: {alt_sol['pivot_row']}")
                solution_str = ", ".join([f"x{j+1} = {val:.4f}" for j, val in enumerate(alt_sol['solution'])])
                print(f"    Solución: {solution_str}")
                
                # Verificar que el valor objetivo sea el mismo
                z_alt = sum(c[j] * alt_sol['solution'][j] for j in range(len(c)))
                if minimize:
                    z_alt = -z_alt
                print(f"    Valor objetivo: z = {z_alt:.4f}")
                print()
        
        # Prueba manual adicional
        print("6. Verificación manual de costos reducidos cero...")
        tolerance = 1e-8
        zero_cost_vars = []
        for j in range(len(c)):
            col = final_tableau[1:, j]
            is_basic = (np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0, atol=tolerance))
            zero_cost = np.isclose(z_row[j], 0.0, atol=tolerance)
            
            print(f"  x{j+1}: es_básica={is_basic}, costo_cero={zero_cost}")
            if not is_basic and zero_cost:
                zero_cost_vars.append(j)
        
        print(f"Variables no básicas con costo reducido cero: {zero_cost_vars}")
        
        return multi_info
        
    except Exception as e:
        print(f"Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_another_example():
    """
    Otro ejemplo con soluciones múltiples más evidentes
    Maximizar: z = 3x1 + 3x2
    Sujeto a:
    x1 + 2x2 <= 8
    2x1 + x2 <= 8
    x1, x2 >= 0
    """
    print("\n" + "=" * 60)
    print("SEGUNDA PRUEBA - OTRO EJEMPLO")
    print("=" * 60)
    
    c = [3.0, 3.0]  # Coeficientes iguales
    A = [[1.0, 2.0], 
         [2.0, 1.0]]
    b = [8.0, 8.0]
    minimize = False
    
    print(f"Función objetivo: Maximizar z = {c[0]}x₁ + {c[1]}x₂")
    print("Restricciones:")    for i, (row, rhs) in enumerate(zip(A, b)):
        constraint = " + ".join([f"{coef}x{j+1}" for j, coef in enumerate(row)])
        print(f"  {constraint} <= {rhs}")
    print()
    
    try:
        result = simplex(c, A, b, minimize, track_iterations=True)
        solution = result['solution']
        z_opt = result['optimal_value'] 
        tableau_history = result['tableau_history']
        final_tableau = tableau_history[-1]
        
        multi_info = detect_multiple_solutions(final_tableau, len(c), c, minimize)
        
        print(f"Solución: x₁ = {solution[0]:.4f}, x₂ = {solution[1]:.4f}")
        print(f"Valor óptimo: z = {z_opt:.4f}")
        print(f"¿Soluciones múltiples? {multi_info['has_multiple_solutions']}")
        print(f"Variables candidatas: {multi_info['variables_with_zero_cost']}")
        print(f"Alternativas: {len(multi_info['alternative_solutions'])}")
        
        return multi_info
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_multiple_solutions()
    test_another_example()
