#!/usr/bin/env python3
"""
Debug específico del flujo del solver de dos fases con logs detallados.
"""

import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_dosfases_step_by_step():
    """Debug paso a paso del solver de dos fases con logs"""
    print("=== DEBUG PASO A PASO DEL SOLVER DE DOS FASES ===")
    
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
    print(f"Restricciones >= indices: [0, 1]")
    print(f"minimize = True")
    
    # Simular el procesamiento del solver
    c_np = np.array(c, dtype=float)
    A_np = np.array(A, dtype=float)
    b_np = np.array(b, dtype=float)
    
    # PASO 1: Si es minimización, negar c
    minimize = True
    if minimize:
        c_negated = -c_np
        print(f"\n=== PASO 1: NEGAR OBJETIVO PARA MINIMIZACIÓN ===")
        print(f"c original: {c_np}")
        print(f"c negado: {c_negated}")
    else:
        c_negated = c_np
    
    m, n = A_np.shape
    print(f"\nDimensiones: m={m} restricciones, n={n} variables")
    
    # PASO 2: Procesar restricciones
    eq_constraints = []
    ge_constraints = [0, 1]  # Ambas restricciones son >=
    
    print(f"\n=== PASO 2: PROCESAR RESTRICCIONES ===")
    print(f"eq_constraints: {eq_constraints}")
    print(f"ge_constraints: {ge_constraints}")
    
    # Simular la conversión a forma estándar
    A_std = []
    b_std = []
    artificial_needed = []
    slack_types = []
    
    for i in range(m):
        if i in ge_constraints:
            # Para >=: convertir a = agregando surplus (-) y artificial (+)
            A_std.append(A_np[i].copy())
            b_std.append(b_np[i])
            slack_types.append('surplus')  # -1 en la matriz de slack
            artificial_needed.append(i)
            print(f"Restricción {i+1}: >= -> surplus + artificial")
        elif i in eq_constraints:
            # Para =: agregar artificial directamente
            A_std.append(A_np[i].copy())
            b_std.append(b_np[i])
            slack_types.append('none')
            artificial_needed.append(i)
            print(f"Restricción {i+1}: = -> artificial")
        else:
            # Para <=: agregar slack
            A_std.append(A_np[i].copy())
            b_std.append(b_np[i])
            slack_types.append('slack')  # +1 en la matriz de slack
            print(f"Restricción {i+1}: <= -> slack")
    
    A_std = np.array(A_std)
    b_std = np.array(b_std)
    
    print(f"A_std: {A_std}")
    print(f"b_std: {b_std}")
    print(f"slack_types: {slack_types}")
    print(f"artificial_needed: {artificial_needed}")
    
    # PASO 3: Agregar variables de slack/surplus
    print(f"\n=== PASO 3: AGREGAR VARIABLES DE SLACK/SURPLUS ===")
    slack_matrix = np.zeros((m, m))
    for i in range(m):
        if slack_types[i] == 'slack':
            slack_matrix[i, i] = 1
            print(f"Fila {i+1}: slack variable s{i+1} con coef +1")
        elif slack_types[i] == 'surplus':
            slack_matrix[i, i] = -1
            print(f"Fila {i+1}: surplus variable s{i+1} con coef -1")
        # Para equality constraints, no slack/surplus
    
    print(f"slack_matrix:\n{slack_matrix}")
    
    A_with_slack = np.hstack([A_std, slack_matrix])
    print(f"A_with_slack:\n{A_with_slack}")
    
    # PASO 4: Variables artificiales
    if artificial_needed:
        print(f"\n=== PASO 4: AGREGAR VARIABLES ARTIFICIALES ===")
        print(f"Necesitamos {len(artificial_needed)} variables artificiales para restricciones {artificial_needed}")
        
        num_artificial = len(artificial_needed)
        artificial_matrix = np.zeros((m, num_artificial))
        
        for idx, constraint_idx in enumerate(artificial_needed):
            artificial_matrix[constraint_idx, idx] = 1
            print(f"Variable artificial a{idx+1} para restricción {constraint_idx+1}")
        
        print(f"artificial_matrix:\n{artificial_matrix}")
        
        A_phase1 = np.hstack([A_with_slack, artificial_matrix])
        print(f"A_phase1:\n{A_phase1}")
        
        # Objetivo de Fase 1: minimizar suma de artificiales
        c_phase1 = np.zeros(A_phase1.shape[1])
        for i in range(num_artificial):
            c_phase1[n + m + i] = 1  # Coeficientes para variables artificiales
        
        print(f"c_phase1 (minimizar artificiales): {c_phase1}")
        
        # PROBLEMA DETECTADO: El código está aquí
        print(f"\n🔍 VERIFICANDO CONSTRUCCIÓN DEL TABLEAU DE FASE 1...")
        
        # Simular create_tableau
        print(f"Llamando create_tableau(c_phase1, A_phase1, b_std, maximize=False)")
        print(f"  c_phase1: {c_phase1}")
        print(f"  A_phase1 shape: {A_phase1.shape}")
        print(f"  b_std: {b_std}")
        print(f"  maximize=False (porque Fase 1 siempre minimiza)")
        
        # Crear tableau manualmente para verificar
        tableau1 = create_tableau_debug(c_phase1, A_phase1, b_std, maximize=False)
        print(f"Tableau1 inicial:")
        print_tableau_debug(tableau1)
        
        # Variables básicas iniciales
        basic_vars = []
        for i in range(m):
            if i in artificial_needed:
                art_idx = artificial_needed.index(i)
                basic_vars.append(n + m + art_idx)
            else:
                basic_vars.append(n + i)
        
        print(f"Variables básicas iniciales: {basic_vars}")
        
        # Hacer las variables artificiales básicas en la función objetivo
        print(f"\n=== HACER VARIABLES ARTIFICIALES BÁSICAS EN OBJETIVO ===")
        for i, constraint_idx in enumerate(artificial_needed):
            art_var_col = n + m + i
            print(f"Variable artificial a{i+1} (columna {art_var_col}) en restricción {constraint_idx+1}")
            
            if abs(tableau1[-1, art_var_col]) > 1e-10:
                coef_before = tableau1[-1, art_var_col]
                print(f"  Coeficiente antes: {coef_before}")
                tableau1[-1] -= tableau1[-1, art_var_col] * tableau1[constraint_idx]
                coef_after = tableau1[-1, art_var_col]
                print(f"  Coeficiente después: {coef_after}")
        
        print(f"Tableau1 después de ajustar objetivo:")
        print_tableau_debug(tableau1)
        
        # Aquí debería empezar el simplex de Fase 1
        print(f"\n🔍 AQUÍ ES DONDE PROBABLEMENTE FALLA EL SOLVER...")
        print(f"El tableau está listo para el simplex de Fase 1")
        print(f"Fila objetivo: {tableau1[-1]}")
        
        # Verificar si hay coeficientes negativos (para minimización)
        obj_row = tableau1[-1, :-1]
        negative_indices = np.where(obj_row < -1e-10)[0]
        print(f"Coeficientes negativos en objetivo (columnas): {negative_indices}")
        print(f"Esto significa que podemos mejorar la solución")

def create_tableau_debug(c, A, b, maximize=True):
    """Create simplex tableau with debug."""
    m, n = A.shape
    tableau = np.zeros((m + 1, n + 1))
    
    # Constraint rows
    tableau[:-1, :-1] = A
    tableau[:-1, -1] = b
    
    # Objective row
    if maximize:
        tableau[-1, :-1] = -c  # Negative for maximization
        print(f"  maximize=True -> objetivo = -c = {-c}")
    else:
        tableau[-1, :-1] = c
        print(f"  maximize=False -> objetivo = c = {c}")
    
    return tableau

def print_tableau_debug(tableau):
    """Print tableau in readable format."""
    m, n = tableau.shape
    n = n - 1  # Exclude RHS
    
    for i in range(m):
        if i == m - 1:  # Objective row
            row_str = "  ".join(f"{val:8.3f}" for val in tableau[i])
            print(f"Z | {row_str}")
        else:  # Constraint rows
            row_str = "  ".join(f"{val:8.3f}" for val in tableau[i])
            print(f"{i+1} | {row_str}")

if __name__ == "__main__":
    debug_dosfases_step_by_step()
