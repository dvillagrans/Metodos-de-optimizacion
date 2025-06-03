#!/usr/bin/env python3
"""
Test del problema específico de minimización con dos fases.
"""

import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.solvers.dosfases_solver import dosfases_solver

def test_problema_correcto():
    """Test del problema correcto con dos fases"""
    print("=== TEST PROBLEMA CORRECTO CON DOS FASES ===")
    
    # Problema correcto:
    # min  3x1 + 2x2 + 3x3 + 0x4
    # s.t. x1 + 4x2 + 3x3 + 0x4 >= 7
    #      2x1 + x2 + 0x3 + x4 >= 10
    #      x1, x2, x3, x4 >= 0
    
    # Solución esperada: Z = 7/2 = 3.5, x1=0, x2=7/4=1.75, x3=0, x4=33/4=8.25
    
    print("\nProblema:")
    print("min  3x1 + 2x2 + 3x3 + 0x4")
    print("s.t. x1 + 4x2 + 3x3 + 0x4 >= 7")
    print("     2x1 + x2 + 0x3 + x4 >= 10")
    print("     x1, x2, x3, x4 >= 0")
    
    c = [3, 2, 3, 0]
    A = [
        [1, 4, 3, 0],   # x1 + 4x2 + 3x3 + 0x4 >= 7
        [2, 1, 0, 1]    # 2x1 + x2 + 0x3 + x4 >= 10
    ]
    b = [7, 10]
    
    # Especificar que ambas restricciones son >=
    ge_constraints = [0, 1]  # Indices de restricciones >=
    eq_constraints = []      # No hay restricciones =
    
    print(f"\nDatos del problema:")
    print(f"c = {c}")
    print(f"A = {A}")
    print(f"b = {b}")
    print(f"Restricciones >= (indices): {ge_constraints}")
    
    # Verificar factibilidad de la solución esperada
    expected_x = [0, 7/4, 0, 33/4]  # [0, 1.75, 0, 8.25]
    expected_z = 7/2  # 3.5
    
    constraint1_expected = expected_x[0] + 4*expected_x[1] + 3*expected_x[2] + 0*expected_x[3]
    constraint2_expected = 2*expected_x[0] + expected_x[1] + 0*expected_x[2] + expected_x[3]
    objective_expected = 3*expected_x[0] + 2*expected_x[1] + 3*expected_x[2] + 0*expected_x[3]
    
    print(f"\n=== VERIFICACIÓN MANUAL DE LA SOLUCIÓN ESPERADA ===")
    print(f"x = {expected_x} = [0, {float(expected_x[1])}, 0, {float(expected_x[3])}]")
    print(f"Restricción 1: 0 + 4*{float(expected_x[1])} + 3*0 + 0*{float(expected_x[3])} = {constraint1_expected} >= 7? {constraint1_expected >= 7}")
    print(f"Restricción 2: 2*0 + {float(expected_x[1])} + 0*0 + {float(expected_x[3])} = {constraint2_expected} >= 10? {constraint2_expected >= 10}")
    print(f"Función objetivo: 3*0 + 2*{float(expected_x[1])} + 3*0 + 0*{float(expected_x[3])} = {objective_expected} = {float(expected_z)}")
    
    try:
        print(f"\n=== RESOLVIENDO CON DOS FASES ===")
        resultado = dosfases_solver(
            c, A, b, 
            eq_constraints=eq_constraints,
            ge_constraints=ge_constraints,
            minimize=True,
            track_iterations=True
        )
        
        print(f"Resultado del solver: {type(resultado)}")
        
        if resultado is None:
            print("❌ El solver devolvió None")
            return False
            
        # El solver puede devolver diferentes formatos
        if isinstance(resultado, tuple):
            if len(resultado) == 4:
                solution, optimal_value, tableau_history, pivot_history = resultado
            elif len(resultado) == 2:
                solution, optimal_value = resultado
                tableau_history = None
            else:
                print(f"❌ Formato de resultado inesperado: {len(resultado)} elementos")
                return False
        elif isinstance(resultado, dict):
            solution = resultado.get('solution', [])
            optimal_value = resultado.get('optimal_value', None)
            tableau_history = resultado.get('tableau_history', None)
        else:
            print(f"❌ Tipo de resultado inesperado: {type(resultado)}")
            return False
        
        print(f"\n=== RESULTADO DEL SOLVER ===")
        print(f"Solución: {solution}")
        print(f"Valor óptimo: {optimal_value}")
        
        if solution is not None and len(solution) >= 4:
            x1, x2, x3, x4 = solution[0], solution[1], solution[2], solution[3]
            constraint1 = x1 + 4*x2 + 3*x3 + 0*x4
            constraint2 = 2*x1 + x2 + 0*x3 + x4
            objective = 3*x1 + 2*x2 + 3*x3 + 0*x4
            
            print(f"\n=== VERIFICACIÓN DE LA SOLUCIÓN DEL SOLVER ===")
            print(f"x1={x1}, x2={x2}, x3={x3}, x4={x4}")
            print(f"Restricción 1: {x1} + 4*{x2} + 3*{x3} + 0*{x4} = {constraint1} >= 7? {constraint1 >= 7}")
            print(f"Restricción 2: 2*{x1} + {x2} + 0*{x3} + {x4} = {constraint2} >= 10? {constraint2 >= 10}")
            print(f"Función objetivo: 3*{x1} + 2*{x2} + 3*{x3} + 0*{x4} = {objective}")
            
            # Comparar con la solución esperada
            tolerance = 1e-6
            sol_diff = [abs(solution[i] - expected_x[i]) for i in range(4)]
            val_diff = abs(optimal_value - expected_z) if optimal_value is not None else float('inf')
            
            print(f"\n=== COMPARACIÓN ===")
            print(f"Diferencias en variables: {sol_diff}")
            print(f"Diferencia en valor objetivo: {val_diff}")
            
            if all(d < tolerance for d in sol_diff) and val_diff < tolerance:
                print("✅ SOLUCIÓN CORRECTA!")
                return True
            else:
                print("❌ SOLUCIÓN INCORRECTA")
                return False
        else:
            print("❌ No se pudo obtener una solución válida")
            return False
            
    except Exception as e:
        print(f"❌ Error en dos fases: {e}")
        import traceback
        traceback.print_exc()
        return False

def add_ejemplo_to_casos():
    """Agregar el ejemplo a los casos guardados"""
    try:
        from app.utils.data_processing import load_casos, save_casos
        
        ejemplo = {
            "nombre": "Problema 4",
            "descripcion": "Minimización con restricciones >= y soluciones múltiples",
            "metodo": "dosfases",
            "c": [3, 2, 3, 0],
            "A": [
                [1, 4, 3, 0],
                [2, 1, 0, 1]
            ],
            "b": [7, 10],
            "eq_constraints": [],
            "ge_constraints": [0, 1],
            "minimize": True,
            "solucion_esperada": {
                "x": [0, 1.75, 0, 8.25],
                "z": 3.5,
                "multiple_solutions": True,
                "nota": "Hay múltiples soluciones óptimas en el segmento: 3x1 + 2x2 + 3x3 + 0x4 = 7/2"
            }
        }
        
        casos = load_casos()
        casos.append(ejemplo)
        save_casos(casos)
        
        print(f"✅ Ejemplo agregado como 'Problema 4' (índice {len(casos)-1})")
        return True
        
    except Exception as e:
        print(f"❌ Error al agregar ejemplo: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando test del problema correcto...\n")
    
    success = test_problema_correcto()
    
    if success:
        print("\n🎉 TEST EXITOSO - Agregando ejemplo a los casos...")
        add_ejemplo_to_casos()
    else:
        print("\n💥 TEST FALLIDO - Revisar el solver de dos fases")
