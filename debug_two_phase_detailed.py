#!/usr/bin/env python3
"""
Debug detallado del solver de dos fases para encontrar el problema específico.
"""

import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_two_phase_solver():
    """Debug paso a paso del solver de dos fases"""
    print("=== DEBUG DETALLADO DEL SOLVER DE DOS FASES ===")
    
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
    print(f"Restricciones >= ambas (indices 0,1)")
    print(f"minimize = True")
    
    # Ahora vamos a simular manualmente lo que debería hacer el solver
    
    # Paso 1: Convertir >= a <= multiplicando por -1
    print(f"\n=== PASO 1: CONVERTIR >= A <= ===")
    
    # Para restricciones >=, multiplicamos por -1
    A_converted = []
    b_converted = []
    
    for i, (row, rhs) in enumerate(zip(A, b)):
        # Como ambas son >=, multiplicamos por -1
        new_row = [-x for x in row]
        new_rhs = -rhs
        A_converted.append(new_row)
        b_converted.append(new_rhs)
        print(f"Restricción {i+1}: {row} >= {rhs} -> {new_row} <= {new_rhs}")
    
    print(f"A después de conversión: {A_converted}")
    print(f"b después de conversión: {b_converted}")
    
    # Paso 2: Agregar variables de holgura (se vuelven negativas por la conversión)
    print(f"\n=== PASO 2: AGREGAR VARIABLES DE HOLGURA ===")
    
    # Las variables de holgura para <= son normales
    # Pero como convertimos >= a <=, las holguras serán negativas
    # Por eso necesitamos variables artificiales
    
    n_vars = len(c)  # 4 variables originales
    n_constraints = len(A_converted)  # 2 restricciones
    
    # Agregar variables de holgura
    A_with_slack = []
    for i, row in enumerate(A_converted):
        new_row = row.copy()
        # Agregar variables de holgura
        for j in range(n_constraints):
            if i == j:
                new_row.append(1)  # Variable de holgura para esta restricción
            else:
                new_row.append(0)
        A_with_slack.append(new_row)
    
    print(f"A con variables de holgura:")
    for i, row in enumerate(A_with_slack):
        print(f"  Restricción {i+1}: {row}")
    
    # Paso 3: Como b < 0, necesitamos variables artificiales
    print(f"\n=== PASO 3: ANÁLISIS DE FACTIBILIDAD BÁSICA ===")
    print(f"b_converted = {b_converted}")
    print("Como todos los valores de b son negativos, no podemos usar las variables de holgura como base inicial")
    print("Necesitamos agregar variables artificiales")
    
    # Agregar variables artificiales
    A_with_artificial = []
    for i, row in enumerate(A_with_slack):
        new_row = row.copy()
        # Agregar variables artificiales
        for j in range(n_constraints):
            if i == j:
                new_row.append(1)  # Variable artificial para esta restricción
            else:
                new_row.append(0)
        A_with_artificial.append(new_row)
    
    print(f"\nA con variables de holgura y artificiales:")
    for i, row in enumerate(A_with_artificial):
        print(f"  Restricción {i+1}: {row}")
    
    # Fase 1: Minimizar suma de variables artificiales
    print(f"\n=== FASE 1: MINIMIZAR VARIABLES ARTIFICIALES ===")
    
    # Función objetivo de Fase 1: minimizar x5 + x6 (variables artificiales)
    c_phase1 = [0] * (n_vars + n_constraints) + [1] * n_constraints
    print(f"Función objetivo Fase 1: {c_phase1}")
    
    # Tableau inicial de Fase 1
    tableau_phase1 = []
    
    # Agregar restricciones
    for i, (row, rhs) in enumerate(zip(A_with_artificial, b_converted)):
        tableau_row = row + [rhs]
        tableau_phase1.append(tableau_row)
    
    # Agregar función objetivo
    obj_row = c_phase1 + [0]  # +0 para el RHS
    tableau_phase1.append(obj_row)
    
    print(f"\nTableau inicial Fase 1:")
    print_tableau(tableau_phase1)
    
    # La base inicial son las variables artificiales
    basis = [n_vars + n_constraints + i for i in range(n_constraints)]  # x5, x6
    print(f"Base inicial: {basis} (variables artificiales)")
    
    # Como las variables artificiales están en la base pero tienen coeficiente +1 en la función objetivo,
    # necesitamos hacer operaciones para hacer que sus coeficientes en la fila objetivo sean 0
    
    print(f"\n=== HACER CEROS EN LA FILA OBJETIVO PARA VARIABLES EN BASE ===")
    
    # Para cada variable artificial en la base, restar su fila de la fila objetivo
    obj_row_idx = len(tableau_phase1) - 1
    
    for i, var_in_basis in enumerate(basis):
        if var_in_basis >= n_vars + n_constraints:  # Es variable artificial
            print(f"Variable artificial x{var_in_basis+1} está en posición básica {i}")
            print(f"Restando fila {i} de la fila objetivo...")
            
            # Restar fila i de la fila objetivo
            for j in range(len(tableau_phase1[obj_row_idx])):
                tableau_phase1[obj_row_idx][j] -= tableau_phase1[i][j]
    
    print(f"\nTableau después de ajustar fila objetivo:")
    print_tableau(tableau_phase1)
    
    print(f"\n🔍 Análisis del problema encontrado:")
    print(f"El solver probablemente falla en alguno de estos pasos:")
    print(f"1. Conversión correcta de >= a <=")
    print(f"2. Manejo de variables artificiales")
    print(f"3. Construcción del tableau inicial")
    print(f"4. Operaciones de pivoteo")
    print(f"5. Transición de Fase 1 a Fase 2")

def print_tableau(tableau):
    """Imprime el tableau de forma legible"""
    for i, row in enumerate(tableau):
        row_str = "  ".join(f"{val:8.2f}" for val in row)
        if i == len(tableau) - 1:
            print(f"Z | {row_str}")
        else:
            print(f"{i+1} | {row_str}")

if __name__ == "__main__":
    debug_two_phase_solver()
