#!/usr/bin/env python3

import numpy as np
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.dirname(__file__))

from app.routes import detect_multiple_solutions
from app.solvers.simplex_solver import simplex

def debug_detection():
    print("=== DEBUG: Detección de soluciones múltiples ===")
    
    # Test case 1: Equal coefficients case    print("\nCaso 1: Coeficientes iguales")
    c = [3, 3]
    A = np.array([[1, 2], [2, 1]])
    b = np.array([8, 8])
    minimize = False
    
    solution, z_opt, T_hist, pivots = simplex(c, A, b, minimize, track_iterations=True)
    final_tableau = T_hist[-1]  # Last tableau is the final one
    
    print(f"Tableau final:\n{final_tableau}")
    print(f"Coeficientes c: {c}")
    
    # Debug the detection process step by step
    n_orig_vars = len(c)
    z_row = final_tableau[0, :-1]
    tol = 1e-8
    
    print(f"\nz_row: {z_row}")
    print(f"n_orig_vars: {n_orig_vars}")
    
    # Method 1 check
    print("\n--- Método 1: Variables no básicas con costo 0 ---")
    method1_candidates = []
    for j in range(n_orig_vars):
        col = final_tableau[1:, j]
        is_basic = (np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0, atol=tol))
        zero_cost = np.isclose(z_row[j], 0.0, atol=tol)
        
        print(f"  x{j+1}: col={col}, is_basic={is_basic}, zero_cost={zero_cost}")
        
        if not is_basic and zero_cost:
            method1_candidates.append(j)
    
    print(f"Método 1 candidatos: {method1_candidates}")
    
    # Method 2 check
    print("\n--- Método 2: Variables básicas con costo 0 ---")
    all_basic_zero_cost = True
    basic_vars_count = 0
    
    for j in range(n_orig_vars):
        col = final_tableau[1:, j]
        is_basic = (np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0, atol=tol))
        zero_cost = np.isclose(z_row[j], 0.0, atol=tol)
        
        print(f"  x{j+1}: is_basic={is_basic}, zero_cost={zero_cost}")
        
        if is_basic:
            basic_vars_count += 1
            if not zero_cost:
                all_basic_zero_cost = False
    
    print(f"basic_vars_count: {basic_vars_count}")
    print(f"all_basic_zero_cost: {all_basic_zero_cost}")
    
    # Method 3 check
    print("\n--- Método 3: Coeficientes iguales ---")
    c_array = np.array(c)
    print(f"c_array: {c_array}")
    print(f"set(np.abs(c_array)): {set(np.abs(c_array))}")
    print(f"len(set(np.abs(c_array))): {len(set(np.abs(c_array)))}")
    print(f"c_array[0]: {c_array[0]}")
    print(f"Condición método 3: {len(set(np.abs(c_array))) == 1 and c_array[0] != 0}")
    print(f"basic_vars_count >= 2: {basic_vars_count >= 2}")
    
    # Call the actual function
    print("\n--- Resultado de detect_multiple_solutions ---")
    multi_info = detect_multiple_solutions(final_tableau, len(c), c, minimize)
    
    print(f"has_multiple_solutions: {multi_info['has_multiple_solutions']}")
    print(f"detection_method: {multi_info['detection_method']}")
    print(f"variables_with_zero_cost: {multi_info['variables_with_zero_cost']}")
    print(f"Número de alternativas: {len(multi_info['alternative_solutions'])}")

if __name__ == "__main__":
    debug_detection()
