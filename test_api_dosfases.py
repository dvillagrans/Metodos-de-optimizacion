import requests
import json

def test_api_dosfases():
    """Test the API endpoint for Two-Phase method"""
    print("🔧 Prueba API - Método de Dos Fases")
    print("=" * 50)
    
    url = 'http://localhost:5000/api/resolver/dosfases'
    
    # Test data for API
    test_data = {
        'c': [3, 2, 1],
        'A': [[1, 1, 1], [2, 1, -1], [1, 2, 1]],
        'b': [6, 4, 8],
        'eq_constraints': [1, 2],
        'minimize': False,
        'track_iterations': True
    }
    
    print("📊 Datos de entrada (API):")
    print(json.dumps(test_data, indent=2))
    print()
    
    try:
        response = requests.post(
            url, 
            json=test_data, 
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📡 Código de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Respuesta JSON válida!")
                print(f"🎯 Solución: {result.get('solution', 'N/A')}")
                print(f"💰 Valor óptimo: {result.get('optimal_value', 'N/A')}")
                print(f"📊 Iteraciones registradas: {len(result.get('tableau_history', []))}")
                print(f"🔀 Múltiples soluciones: {result.get('has_multiple_solutions', False)}")
                
                if result.get('alternative_solutions'):
                    print(f"🎲 Soluciones alternativas: {len(result['alternative_solutions'])}")
                
                return True
                
            except json.JSONDecodeError:
                print("❌ Error: Respuesta no es JSON válido")
                print(f"📝 Contenido: {response.text[:200]}...")
                return False
        else:
            print(f"❌ Error en la respuesta: {response.status_code}")
            print(f"📝 Mensaje: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"🔌 Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"💥 Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = test_api_dosfases()
    if success:
        print("\n🎉 ¡Prueba API exitosa!")
    else:
        print("\n⚠️  Prueba API falló.")
