#!/usr/bin/env python3
"""
Script para probar la detección de soluciones múltiples localmente
"""

import sys
import numpy as np

# Agregar el directorio del proyecto al path
sys.path.append('.')

def test_multiple_solutions_detector():
    """Prueba el detector de soluciones múltiples con un tableau conocido"""
    
    try:
        from app.solvers.multiple_solutions_detector import detect_multiple_solutions, format_multiple_solutions_result
        print("✅ Imports exitosos")
        
        # Crear un tableau final típico para el problema:
        # MAX Z = x₁ + x₂
        # s.a. x₁ + x₂ ≤ 4, 2x₁ + x₂ ≤ 6, x₁,x₂ ≥ 0
        #
        # Una solución óptima posible es x₁=2, x₂=2, s₁=0, s₂=0
        # El tableau final podría ser (esto es un ejemplo):
        
        # Ejemplo de tableau final donde x1 y x2 están en la base
        # Fila Z: [0, 0, 0, 0, 4] (costos reducidos 0 para x1,x2 indican soluciones múltiples)
        # Variables: x1, x2, s1, s2, RHS
        tableau_final = np.array([
            [0,  0,  -1,  -1,  -4],  # Fila Z (negativa porque es maximización)
            [1,  0,   1,  -1,   2],  # x1 básica = 2
            [0,  1,  -1,   1,   2],  # x2 básica = 2
        ])
        
        print("\n🧮 Probando tableau final:")
        print("Variables: x1, x2, s1, s2")
        print("Tableau:")
        print(tableau_final)
        
        # Detectar soluciones múltiples
        n_original_vars = 2  # x1, x2
        result = detect_multiple_solutions(tableau_final, n_original_vars)
        
        print(f"\n📊 Resultados de detección:")
        print(f"  Tiene soluciones múltiples: {result['has_multiple']}")
        print(f"  Variables con costo reducido cero: {result['zero_cost_vars']}")
        print(f"  Solución actual: {result['current_solution']['values']}")
        print(f"  Valor objetivo: {result['current_solution']['objective_value']}")
        
        if result['alternative_solutions']:
            print(f"\n🔄 Soluciones alternativas encontradas: {len(result['alternative_solutions'])}")
            for i, alt in enumerate(result['alternative_solutions']):
                print(f"  Alt {i+1}: {alt['values']} (Z = {alt['objective_value']})")
        
        # Probar formateo
        formatted = format_multiple_solutions_result(result, ['x1', 'x2'])
        print(f"\n📋 Resultado formateado:")
        print(f"  has_multiple_solutions: {formatted['has_multiple_solutions']}")
        print(f"  multiple_solution_vars: {formatted['multiple_solution_vars']}")
        
    except ImportError as e:
        print(f"❌ Error de import: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def test_simple_case():
    """Prueba con un caso más simple"""
    
    print("\n" + "="*50)
    print("🧪 Prueba con caso simple")
    
    # Tableau donde x2 no está en la base y tiene costo reducido 0
    # MAX Z = x1 + x2
    # Solución: x1=3, x2=0 (pero x2 puede entrar sin cambiar Z)
    tableau_simple = np.array([
        [0,  0,  -1,   0,  -3],  # Fila Z: x2 tiene costo reducido 0
        [1,  1,   1,   0,   3],  # x1 + x2 + s1 = 3, x1 básica
        [0, -1,   2,   1,   1],  # -x2 + 2s1 + s2 = 1, s2 básica  
    ])
    
    try:
        from app.solvers.multiple_solutions_detector import detect_multiple_solutions
        
        print("Tableau simple:")
        print(tableau_simple)
        
        result = detect_multiple_solutions(tableau_simple, 2)
        print(f"\nResultados:")
        print(f"  Soluciones múltiples: {result['has_multiple']}")
        print(f"  Variables candidatas: {result['zero_cost_vars']}")
        print(f"  Solución actual: {result['current_solution']['values']}")
        
        return result['has_multiple']
        
    except Exception as e:
        print(f"❌ Error en prueba simple: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando pruebas del detector de soluciones múltiples")
    print("="*60)
    
    success1 = test_multiple_solutions_detector()
    success2 = test_simple_case()
    
    print("\n" + "="*60)
    if success1 and success2:
        print("✅ Todas las pruebas exitosas")
        print("\n🎯 Para probar tu problema específico:")
        print("   1. Ejecuta el servidor: python run.py")
        print("   2. Ve a http://localhost:5000/dosfases")
        print("   3. Ingresa:")
        print("      c: 1,1")
        print("      A: 1,1")
        print("         2,1")
        print("      b: 4,6")
        print("      ✓ Mostrar iteraciones")
        print("   4. Presiona 'Resolver'")
        print("\n   Deberías ver una alerta sobre 'soluciones óptimas múltiples'")
    else:
        print("❌ Algunas pruebas fallaron")
