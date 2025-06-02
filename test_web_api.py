#!/usr/bin/env python3

import sys
import os
import numpy as np

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.dirname(__file__))

from app.routes import detect_multiple_solutions
from app.solvers.simplex_solver import simplex

def test_web_api():
    """Test the multiple solutions detection through direct function calls"""
    print("=== TEST: Detección de soluciones múltiples ===")
    
    # Test case 1: Equal coefficients
    print("\nCaso 1: Coeficientes iguales (3, 3)")
    c = [3, 3]
    A_matrix = np.array([[1, 2], [2, 1]])
    b_vector = np.array([8, 8])
    minimize = False
    
    try:
        # Solve using simplex
        solution, z_opt, T_hist, pivots = simplex(c, A_matrix, b_vector, minimize, track_iterations=True)
        final_tableau = T_hist[-1]
        
        # Detect multiple solutions
        multi_info = detect_multiple_solutions(final_tableau, len(c), c, minimize)
        
        print(f"Solución: {solution}")
        print(f"Valor óptimo: {z_opt}")
        print(f"¿Soluciones múltiples? {multi_info['has_multiple_solutions']}")
        print(f"Método de detección: {multi_info['detection_method']}")
        
        if multi_info['has_multiple_solutions']:
            alternatives = multi_info['alternative_solutions']
            print(f"Número de alternativas: {len(alternatives)}")
            
            for i, alt in enumerate(alternatives[:3]):  # Show first 3
                sol_str = ", ".join([f"x{j+1}={val:.4f}" for j, val in enumerate(alt['solution'])])
                print(f"  {i+1}. {sol_str}")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    
    # Test case 2: Traditional single solution
    print("\nCaso 2: Solución única")
    c = [1, 2]  # Different coefficients
    A_matrix = np.array([[1, 1], [2, 1]])
    b_vector = np.array([6, 8])
    minimize = False
    
    try:
        # Solve using simplex
        solution, z_opt, T_hist, pivots = simplex(c, A_matrix, b_vector, minimize, track_iterations=True)
        final_tableau = T_hist[-1]
        
        # Detect multiple solutions
        multi_info = detect_multiple_solutions(final_tableau, len(c), c, minimize)
        
        print(f"Solución: {solution}")
        print(f"Valor óptimo: {z_opt}")
        print(f"¿Soluciones múltiples? {multi_info['has_multiple_solutions']}")
        print(f"Método de detección: {multi_info['detection_method']}")
        
        if multi_info['has_multiple_solutions']:
            alternatives = multi_info['alternative_solutions']
            print(f"Número de alternativas: {len(alternatives)}")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_web_api()
