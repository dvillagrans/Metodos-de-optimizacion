#!/usr/bin/env python3

import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.solvers.dosfases_solver import dosfases_solver

def debug_two_phase():
    """Debug the two-phase method step by step"""
    print("=== DEBUG PASO A PASO DEL MÉTODO DE DOS FASES ===")
    
    # Problema: min 3x1 + 2x2 + 3x3
    # s.t. x1 + 4x2 + x3 >= 7
    #      2x1 + x2 + x3 >= 10
    #      x1, x2, x3 >= 0
    
    c = np.array([3, 2, 3])
    A = np.array([
        [1, 4, 1],
        [2, 1, 1]
    ])
    b = np.array([7, 10])
    
    print("Problema original:")
    print(f"c = {c}")
    print(f"A = \n{A}")
    print(f"b = {b}")
    print(f"Restricciones >= para filas: [0, 1]")
    
    try:
        # Probar el solver con tracking
        result = dosfases_solver(
            c=c, 
            A=A, 
            b=b, 
            ge_constraints=[0, 1], 
            minimize=True, 
            track_iterations=True
        )
        
        if result is None:
            print("❌ Resultado es None")
            return
            
        if len(result) == 4:
            solution, optimal_value, tableau_history, pivot_history = result
        elif len(result) == 2:
            solution, optimal_value = result
            tableau_history = None
            pivot_history = None
        else:
            print(f"❌ Resultado inesperado: {result}")
            return
            
        print(f"\n=== RESULTADO ===")
        if solution is not None:
            print(f"Solución: {solution}")
            print(f"Valor óptimo: {optimal_value}")
            
            # Verificar restricciones
            print(f"\n=== VERIFICACIÓN ===")
            print(f"x1 + 4*x2 + x3 >= 7: {solution[0] + 4*solution[1] + solution[2]} >= 7")
            print(f"2*x1 + x2 + x3 >= 10: {2*solution[0] + solution[1] + solution[2]} >= 10")
            print(f"Función objetivo: {3*solution[0] + 2*solution[1] + 3*solution[2]}")
        else:
            print("❌ Solución es None - problema infactible")
            
        if tableau_history:
            print(f"\n=== HISTORIAL DE TABLEROS ({len(tableau_history)} tableros) ===")
            for i, tableau in enumerate(tableau_history):
                print(f"\nTablero {i+1}:")
                print(tableau)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_two_phase()
