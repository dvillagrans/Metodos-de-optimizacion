#!/usr/bin/env python3
"""
Implementación simplificada y corregida del método de dos fases.
"""

import numpy as np

def two_phase_simple(c, A, b, ge_constraints=None, minimize=False):
    """
    Implementación simplificada del método de dos fases.
    """
    c = np.array(c, dtype=float)
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float)
    
    if ge_constraints is None:
        ge_constraints = []
    
    m, n = A.shape
    print(f"Problema original: {m} restricciones, {n} variables")
    print(f"c = {c}")
    print(f"A = {A}")
    print(f"b = {b}")
    print(f"ge_constraints = {ge_constraints}")
    
    # ===== CONVERSIÓN A FORMA ESTÁNDAR =====
    
    # Para restricciones >=: Ax >= b se convierte en Ax - s + a = b
    # donde s es surplus (variable de surplus) y a es artificial
    
    A_standard = []
    b_standard = []
    surplus_vars = []
    artificial_vars = []
    
    for i in range(m):
        if i in ge_constraints:
            # Restricción >= : Ax >= b => Ax - s + a = b
            A_standard.append(A[i].copy())
            b_standard.append(b[i])
            surplus_vars.append(i)
            artificial_vars.append(i)
        else:
            # Restricción <= : Ax <= b => Ax + s = b
            A_standard.append(A[i].copy())
            b_standard.append(b[i])
    
    A_standard = np.array(A_standard)
    b_standard = np.array(b_standard)
    
    print(f"\\nA_standard = {A_standard}")
    print(f"b_standard = {b_standard}")
    print(f"Variables surplus en restricciones: {surplus_vars}")
    print(f"Variables artificiales en restricciones: {artificial_vars}")
    
    # ===== FASE 1: ENCONTRAR SOLUCIÓN BÁSICA FACTIBLE =====
    
    # Crear matriz extendida con surplus y artificiales
    # Variables: x1,...,xn, s1,...,sm, a1,...,ak (donde k = len(artificial_vars))
    
    n_surplus = m  # Una variable surplus por restricción
    n_artificial = len(artificial_vars)
    n_total = n + n_surplus + n_artificial
    
    A_phase1 = np.zeros((m, n_total))
    
    # Copiar variables originales
    A_phase1[:, :n] = A_standard
    
    # Agregar variables surplus y artificiales
    for i in range(m):
        if i in surplus_vars:
            # Variable surplus (coeficiente -1)
            A_phase1[i, n + i] = -1
            # Variable artificial (coeficiente +1)
            art_idx = artificial_vars.index(i)
            A_phase1[i, n + m + art_idx] = 1
        else:
            # Variable slack normal (coeficiente +1)
            A_phase1[i, n + i] = 1
    
    print(f"\\nA_phase1 ({A_phase1.shape}):")
    print(A_phase1)
    
    # Función objetivo Fase 1: minimizar suma de variables artificiales
    c_phase1 = np.zeros(n_total)
    for i in range(n_artificial):
        c_phase1[n + m + i] = 1
    
    print(f"c_phase1 = {c_phase1}")
    
    # Crear tableau Fase 1
    tableau1 = np.zeros((m + 1, n_total + 1))
    tableau1[:m, :-1] = A_phase1
    tableau1[:m, -1] = b_standard
    tableau1[-1, :-1] = c_phase1  # Ya está para minimización
    
    print(f"\\nTableau inicial Fase 1:")
    print(tableau1)
    
    # Variables básicas iniciales (artificiales)
    basic_vars_1 = []
    for i in range(m):
        if i in artificial_vars:
            art_idx = artificial_vars.index(i)
            basic_vars_1.append(n + m + art_idx)
        else:
            basic_vars_1.append(n + i)  # Variable slack
    
    print(f"Variables básicas iniciales Fase 1: {basic_vars_1}")
    
    # Eliminar variables artificiales básicas de la función objetivo
    for i, constraint_idx in enumerate(artificial_vars):
        art_col = n + m + i
        if abs(tableau1[-1, art_col]) > 1e-10:
            tableau1[-1] -= tableau1[-1, art_col] * tableau1[constraint_idx]
    
    print(f"\\nTableau Fase 1 después de eliminar artificiales:")
    print(tableau1)
    
    # Resolver Fase 1
    solution1, value1, tableau1_final = solve_simplex_tableau(tableau1, basic_vars_1)
    
    print(f"\\nSolución Fase 1: {solution1}")
    print(f"Valor objetivo Fase 1: {value1}")
    print(f"Tableau final Fase 1:")
    print(tableau1_final)
    
    # Verificar factibilidad
    if value1 > 1e-8:
        print("❌ Problema infactible!")
        return None, None
    
    # Verificar que variables artificiales sean cero
    artificial_sum = 0
    for i in range(n_artificial):
        art_var_value = solution1[n + m + i] if solution1 is not None else 0
        artificial_sum += art_var_value
    
    if artificial_sum > 1e-8:
        print("❌ Variables artificiales no son cero!")
        return None, None
    
    print("✅ Fase 1 completada exitosamente")
    
    # ===== FASE 2: OPTIMIZAR FUNCIÓN OBJETIVO ORIGINAL =====
    
    # Remover variables artificiales del tableau
    A_phase2 = A_phase1[:, :n + m]  # Sin variables artificiales
    
    print(f"\\nA_phase2 ({A_phase2.shape}):")
    print(A_phase2)
    
    # Función objetivo original (extendida con ceros para variables slack/surplus)
    c_phase2 = np.zeros(n + m)
    if minimize:
        c_phase2[:n] = c  # Para minimización
    else:
        c_phase2[:n] = -c  # Para maximización
    
    print(f"c_phase2 = {c_phase2}")
    
    # Crear tableau Fase 2
    tableau2 = np.zeros((m + 1, n + m + 1))
    tableau2[:m, :-1] = A_phase2
    tableau2[:m, -1] = tableau1_final[:m, -1]  # RHS de la Fase 1
    
    if minimize:
        tableau2[-1, :-1] = c_phase2  # Minimización
    else:
        tableau2[-1, :-1] = -c_phase2  # Maximización (negar c)
    
    print(f"\\nTableau inicial Fase 2:")
    print(tableau2)
    
    # Variables básicas de la Fase 2 (sin artificiales)
    basic_vars_2 = []
    for var in basic_vars_1:
        if var < n + m:  # Excluir variables artificiales
            basic_vars_2.append(var)
    
    # Completar si faltan variables básicas
    while len(basic_vars_2) < m:
        for i in range(n + m):
            if i not in basic_vars_2:
                basic_vars_2.append(i)
                break
    
    basic_vars_2 = basic_vars_2[:m]  # Exactamente m variables
    print(f"Variables básicas Fase 2: {basic_vars_2}")
    
    # Hacer que variables básicas tengan coeficiente 0 en la función objetivo
    for i, basic_var in enumerate(basic_vars_2):
        if basic_var < n and abs(tableau2[-1, basic_var]) > 1e-8:
            # Esta es una variable original que es básica
            tableau2[-1] -= tableau2[-1, basic_var] * tableau2[i]
    
    print(f"\\nTableau Fase 2 después de ajustar función objetivo:")
    print(tableau2)
    
    # Resolver Fase 2
    solution2, value2, tableau2_final = solve_simplex_tableau(tableau2, basic_vars_2)
    
    print(f"\\nSolución final: {solution2}")
    print(f"Valor objetivo final: {value2}")
    
    if solution2 is None:
        return None, None
    
    # Extraer solo las variables originales
    x = solution2[:n]
    
    # Ajustar valor objetivo según minimización/maximización
    if minimize:
        final_value = value2
    else:
        final_value = -value2
    
    return x, final_value


def solve_simplex_tableau(tableau, basic_vars, max_iter=100):
    """Resuelve un tableau de simplex."""
    m, n = tableau.shape
    n = n - 1  # Excluir columna RHS
    
    for iteration in range(max_iter):
        print(f"\\n--- Iteración {iteration + 1} ---")
        print(f"Tableau actual:")
        print(tableau)
        print(f"Variables básicas: {basic_vars}")
        
        # Encontrar variable entrante (costo reducido más negativo)
        z_row = tableau[-1, :-1]
        entering_col = np.argmin(z_row)
        
        if z_row[entering_col] >= -1e-10:
            print("✅ Solución óptima encontrada")
            break
        
        print(f"Variable entrante: columna {entering_col} (costo reducido: {z_row[entering_col]})")
        
        # Test de la razón mínima
        ratios = []
        for i in range(m - 1):  # Excluir fila objetivo
            if tableau[i, entering_col] > 1e-10:
                ratio = tableau[i, -1] / tableau[i, entering_col]
                ratios.append((ratio, i))
        
        if not ratios:
            print("❌ Problema no acotado")
            return None, None, tableau
        
        # Elegir fila con razón mínima
        min_ratio, leaving_row = min(ratios)
        print(f"Variable saliente: fila {leaving_row} (razón: {min_ratio})")
        
        # Operación pivote
        pivot = tableau[leaving_row, entering_col]
        tableau[leaving_row] /= pivot
        
        for i in range(m):
            if i != leaving_row:
                tableau[i] -= tableau[i, entering_col] * tableau[leaving_row]
        
        # Actualizar variables básicas
        basic_vars[leaving_row] = entering_col
        
    # Extraer solución
    solution = np.zeros(n)
    for i, basic_var in enumerate(basic_vars):
        if basic_var < n:
            solution[basic_var] = tableau[i, -1]
    
    optimal_value = tableau[-1, -1]
    
    return solution, optimal_value, tableau


if __name__ == "__main__":
    # Test del problema
    c = [3, 2, 3, 0]
    A = [
        [1, 4, 3, 0],
        [2, 1, 0, 1]
    ]
    b = [7, 10]
    ge_constraints = [0, 1]
    
    print("=== MÉTODO DE DOS FASES SIMPLIFICADO ===\\n")
    
    solution, optimal_value = two_phase_simple(c, A, b, ge_constraints, minimize=True)
    
    if solution is not None:
        print(f"\\n🎉 SOLUCIÓN ENCONTRADA:")
        print(f"x = {solution}")
        print(f"Z = {optimal_value}")
        
        # Verificar factibilidad
        print(f"\\n=== VERIFICACIÓN ===")
        x1, x2, x3, x4 = solution
        constraint1 = x1 + 4*x2 + 3*x3 + 0*x4
        constraint2 = 2*x1 + x2 + 0*x3 + x4
        objective = 3*x1 + 2*x2 + 3*x3 + 0*x4
        
        print(f"Restricción 1: {x1} + 4*{x2} + 3*{x3} + 0*{x4} = {constraint1} >= 7? {constraint1 >= 7}")
        print(f"Restricción 2: 2*{x1} + {x2} + 0*{x3} + {x4} = {constraint2} >= 10? {constraint2 >= 10}")
        print(f"Función objetivo: 3*{x1} + 2*{x2} + 3*{x3} + 0*{x4} = {objective}")
    else:
        print("\\n❌ No se encontró solución")
