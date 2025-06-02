#!/usr/bin/env python3
"""
Test para verificar la API con el problema de múltiples soluciones óptimas
Usando el formato correcto de la API existente
"""

import requests
import json

def test_multiple_solutions_api():
    """Test de la API con el problema de múltiples soluciones"""
    
    base_url = "http://127.0.0.1:5000"
    
    # Problema: MAX Z = x₁ + x₂
    # s.a. x₁ + x₂ ≤ 4
    #      2x₁ + x₂ ≤ 6
    #      x₁, x₂ ≥ 0
    #
    # En forma estándar:
    # c = [1, 1] (coeficientes de la función objetivo)
    # A = [[1, 1], [2, 1]] (matriz de restricciones)
    # b = [4, 6] (lado derecho)
    
    problem_data = {
        "c": [1, 1],
        "A": [[1, 1], [2, 1]], 
        "b": [4, 6],
        "minimize": False,
        "track_iterations": True
    }
    
    print("="*60)
    print("TEST API - MÚLTIPLES SOLUCIONES ÓPTIMAS")
    print("="*60)
    print("Problema:")
    print("MAX Z = x₁ + x₂")
    print("s.a. x₁ + x₂ ≤ 4")
    print("     2x₁ + x₂ ≤ 6")
    print("     x₁, x₂ ≥ 0")
    print()
    print("Datos API:", json.dumps(problem_data, indent=2))
    print()
    
    # Probar cada método
    methods = ["simplex", "granm", "dosfases"]
    
    for method in methods:
        print(f"\n{'='*20} {method.upper()} {'='*20}")
        try:
            endpoint = f"{base_url}/api/resolver/{method}"
            response = requests.post(endpoint, json=problem_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ Respuesta exitosa")
                print(f"Solución: {result.get('solution', 'N/A')}")
                print(f"Valor óptimo: {result.get('optimal_value', 'N/A')}")
                print(f"Estado: {result.get('status', 'N/A')}")
                
                # Verificar múltiples soluciones usando el nuevo detector
                if 'multiple_solutions' in result:
                    ms = result['multiple_solutions']
                    print(f"¿Múltiples soluciones?: {ms.get('has_multiple_solutions', False)}")
                    
                    if ms.get('has_multiple_solutions'):
                        print(f"🎯 MÚLTIPLES SOLUCIONES DETECTADAS:")
                        if 'alternative_solutions' in ms:
                            for i, alt_sol in enumerate(ms['alternative_solutions'], 1):
                                sol_values = alt_sol.get('solution', [])
                                obj_value = alt_sol.get('objective_value', 'N/A')
                                print(f"  Solución {i}: {sol_values} con Z = {obj_value}")
                        
                        if 'current_solution' in ms:
                            current = ms['current_solution']
                            print(f"  Solución actual: {current}")
                    else:
                        print(f"❌ No se detectaron múltiples soluciones")
                        if 'multiple_solution_vars' in ms:
                            print(f"  Variables con costo reducido cero: {ms['multiple_solution_vars']}")
                
                # Verificar detección de múltiples soluciones (API antigua)
                elif 'has_multiple_solutions' in result:
                    print(f"¿Múltiples soluciones? (API antigua): {result.get('has_multiple_solutions', False)}")
                    if result.get('has_multiple_solutions'):
                        print(f"🎯 MÚLTIPLES SOLUCIONES DETECTADAS (API antigua):")
                        if 'alternative_solutions' in result:
                            for i, alt_sol in enumerate(result['alternative_solutions'], 1):
                                sol_values = alt_sol.get('solution', [])
                                print(f"  Solución alternativa {i}: {sol_values}")
                        
                        if 'multiple_solution_vars' in result:
                            print(f"  Variables con costo reducido cero: {result['multiple_solution_vars']}")
                    else:
                        print(f"❌ No se detectaron múltiples soluciones")
                else:
                    print(f"⚠️  No hay información de múltiples soluciones en la respuesta")
                
                # Mostrar información adicional si está disponible
                if 'tableau_history' in result:
                    print(f"Iteraciones: {len(result['tableau_history'])}")
                
            else:
                print(f"❌ Error HTTP {response.status_code}")
                print(f"Respuesta: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
    
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    print("Este test verifica que los tres métodos (Simplex, Gran M, Dos Fases)")
    print("detecten correctamente las múltiples soluciones óptimas para el problema:")
    print("MAX Z = x₁ + x₂")
    print("s.a. x₁ + x₂ ≤ 4")
    print("     2x₁ + x₂ ≤ 6")
    print("     x₁, x₂ ≥ 0")
    print()
    print("Soluciones esperadas: (0,4) y (2,2) con Z = 4")

if __name__ == "__main__":
    test_multiple_solutions_api()
