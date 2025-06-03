#!/usr/bin/env python3
"""
Debug detallado del solver de dos fases.
"""

import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.solvers.dosfases_solver import dosfases_solver

def debug_dos_fases_step_by_step():
    """Debug paso a paso del solver de dos fases"""
    print("=== DEBUG DETALLADO DEL SOLVER DE DOS FASES ===")
    
    # Problema:
    # min  3x1 + 2x2 + 3x3 + 0x4
    # s.t. x1 + 4x2 + 3x3 + 0x4 >= 7
    #      2x1 + x2 + 0x3 + x4 >= 10
    #      x1, x2, x3, x4 >= 0
    
    c = [3, 2, 3, 0]
    A = [
        [1, 4, 3, 0],   
        [2, 1, 0, 1]    
    ]
    b = [7, 10]
    ge_constraints = [0, 1]
    
    print(f"Problema original:")
    print(f"c = {c}")
    print(f"A = {A}")  
    print(f"b = {b}")
    print(f"ge_constraints = {ge_constraints}")
    
    # Voy a hacer el debug paso a paso manualmente
    print(f"\n=== PASO 1: CONVERSIÓN A FORMA ESTÁNDAR ===")
    
    # Para >= constraints: x1 + 4x2 + 3x3 + 0x4 >= 7
    # Se convierte en: x1 + 4x2 + 3x3 + 0x4 - s1 + a1 = 7
    # Y: 2x1 + x2 + 0x3 + x4 >= 10
    # Se convierte en: 2x1 + x2 + 0x3 + x4 - s2 + a2 = 10
    
    A_std = np.array(A, dtype=float)
    b_std = np.array(b, dtype=float)
    
    print(f"A_std después de conversión: {A_std}")
    print(f"b_std después de conversión: {b_std}")
    
    # Agregar variables de holgura/surplus
    # Para >= necesitamos surplus (coef -1) y artificiales
    m, n = A_std.shape
    print(f"m={m}, n={n}")
    
    # Matriz con surplus variables (-1 para >=)
    slack_matrix = np.array([
        [-1, 0],  # -s1 para primera restricción >=
        [0, -1]   # -s2 para segunda restricción >=
    ])
    
    # Matriz con variables artificiales (+1)
    artificial_matrix = np.array([
        [1, 0],   # +a1 para primera restricción
        [0, 1]    # +a2 para segunda restricción  
    ])
    
    A_phase1 = np.hstack([A_std, slack_matrix, artificial_matrix])
    print(f"A_phase1 completa: {A_phase1.shape}")
    print(f"A_phase1 = ")
    print(A_phase1)
    
    print(f"\n=== PASO 2: SETUP FASE 1 ===")
    
    # Fase 1 objetivo: min a1 + a2
    c_phase1 = np.zeros(A_phase1.shape[1])
    c_phase1[n + m:] = 1  # Coeficientes 1 para variables artificiales
    print(f"c_phase1 = {c_phase1}")
    
    # Crear tableau inicial
    tableau1 = np.zeros((m + 1, A_phase1.shape[1] + 1))
    tableau1[:m, :-1] = A_phase1
    tableau1[:m, -1] = b_std
    tableau1[-1, :-1] = -c_phase1  # Negar para maximización
    
    print(f"Tableau inicial Fase 1:")
    print(tableau1)
    
    # Variables básicas iniciales son las artificiales
    basic_vars = [n + m, n + m + 1]  # a1, a2
    print(f"Variables básicas iniciales: {basic_vars}")
    
    # Eliminar artificiales de la función objetivo
    for i in range(m):
        art_col = n + m + i
        if abs(tableau1[-1, art_col]) > 1e-10:
            tableau1[-1] -= tableau1[-1, art_col] * tableau1[i]
    
    print(f"Tableau después de eliminar artificiales:")
    print(tableau1)
    
    print(f"\n=== INTENTANDO CON EL SOLVER REAL ===")
    
    try:
        resultado = dosfases_solver(
            c, A, b, 
            eq_constraints=[],
            ge_constraints=ge_constraints,
            minimize=True,
            track_iterations=True
        )
        
        if resultado is None:
            print("❌ Resultado es None")
        else:
            solution, optimal_value, tableau_history, pivot_history = resultado
            print(f"Solución: {solution}")
            print(f"Valor óptimo: {optimal_value}")
            print(f"Número de tableaux: {len(tableau_history) if tableau_history else 0}")
            
            if tableau_history:
                print(f"\nPrimer tableau:")
                print(tableau_history[0])
                print(f"\nÚltimo tableau:")
                print(tableau_history[-1])
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_dos_fases_step_by_step()
