#!/usr/bin/env python3
"""
Debug específico de la función solve_tableau.
"""

import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_solve_tableau():
    """Debug específico de solve_tableau con el tableau de Fase 2"""
    print("=== DEBUG ESPECÍFICO DE SOLVE_TABLEAU ===")
    
    # Tableau 5 del debug anterior (inicio de Fase 2)
    tableau = np.array([
        [0.000, 1.000, 0.857, -0.143, -0.286, 0.143, 0.571],
        [1.000, 0.000, -0.429, 0.571, 0.143, -0.571, 4.714],
        [0.000, 0.000, 2.571, -1.429, 0.143, 1.429, -15.286]
    ])
    
    basic_vars = [1, 0]  # x2, x1
    minimize = False  # Tableau en forma de maximización
    
    print(f"Tableau inicial de Fase 2:")
    print_tableau_debug(tableau)
    print(f"Variables básicas: {basic_vars}")
    print(f"minimize: {minimize}")
    
    # Simular una iteración de solve_tableau
    m, n = tableau.shape
    n = n - 1  # Adjust for RHS column
    
    print(f"\nDimensiones: m={m}, n={n}")
    
    # Find entering variable based on optimization type
    z_row = tableau[-1, :-1]
    print(f"Fila objetivo (sin RHS): {z_row}")
    
    if minimize:
        # For minimization: look for most negative coefficient
        entering_col = np.argmin(z_row)
        optimal_condition = z_row[entering_col] >= -1e-10
        print(f"Minimización: columna entrante = {entering_col}, coef = {z_row[entering_col]}")
        print(f"Condición optimal: {optimal_condition}")
    else:
        # For maximization: look for most positive coefficient
        entering_col = np.argmax(z_row)
        optimal_condition = z_row[entering_col] <= 1e-10
        print(f"Maximización: columna entrante = {entering_col}, coef = {z_row[entering_col]}")
        print(f"Condición optimal: {optimal_condition}")
    
    if optimal_condition:
        print("✓ Condición de optimalidad cumplida - se detiene")
        # Extract solution
        solution = np.zeros(n)
        for i, basic_var in enumerate(basic_vars):
            if basic_var < n:
                solution[basic_var] = tableau[i, -1]
        
        optimal_value = tableau[-1, -1]
        print(f"Solución extraída: {solution}")
        print(f"Valor objetivo: {optimal_value}")
    else:
        print("❌ Condición de optimalidad NO cumplida - debería continuar")
        print(f"Variable entrante: x{entering_col+1} (columna {entering_col})")
        
        # Find leaving variable (minimum ratio test)
        pivot_ratios = []
        for i in range(m-1):  # Skip objective row
            if tableau[i, entering_col] > 1e-10:
                ratio = tableau[i, -1] / tableau[i, entering_col]
                pivot_ratios.append((ratio, i))
                print(f"  Fila {i+1}: {tableau[i, -1]} / {tableau[i, entering_col]} = {ratio}")
            else:
                print(f"  Fila {i+1}: coeficiente = {tableau[i, entering_col]} <= 0, no válido")
        
        if not pivot_ratios:
            print("❌ No hay ratios positivos - problema no acotado")
        else:
            # Choose row with minimum positive ratio
            min_ratio, pivot_row = min(pivot_ratios)
            print(f"✓ Variable saliente: fila {pivot_row+1}, ratio mínimo = {min_ratio}")
            print(f"  Pivot: fila {pivot_row+1}, columna {entering_col+1}")
            print(f"  Elemento pivot: {tableau[pivot_row, entering_col]}")
            
            # Simulate pivot operation
            print(f"\n=== SIMULANDO OPERACIÓN DE PIVOT ===")
            tableau_new = tableau.copy()
            
            # Pivot operation
            pivot_element = tableau_new[pivot_row, entering_col]
            print(f"1. Dividir fila {pivot_row+1} por {pivot_element}")
            tableau_new[pivot_row] /= pivot_element
            
            print(f"Fila {pivot_row+1} después de normalizar:")
            print(f"  {tableau_new[pivot_row]}")
            
            print(f"2. Eliminar columna {entering_col+1} en otras filas")
            for i in range(m):
                if i != pivot_row:
                    multiplier = tableau_new[i, entering_col]
                    print(f"  Fila {i+1}: restar {multiplier} * fila_pivot")
                    tableau_new[i] -= multiplier * tableau_new[pivot_row]
            
            print(f"\nTableau después del pivot:")
            print_tableau_debug(tableau_new)
            
            # Update basic variables
            basic_vars_new = basic_vars.copy()
            basic_vars_new[pivot_row] = entering_col
            print(f"Nuevas variables básicas: {basic_vars_new}")

def print_tableau_debug(tableau):
    """Print tableau in readable format."""
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
    debug_solve_tableau()
