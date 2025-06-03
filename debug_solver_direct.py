#!/usr/bin/env python3
"""
Debug directo del solver de dos fases para encontrar el punto exacto de falla.
"""

import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.solvers.dosfases_solver import dosfases_solver

def debug_solver_direct():
    """Debug directo del solver con logs"""
    print("=== DEBUG DIRECTO DEL SOLVER DE DOS FASES ===")
    
    # Problema:
    # min  3x1 + 2x2 + 3x3 + 0x4
    # s.t. x1 + 4x2 + 3x3 + 0x4 >= 7
    #      2x1 + x2 + 0x3 + x4 >= 10
    #      x1, x2, x3, x4 >= 0
    
    c = [3, 2, 3, 0]
    A = [
        [1, 4, 3, 0],   # x1 + 4x2 + 3x3 + 0x4 >= 7
        [2, 1, 0, 1]    # 2x1 + x2 + 0x3 + x4 >= 10
    ]
    b = [7, 10]
    
    print(f"Problema original:")
    print(f"c = {c}")
    print(f"A = {A}")
    print(f"b = {b}")
    print(f"ge_constraints = [0, 1]")
    print(f"minimize = True")
    
    try:
        print(f"\n=== LLAMANDO AL SOLVER CON TRACKING ===")
        resultado = dosfases_solver(
            c, A, b, 
            eq_constraints=[],
            ge_constraints=[0, 1],
            minimize=True,
            track_iterations=True
        )
        
        print(f"Tipo de resultado: {type(resultado)}")
        print(f"Longitud del resultado: {len(resultado) if resultado else 'None'}")
        
        if resultado and len(resultado) >= 4:
            solution, optimal_value, tableau_history, pivot_history = resultado
            
            print(f"\n=== RESULTADO ===")
            print(f"Solución: {solution}")
            print(f"Valor óptimo: {optimal_value}")
            print(f"Número de tableaux en historial: {len(tableau_history) if tableau_history else 0}")
            print(f"Número de pivots en historial: {len(pivot_history) if pivot_history else 0}")
            
            if tableau_history:
                print(f"\n=== ANÁLISIS DE TABLEAUX ===")
                for i, tableau in enumerate(tableau_history):
                    print(f"\nTableau {i+1}:")
                    print_tableau_debug(tableau)
                    
                    if i < len(pivot_history):
                        pivot_row, pivot_col = pivot_history[i]
                        print(f"  Pivot: fila {pivot_row+1}, columna {pivot_col+1}")
            
            if solution is None:
                print(f"\n❌ SOLVER DEVOLVIÓ SOLUCIÓN NONE")
                print(f"Valor óptimo: {optimal_value}")
                
                # Analizar el último tableau
                if tableau_history:
                    last_tableau = tableau_history[-1]
                    print(f"\n🔍 ANÁLISIS DEL ÚLTIMO TABLEAU:")
                    print_tableau_debug(last_tableau)
                    
                    # Verificar condiciones de optimalidad
                    obj_row = last_tableau[-1, :-1]
                    min_coef = np.min(obj_row)
                    print(f"Coeficiente mínimo en fila objetivo: {min_coef}")
                    
                    if min_coef >= -1e-10:
                        print(f"✓ Condición de optimalidad cumplida")
                        
                        # Extraer solución manualmente
                        print(f"\n🔧 EXTRAYENDO SOLUCIÓN MANUALMENTE...")
                        n_cols = last_tableau.shape[1] - 1
                        
                        # Buscar variables básicas
                        solution_manual = np.zeros(n_cols)
                        basic_vars_found = []
                        
                        for col in range(n_cols):
                            # Buscar si es variable básica
                            column = last_tableau[:-1, col]  # Excluir fila objetivo
                            ones_count = np.sum(np.abs(column - 1.0) < 1e-8)
                            zeros_count = np.sum(np.abs(column) < 1e-8)
                            
                            if ones_count == 1 and zeros_count == len(column) - 1:
                                # Es variable básica
                                basic_row = np.where(np.abs(column - 1.0) < 1e-8)[0][0]
                                value = last_tableau[basic_row, -1]
                                solution_manual[col] = value
                                basic_vars_found.append((col, basic_row, value))
                                
                        print(f"Variables básicas encontradas: {basic_vars_found}")
                        print(f"Solución manual: {solution_manual}")
                        
                        # Valor objetivo
                        obj_value = last_tableau[-1, -1]
                        print(f"Valor objetivo del tableau: {obj_value}")
                    else:
                        print(f"❌ Condición de optimalidad NO cumplida")
                        negative_indices = np.where(obj_row < -1e-10)[0]
                        print(f"Coeficientes negativos en columnas: {negative_indices}")
                
        else:
            print(f"❌ RESULTADO INVÁLIDO: {resultado}")
    
    except Exception as e:
        print(f"❌ ERROR EN EL SOLVER: {e}")
        import traceback
        traceback.print_exc()

def print_tableau_debug(tableau):
    """Print tableau in readable format."""
    if tableau is None:
        print("  Tableau is None")
        return
        
    m, n = tableau.shape
    n = n - 1  # Exclude RHS
    
    for i in range(m):
        if i == m - 1:  # Objective row
            row_str = "  ".join(f"{val:8.3f}" for val in tableau[i])
            print(f"  Z | {row_str}")
        else:  # Constraint rows
            row_str = "  ".join(f"{val:8.3f}" for val in tableau[i])
            print(f"  {i+1} | {row_str}")

if __name__ == "__main__":
    debug_solver_direct()
