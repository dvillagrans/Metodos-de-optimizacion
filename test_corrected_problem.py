#!/usr/bin/env python3
"""
Test corregido para verificar que funciona el problema de MAX Z = x₁ + x₂
con las correcciones aplicadas.
"""

import requests
import json

def test_simple_max_problem():
    """Test del problema MAX Z = x₁ + x₂ s.a. x₁ + x₂ ≤ 4, 2x₁ + x₂ ≤ 6, x₁, x₂ ≥ 0"""
    
    print("🔍 Testing problema corregido...")
    
    # URL del endpoint
    url = "http://localhost:5000/api/dosfases/solve"
    
    # Datos del problema
    data = {
        "c": [1, 1],  # MAX Z = x₁ + x₂
        "A": [[1, 1], [2, 1]],  # x₁ + x₂ ≤ 4, 2x₁ + x₂ ≤ 6
        "b": [4, 6],
        "eq_constraints": [],
        "ge_constraints": [],
        "minimize": False  # Maximización
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Solicitud exitosa!")
            print(f"📊 Solución: {result.get('solution')}")
            print(f"🎯 Valor óptimo: {result.get('optimal_value')}")
            print(f"🔍 ¿Soluciones múltiples?: {result.get('has_multiple_solutions')}")
            
            # Verificar que el valor óptimo sea positivo (4.0)
            optimal_value = result.get('optimal_value')
            if optimal_value and optimal_value > 0:
                print(f"✅ Valor óptimo correcto: {optimal_value} (debería ser 4.0)")
            else:
                print(f"❌ Valor óptimo incorrecto: {optimal_value} (debería ser 4.0)")
                
            # Verificar la solución
            solution = result.get('solution')
            if solution and len(solution) >= 2:
                x1, x2 = solution[0], solution[1]
                z_value = x1 + x2
                print(f"📐 Verificación: x₁={x1:.3f}, x₂={x2:.3f}, Z=x₁+x₂={z_value:.3f}")
                
                # Verificar restricciones
                constraint1 = x1 + x2 <= 4 + 1e-6  # x₁ + x₂ ≤ 4
                constraint2 = 2*x1 + x2 <= 6 + 1e-6  # 2x₁ + x₂ ≤ 6
                non_negative = x1 >= -1e-6 and x2 >= -1e-6  # x₁, x₂ ≥ 0
                
                if constraint1 and constraint2 and non_negative:
                    print("✅ Todas las restricciones se cumplen")
                else:
                    print("❌ Alguna restricción no se cumple")
                    print(f"   x₁ + x₂ ≤ 4: {constraint1} ({x1 + x2:.3f} ≤ 4)")
                    print(f"   2x₁ + x₂ ≤ 6: {constraint2} ({2*x1 + x2:.3f} ≤ 6)")
                    print(f"   x₁, x₂ ≥ 0: {non_negative} (x₁={x1:.3f}, x₂={x2:.3f})")
            
            return True
            
        else:
            print(f"❌ Error en la solicitud: {response.status_code}")
            print(f"📝 Respuesta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        print("💡 Asegúrate de que el servidor Flask esté corriendo en puerto 5000")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_max_problem()
    if success:
        print("\n🎉 Test completado exitosamente!")
    else:
        print("\n💥 Test falló!")
