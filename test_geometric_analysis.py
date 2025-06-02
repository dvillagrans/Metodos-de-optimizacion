#!/usr/bin/env python3
"""
Análisis detallado del problema de múltiples soluciones óptimas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from app.solvers.simplex_solver import simplex

def test_multiple_solutions_analysis():
    """Análisis detallado de múltiples soluciones"""
    
    print("="*60)
    print("ANÁLISIS DETALLADO - MÚLTIPLES SOLUCIONES ÓPTIMAS")
    print("="*60)
    
    # Problema: MAX Z = x₁ + x₂
    # s.a.: x₁ + x₂ ≤ 4
    #       2x₁ + x₂ ≤ 6
    #       x₁,x₂ ≥ 0
    
    print("Problema:")
    print("MAX Z = x₁ + x₂")
    print("s.a.: x₁ + x₂ ≤ 4")
    print("      2x₁ + x₂ ≤ 6")
    print("      x₁,x₂ ≥ 0")
    print()
    
    # Forma estándar
    c = [1, 1, 0, 0]  # MAX: [1, 1, 0, 0]
    A = [
        [1, 1, 1, 0],   # x₁ + x₂ + s₁ = 4
        [2, 1, 0, 1]    # 2x₁ + x₂ + s₂ = 6
    ]
    b = [4, 6]
    
    print("Forma estándar:")
    print("c =", c)
    print("A =", A)
    print("b =", b)
    print()
    
    # Analizar las dos soluciones óptimas esperadas
    print("ANÁLISIS DE SOLUCIONES ESPERADAS:")
    print("-" * 40)
    
    solutions = [
        ("(0,4)", [0, 4, 0, 2]),  # x₁=0, x₂=4, s₁=0, s₂=2
        ("(2,2)", [2, 2, 0, 0])   # x₁=2, x₂=2, s₁=0, s₂=0
    ]
    
    for name, sol in solutions:
        x1, x2, s1, s2 = sol
        print(f"\nSolución {name}: x₁={x1}, x₂={x2}, s₁={s1}, s₂={s2}")
        
        # Verificar restricciones
        constraint1 = x1 + x2 + s1
        constraint2 = 2*x1 + x2 + s2
        obj_value = x1 + x2
        
        print(f"  Restricción 1: {x1} + {x2} + {s1} = {constraint1} (debe ser 4)")
        print(f"  Restricción 2: 2×{x1} + {x2} + {s2} = {constraint2} (debe ser 6)")
        print(f"  Valor objetivo: Z = {x1} + {x2} = {obj_value}")
        
        valid1 = abs(constraint1 - 4) < 1e-6
        valid2 = abs(constraint2 - 6) < 1e-6
        non_negative = all(v >= -1e-6 for v in sol)
        
        if valid1 and valid2 and non_negative:
            print(f"  ✅ Solución factible y óptima")
        else:
            print(f"  ❌ Solución no válida")
    
    print("\n" + "="*60)
    print("PRUEBA CON SIMPLEX INICIANDO DESDE DIFERENTES PUNTOS")
    print("="*60)
    
    # Ejecutar simplex normal
    print("\n1. SIMPLEX ESTÁNDAR:")
    result = simplex(c, A, b, track_iterations=True)
    if len(result) >= 2:
        solution = result[0]
        obj_value = result[1]
        print(f"  Solución: {solution}")
        print(f"  Valor objetivo: {obj_value}")
        
        if len(result) >= 3:
            tableau_history = result[2]
            print(f"  Número de iteraciones: {len(tableau_history)}")
            if tableau_history:
                final_tableau = tableau_history[-1]
                print(f"  Tableau final:")
                for i, row in enumerate(final_tableau):
                    if i == 0:
                        print(f"    Z: {row}")
                    else:
                        print(f"    R{i}: {row}")
                
                # Analizar el tableau final
                print(f"\n  ANÁLISIS DEL TABLEAU FINAL:")
                z_row = final_tableau[0, :-1]
                print(f"    Costos reducidos: {z_row}")
                
                # Buscar variables no básicas con costo reducido cero
                zero_cost_vars = []
                for j, cost in enumerate(z_row):
                    if abs(cost) < 1e-6:
                        zero_cost_vars.append(f"x{j+1}" if j < 2 else f"s{j-1}")
                
                if zero_cost_vars:
                    print(f"    Variables con costo reducido ≈ 0: {zero_cost_vars}")
                    print(f"    🎯 INDICA MÚLTIPLES SOLUCIONES ÓPTIMAS")
                else:
                    print(f"    No hay variables no básicas con costo reducido cero")
                    print(f"    ❌ No se detectan múltiples soluciones por este método")
    
    print("\n" + "="*60)
    print("VERIFICACIÓN GEOMÉTRICA")
    print("="*60)
    
    # Verificar el gradiente de la función objetivo
    print("\nAnálisis geométrico:")
    print("Gradiente de Z = x₁ + x₂: ∇Z = (1, 1)")
    print("Restricción activa 1: x₁ + x₂ = 4, normal = (1, 1)")
    print("Restricción activa 2: 2x₁ + x₂ = 6, normal = (2, 1)")
    print()
    print("En el punto (2,2):")
    print("  - Ambas restricciones están activas")
    print("  - El gradiente de Z es paralelo al de la restricción 1")
    print("  - Esto indica múltiples soluciones a lo largo de la restricción 1")
    print()
    print("En el punto (0,4):")
    print("  - Solo la restricción 1 está activa")
    print("  - También es una solución óptima")
    print()
    print("CONCLUSIÓN: El segmento de línea entre (0,4) y (2,2) contiene")
    print("todas las soluciones óptimas con Z = 4")

if __name__ == "__main__":
    test_multiple_solutions_analysis()
