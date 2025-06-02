import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.solvers.simplex_solver import simplex
from app.solvers.granm_solver import granm_solver  
from app.solvers.dosfases_solver import dosfases_solver

def verify_constraints(solution, constraints, sense_list, b_values):
    """Verifica si una solución cumple todas las restricciones"""
    x1, x2, x3 = solution
    
    print(f"    Verificación para solución: [{x1:.3f}, {x2:.3f}, {x3:.3f}]:")
    
    all_satisfied = True
    for i, (constraint, tipo) in enumerate(zip(constraints, sense_list)):
        left_side = sum(constraint[j] * solution[j] for j in range(len(solution)))
        rhs = b_values[i]
        
        if tipo in ['<=', '≤']:
            satisfied = left_side <= rhs + 1e-6  # tolerancia numérica
            symbol = '≤'
        elif tipo in ['>=', '≥']:
            satisfied = left_side >= rhs - 1e-6
            symbol = '≥'
        else:  # '='
            satisfied = abs(left_side - rhs) <= 1e-6
            symbol = '='
        
        status = "✓" if satisfied else "✗"
        print(f"      Restricción {i+1}: {left_side:.3f} {symbol} {rhs} ({status})")
        
        if not satisfied:
            all_satisfied = False
    
    return all_satisfied

def test_specific_problem():
    """
    Prueba el problema específico:
    MAX Z = 2x₁ + 3x₂ + 4x₃
    s.a.  x₁ + x₂ + x₃ ≤ 30
         2x₁ + x₂     ≥ 40
         3x₂ + 2x₃    ≤ 60
         x₁,x₂,x₃ ≥ 0
    """
    print("🧪 PROBLEMA ESPECÍFICO DEL USUARIO")
    print("=" * 50)
    print("MAX Z = 2x₁ + 3x₂ + 4x₃")
    print("s.a.  x₁ + x₂ + x₃ ≤ 30")
    print("     2x₁ + x₂     ≥ 40")
    print("     3x₂ + 2x₃    ≤ 60")
    print("     x₁,x₂,x₃ ≥ 0")
    print()
      # Configuración del problema
    c = [2, 3, 4]  # Coeficientes de la función objetivo
    A = [
        [1, 1, 1],   # x₁ + x₂ + x₃ ≤ 30
        [2, 1, 0],   # 2x₁ + x₂ ≥ 40
        [0, 3, 2]    # 3x₂ + 2x₃ ≤ 60
    ]
    b = [30, 40, 60]
    sense = ['≤', '≥', '≤']  # Tipos de restricciones para Gran M y Dos Fases
    
    # Para verificación de restricciones (formato original)
    A_original = A.copy()
    
    # Matriz A para el solver Simplex regular (con conversión de ≥ a ≤)
    A_simplex = [
        [1, 1, 1],   # x₁ + x₂ + x₃ ≤ 30
        [-2, -1, 0], # -2x₁ - x₂ ≤ -40 (equivalente a 2x₁ + x₂ ≥ 40)
        [0, 3, 2]    # 3x₂ + 2x₃ ≤ 60
    ]
    b_simplex = [30, -40, 60]
    
    print("💡 Soluciones factibles conocidas:")
    print("   [20, 0, 0] → Z = 2(20) + 3(0) + 4(0) = 40")
    print("   [10, 20, 0] → Z = 2(10) + 3(20) + 4(0) = 80")
    print("   Óptimo esperado: alrededor de Z = 80-100")
    print()    # Probar los tres métodos
    print("📊 Método: Simplex Regular")
    print("    ⚠️ Saltando - No puede manejar restricciones ≥ directamente")
    print("-" * 40)
    
    print("📊 Método: Gran M")
    try:
        result = granm_solver(c, A, b, sense=sense, track_iterations=True)
        
        if isinstance(result, tuple):
            # Desempaquetar tupla si es necesario
            if len(result) >= 3:
                solution = result[0]
                optimal_value = result[1]
                status = 'optimal' if solution is not None else 'error'
            else:
                print("    Estado: ❌ Resultado inesperado")
                print(f"    Resultado: {result}")
                solution = None
                status = 'error'
        elif isinstance(result, dict):
            solution = result.get('solution')
            optimal_value = result.get('optimal_value')
            status = result.get('status', 'optimal' if solution is not None else 'error')
        else:
            print(f"    Estado: ❌ Tipo de resultado inesperado: {type(result)}")
            solution = None
            status = 'error'
        
        if status == 'optimal' and solution is not None:
            # Verificar si la solución es factible
            is_feasible = verify_constraints(solution, A_original, sense, b)
            
            status_icon = "✅" if is_feasible else "❌"
            print(f"    Estado: {status_icon} {'Factible' if is_feasible else 'NO FACTIBLE'}")
            print(f"    Solución: [{solution[0]:.3f}, {solution[1]:.3f}, {solution[2]:.3f}]")
            print(f"    Valor óptimo: {optimal_value:.3f}")
            
            if not is_feasible:
                print("    ⚠️ PROBLEMA: Solución matemáticamente incorrecta")
        else:
            print(f"    Estado: ❌ {status}")
    
    except Exception as e:
        print(f"    Estado: ❌ Error de ejecución")
        print(f"    Error: {str(e)}")
    
    print("-" * 40)
    
    print("📊 Método: Dos Fases")
    try:
        # Dos Fases necesita identificar restricciones de igualdad
        eq_constraints = []  # No hay restricciones de igualdad en este problema
        result = dosfases_solver(c, A, b, eq_constraints=eq_constraints, track_iterations=True)
        
        if isinstance(result, tuple):
            # Desempaquetar tupla si es necesario
            if len(result) >= 3:
                solution = result[0]
                optimal_value = result[1]
                status = 'optimal' if solution is not None else 'error'
            else:
                print("    Estado: ❌ Resultado inesperado")
                print(f"    Resultado: {result}")
                solution = None
                status = 'error'
        elif isinstance(result, dict):
            solution = result.get('solution')
            optimal_value = result.get('optimal_value')
            status = result.get('status', 'optimal' if solution is not None else 'error')
        else:
            print(f"    Estado: ❌ Tipo de resultado inesperado: {type(result)}")
            solution = None
            status = 'error'
        
        if status == 'optimal' and solution is not None:
            # Verificar si la solución es factible
            is_feasible = verify_constraints(solution, A_original, sense, b)
            
            status_icon = "✅" if is_feasible else "❌"
            print(f"    Estado: {status_icon} {'Factible' if is_feasible else 'NO FACTIBLE'}")
            print(f"    Solución: [{solution[0]:.3f}, {solution[1]:.3f}, {solution[2]:.3f}]")
            print(f"    Valor óptimo: {optimal_value:.3f}")
            
            if not is_feasible:
                print("    ⚠️ PROBLEMA: Solución matemáticamente incorrecta")
        else:
            print(f"    Estado: ❌ {status}")
    
    except Exception as e:
        print(f"    Estado: ❌ Error de ejecución")
        print(f"    Error: {str(e)}")
    
    print("-" * 40)

if __name__ == "__main__":
    test_specific_problem()
