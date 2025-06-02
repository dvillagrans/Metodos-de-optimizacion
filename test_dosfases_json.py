#!/usr/bin/env python3
"""
Script para probar la corrección del error de serialización JSON en el método de Dos Fases
"""

import requests
import json

def test_dosfases_json_serialization():
    """Prueba la serialización JSON del método de Dos Fases"""
    
    # URL del endpoint
    url = "http://localhost:5000/api/resolver/dosfases"
    
    # Datos de prueba que podrían causar tipos int64 de NumPy
    test_data = {
        "c": [3, 2, 1],
        "A": [
            [1, 1, 1],
            [2, 1, -1],
            [1, 2, 1]
        ],
        "b": [6, 4, 8],
        "eq_constraints": [1, 2],  # Estas constraintes causarán uso extensivo de NumPy
        "minimize": False,
        "track_iterations": True  # Esto activará la serialización de tableau_history
    }
    
    print("🧪 Probando método de Dos Fases con serialización JSON...")
    print(f"📊 Datos de entrada: {json.dumps(test_data, indent=2)}")
    
    try:
        # Enviar petición POST
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"\n📡 Código de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            # Intentar deserializar la respuesta JSON
            result = response.json()
            
            print("✅ Serialización JSON exitosa!")
            print(f"🎯 Solución: {result.get('solution', 'No encontrada')}")
            print(f"💰 Valor óptimo: {result.get('optimal_value', 'No encontrado')}")
            
            # Verificar que tableau_history se serializó correctamente
            if 'tableau_history' in result:
                print(f"📊 Historial de tableau: {len(result['tableau_history'])} iteraciones")
                
            # Verificar soluciones múltiples
            if result.get('has_multiple_solutions', False):
                print(f"🔄 Soluciones múltiples detectadas: {len(result.get('alternative_solutions', []))} alternativas")
            
            return True
            
        else:
            print(f"❌ Error en la respuesta: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📝 Mensaje de error: {error_data.get('error', 'Error desconocido')}")
            except:
                print(f"📝 Respuesta sin formato JSON: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error de deserialización JSON: {e}")
        print(f"📝 Respuesta recibida: {response.text[:500]}...")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_simple_dosfases():
    """Prueba más simple para verificar funcionamiento básico"""
    
    url = "http://localhost:5000/api/resolver/dosfases"
    
    # Problema simple
    simple_data = {
        "c": [1, 2],
        "A": [[1, 1], [1, -1]],
        "b": [3, 1],
        "eq_constraints": [0],
        "minimize": False,
        "track_iterations": False
    }
    
    print("\n🧪 Probando versión simple (sin track_iterations)...")
    
    try:
        response = requests.post(url, json=simple_data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Versión simple funcionando correctamente!")
            print(f"🎯 Solución: {result.get('solution')}")
            print(f"💰 Valor óptimo: {result.get('optimal_value')}")
            return True
        else:
            print(f"❌ Error en versión simple: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en versión simple: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Prueba de corrección de serialización JSON - Método de Dos Fases")
    print("=" * 70)
    
    # Probar versión simple primero
    simple_ok = test_simple_dosfases()
    
    # Probar versión completa con historial
    complex_ok = test_dosfases_json_serialization()
    
    print("\n" + "=" * 70)
    print("📋 RESUMEN DE PRUEBAS:")
    print(f"  • Versión simple: {'✅ PASÓ' if simple_ok else '❌ FALLÓ'}")
    print(f"  • Versión completa: {'✅ PASÓ' if complex_ok else '❌ FALLÓ'}")
    
    if simple_ok and complex_ok:
        print("\n🎉 ¡Todas las pruebas pasaron! El error de serialización JSON está corregido.")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisar los errores anteriores.")
