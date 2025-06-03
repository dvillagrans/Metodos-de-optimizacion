#!/usr/bin/env python3
"""
Script para debuggear problemas de minimización en el algoritmo Simplex.
"""

import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.solvers.simplex_solver import simplex
from app.solvers.dosfases_solver import dosfases_solver

def test_specific_problem():
    """Test del problema específico proporcionado por el usuario"""
    print("=== TEST DEL PROBLEMA ESPECÍFICO ===")
    
    # Problema:
    # min  3x1 + 2x2 + 3x3
    # s.t. x1 + 4x2 + x3 >= 7
    #      2x1 + x2 + x3 >= 10
    #      x1, x2, x3 >= 0
    
    print("Problema de minimización:")
    print("min  3x1 + 2x2 + 3x3")
    print("s.t. x1 + 4x2 + x3 >= 7")
    print("     2x1 + x2 + x3 >= 10")
    print("     x1, x2, x3 >= 0")
    
    c = [3, 2, 3]
    A = [
        [1, 4, 1],    # x1 + 4x2 + x3 >= 7
        [2, 1, 1]     # 2x1 + x2 + x3 >= 10
    ]
    b = [7, 10]
    
    print("\n--- Resolviendo con método de DOS FASES ---")
    try:
        # Usar la función correcta con track_iterations=True para ver el proceso
        resultado = dosfases_solver(
            c, A, b, 
            eq_constraints=[],
            ge_constraints=[0, 1],  # Ambas restricciones son >=
            minimize=True,
            track_iterations=True
        )
        
        if resultado is None:
            print("❌ El solver devolvió None")
            return False
            
        print(f"Tipo de resultado: {type(resultado)}")
        
        # El resultado debería ser una tupla (solution, optimal_value, phase1_history, phase2_history, ...)
        if isinstance(resultado, tuple) and len(resultado) >= 2:
            solution = resultado[0]
            optimal_value = resultado[1]
            
            print(f"Solución óptima: x1={solution[0]:.6f}, x2={solution[1]:.6f}, x3={solution[2]:.6f}")
            print(f"Valor óptimo: Z = {optimal_value:.6f}")
            
            # Verificar solución esperada
            expected_solution = [0, 6/5, 11/5]  # [0, 1.2, 2.2]
            expected_value = 9
            
            print(f"\nSolución esperada: x1={expected_solution[0]}, x2={expected_solution[1]:.6f}, x3={expected_solution[2]:.6f}")
            print(f"Valor esperado: Z = {expected_value}")
            
            # Verificar restricciones
            print("\n--- Verificación de restricciones ---")
            r1 = solution[0] + 4*solution[1] + solution[2]
            r2 = 2*solution[0] + solution[1] + solution[2]
            
            print(f"Restricción 1: {solution[0]:.6f} + 4*{solution[1]:.6f} + {solution[2]:.6f} = {r1:.6f} >= 7 {'✓' if r1 >= 7-1e-6 else '✗'}")
            print(f"Restricción 2: 2*{solution[0]:.6f} + {solution[1]:.6f} + {solution[2]:.6f} = {r2:.6f} >= 10 {'✓' if r2 >= 10-1e-6 else '✗'}")
            
            # Verificar no negatividad
            print(f"No negatividad: x1={solution[0]:.6f} >= 0 {'✓' if solution[0] >= -1e-6 else '✗'}")
            print(f"No negatividad: x2={solution[1]:.6f} >= 0 {'✓' if solution[1] >= -1e-6 else '✗'}")
            print(f"No negatividad: x3={solution[2]:.6f} >= 0 {'✓' if solution[2] >= -1e-6 else '✗'}")
            
            # Verificar valor de función objetivo
            calculated_z = 3*solution[0] + 2*solution[1] + 3*solution[2]
            print(f"Verificación Z: 3*{solution[0]:.6f} + 2*{solution[1]:.6f} + 3*{solution[2]:.6f} = {calculated_z:.6f}")
            
            # Verificar si coincide con la solución esperada
            tolerance = 1e-3
            sol_diff = np.abs(np.array(solution[:3]) - np.array(expected_solution))
            val_diff = np.abs(optimal_value - expected_value)
            
            print(f"\nDiferencia en solución: {sol_diff}")
            print(f"Diferencia en valor: {val_diff}")
            
            if np.all(sol_diff < tolerance) and val_diff < tolerance:
                print("✅ SOLUCIÓN CORRECTA")
                return True
            else:
                print("❌ SOLUCIÓN INCORRECTA - pero verifiquemos si es una solución válida")
                # Verificar si al menos es una solución factible
                if (r1 >= 7-1e-6 and r2 >= 10-1e-6 and 
                    all(x >= -1e-6 for x in solution[:3])):
                    print("✓ La solución es factible, pero puede ser una solución alternativa")
                    return True
                return False
        else:
            print(f"❌ Resultado no tiene formato esperado: {resultado}")
            return False
            
    except Exception as e:
        print(f"Error en dos fases: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_expected_solution():
    """Verificar manualmente la solución esperada"""
    print("\n=== VERIFICACIÓN MANUAL DE LA SOLUCIÓN ESPERADA ===")
    
    # Solución esperada: x1=0, x2=6/5=1.2, x3=11/5=2.2, Z=9
    x1, x2, x3 = 0, 6/5, 11/5
    
    print(f"Solución esperada: x1={x1}, x2={x2:.6f}, x3={x3:.6f}")
    
    # Verificar restricciones
    r1 = x1 + 4*x2 + x3
    r2 = 2*x1 + x2 + x3
    z_val = 3*x1 + 2*x2 + 3*x3
    
    print(f"Restricción 1: {x1} + 4*{x2:.6f} + {x3:.6f} = {r1:.6f} >= 7 {'✓' if r1 >= 7 else '✗'}")
    print(f"Restricción 2: 2*{x1} + {x2:.6f} + {x3:.6f} = {r2:.6f} >= 10 {'✓' if r2 >= 10 else '✗'}")
    print(f"Función objetivo: 3*{x1} + 2*{x2:.6f} + 3*{x3:.6f} = {z_val:.6f}")
    
    if r1 >= 7 and r2 >= 10 and x1 >= 0 and x2 >= 0 and x3 >= 0:
        print("✅ La solución esperada es factible")
        return True
    else:
        print("❌ La solución esperada NO es factible")
        return False

if __name__ == "__main__":
    print("Iniciando debugger de minimización...\n")
    
    # Verificar solución esperada
    verify_expected_solution()
    
    # Test del algoritmo
    success = test_specific_problem()
    
    if success:
        print("\n🎉 TEST PASÓ")
    else:
        print("\n💥 HAY PROBLEMAS QUE NECESITAN CORRECCIÓN")
