#!/usr/bin/env python3
"""
Test específico para debuggear el problema de dos fases.
"""

import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.solvers.dosfases_solver import dosfases_solver

def debug_two_phase():
    """Debug detallado del método de dos fases"""
    print("=== DEBUG DETALLADO DEL MÉTODO DE DOS FASES ===")
    
    # Problema original:
    # min  3x1 + 2x2 + 3x3
    # s.t. x1 + 4x2 + x3 >= 7
    #      2x1 + x2 + x3 >= 10
    #      x1, x2, x3 >= 0
    
    c = np.array([3, 2, 3], dtype=float)
    A = np.array([
        [1, 4, 1],    # x1 + 4x2 + x3 >= 7
        [2, 1, 1]     # 2x1 + x2 + x3 >= 10
    ], dtype=float)
    b = np.array([7, 10], dtype=float)
    
    print("Problema original:")
    print(f"c = {c}")
    print(f"A = \n{A}")
    print(f"b = {b}")
    print(f"Restricciones >= en índices: [0, 1]")
    
    # Paso 1: Conversión manual a forma estándar
    print("\n--- CONVERSIÓN MANUAL A FORMA ESTÁNDAR ---")
    
    # Para >= restricciones, multiplicamos por -1 para convertir a <=
    A_std = A.copy()
    b_std = b.copy()
    
    # Convertir >= a <=
    A_std[0] = -A_std[0]  # -x1 - 4x2 - x3 <= -7
    b_std[0] = -b_std[0]
    A_std[1] = -A_std[1]  # -2x1 - x2 - x3 <= -10
    b_std[1] = -b_std[1]
    
    print(f"Después de convertir >= a <=:")
    print(f"A_std = \n{A_std}")
    print(f"b_std = {b_std}")
    
    # Agregar variables de holgura
    slack_matrix = np.eye(2)
    A_with_slack = np.hstack([A_std, slack_matrix])
    
    print(f"Después de agregar variables de holgura:")
    print(f"A_with_slack = \n{A_with_slack}")
    
    # Para restricciones que fueron >= (ahora <=), necesitamos variables artificiales
    # porque tenemos b < 0
    print(f"b_std después de conversión: {b_std}")
    print("Como b_std tiene valores negativos, necesitamos variables artificiales")
    
    # Intentar resolver paso a paso
    print("\n--- RESOLVIENDO CON DOSFASES_SOLVER ---")
    try:
        resultado = dosfases_solver(
            c, A, b, 
            eq_constraints=[],
            ge_constraints=[0, 1],
            minimize=True,
            track_iterations=True
        )
        
        if resultado is None or len(resultado) < 2:
            print("❌ El solver devolvió None o resultado incompleto")
            return
            
        solution, optimal_value = resultado[0], resultado[1]
        
        print(f"Resultado del solver:")
        print(f"  Solución: {solution}")
        print(f"  Valor óptimo: {optimal_value}")
        
        if len(resultado) > 2:
            tableau_history = resultado[2]
            print(f"  Número de iteraciones: {len(tableau_history)}")
            if len(tableau_history) > 0:
                print(f"  Tableau final:\n{tableau_history[-1]}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def manual_solution():
    """Calcular la solución manualmente usando gráficos/geometría"""
    print("\n=== CÁLCULO MANUAL DE LA SOLUCIÓN ===")
    
    # El problema es:
    # min  3x1 + 2x2 + 3x3
    # s.t. x1 + 4x2 + x3 >= 7
    #      2x1 + x2 + x3 >= 10
    #      x1, x2, x3 >= 0
    
    # Para encontrar el óptimo, necesitamos encontrar las intersecciones de las restricciones
    # que forman los vértices del poliedro factible
    
    print("Analizando vértices del poliedro factible...")
    
    # Casos básicos donde algunas variables son 0:
    
    # Caso 1: x1 = 0, x3 = 0 → 4x2 >= 7 y x2 >= 10 → x2 = 10
    # Verificar: 0 + 4*10 + 0 = 40 >= 7 ✓, 2*0 + 10 + 0 = 10 >= 10 ✓
    # Z = 3*0 + 2*10 + 3*0 = 20
    candidates = [(0, 10, 0, 20)]
    print(f"Candidato 1: x1=0, x2=10, x3=0, Z=20")
    
    # Caso 2: x1 = 0, x2 = 0 → x3 >= 7 y x3 >= 10 → x3 = 10
    # Verificar: 0 + 0 + 10 = 10 >= 7 ✓, 2*0 + 0 + 10 = 10 >= 10 ✓
    # Z = 3*0 + 2*0 + 3*10 = 30
    candidates.append((0, 0, 10, 30))
    print(f"Candidato 2: x1=0, x2=0, x3=10, Z=30")
    
    # Caso 3: x2 = 0, x3 = 0 → x1 >= 7 y 2x1 >= 10 → x1 = 7 (máximo de 7 y 5)
    # Verificar: 7 + 0 + 0 = 7 >= 7 ✓, 2*7 + 0 + 0 = 14 >= 10 ✓
    # Z = 3*7 + 2*0 + 3*0 = 21
    candidates.append((7, 0, 0, 21))
    print(f"Candidato 3: x1=7, x2=0, x3=0, Z=21")
    
    # Caso 4: x1 = 0, intersección de restricciones activas
    # x1 + 4x2 + x3 = 7 → 4x2 + x3 = 7
    # 2x1 + x2 + x3 = 10 → x2 + x3 = 10
    # Resolviendo: 4x2 + x3 = 7, x2 + x3 = 10
    # Restando: 3x2 = -3 → x2 = -1 (no factible)
    print(f"Candidato 4: No factible (x2 < 0)")
    
    # Caso 5: x2 = 0, intersección de restricciones activas
    # x1 + x3 = 7, 2x1 + x3 = 10
    # Restando: x1 = 3, entonces x3 = 4
    # Verificar: 3 + 0 + 4 = 7 >= 7 ✓, 2*3 + 0 + 4 = 10 >= 10 ✓
    # Z = 3*3 + 2*0 + 3*4 = 9 + 12 = 21
    candidates.append((3, 0, 4, 21))
    print(f"Candidato 5: x1=3, x2=0, x3=4, Z=21")
    
    # Caso 6: x3 = 0, intersección de restricciones activas
    # x1 + 4x2 = 7, 2x1 + x2 = 10
    # De la segunda: x1 = (10 - x2)/2
    # Sustituyendo: (10 - x2)/2 + 4x2 = 7
    # 10 - x2 + 8x2 = 14 → 7x2 = 4 → x2 = 4/7
    # x1 = (10 - 4/7)/2 = (70/7 - 4/7)/2 = 66/14 = 33/7
    x2 = 4/7
    x1 = 33/7
    z_val = 3*x1 + 2*x2 + 3*0
    # Verificar factibilidad
    r1 = x1 + 4*x2
    r2 = 2*x1 + x2
    if r1 >= 7 - 1e-6 and r2 >= 10 - 1e-6 and x1 >= 0 and x2 >= 0:
        candidates.append((x1, x2, 0, z_val))
        print(f"Candidato 6: x1={x1:.6f}, x2={x2:.6f}, x3=0, Z={z_val:.6f}")
        print(f"  Verificación: {r1:.6f} >= 7, {r2:.6f} >= 10")
    else:
        print(f"Candidato 6: No factible")
    
    # Encontrar el mínimo
    if candidates:
        best = min(candidates, key=lambda x: x[3])
        print(f"\n✅ SOLUCIÓN ÓPTIMA MANUAL: x1={best[0]:.6f}, x2={best[1]:.6f}, x3={best[2]:.6f}, Z={best[3]:.6f}")
        return best
    else:
        print("❌ No se encontraron candidatos factibles")
        return None

if __name__ == "__main__":
    manual_solution()
    debug_two_phase()
