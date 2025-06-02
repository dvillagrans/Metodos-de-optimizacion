import requests
import json

def test_dosfases_api():
    """Test the Dos Fases API endpoint with the specific problem"""
    url = "http://localhost:5000/api/resolver/dosfases"
    
    # Problema específico del usuario
    data = {
        "c": [2, 3, 4],
        "A": [
            [1, 1, 1],   # x₁ + x₂ + x₃ ≤ 30
            [2, 1, 0],   # 2x₁ + x₂ ≥ 40  
            [0, 3, 2]    # 3x₂ + 2x₃ ≤ 60
        ],
        "b": [30, 40, 60],
        "eq_constraints": [],  # No hay restricciones de igualdad
        "track_iterations": True
    }
    
    print("🧪 PROBANDO API DOS FASES")
    print("=" * 40)
    print("Enviando problema:")
    print(f"  Función objetivo: MAX Z = 2x₁ + 3x₂ + 4x₃")
    print(f"  Restricciones:")
    print(f"    x₁ + x₂ + x₃ ≤ 30")
    print(f"    2x₁ + x₂ ≥ 40")
    print(f"    3x₂ + 2x₃ ≤ 60")
    print()
    
    try:
        response = requests.post(url, json=data, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response content type: {response.headers.get('content-type', 'Unknown')}")
        print(f"Response text (first 300 chars): {response.text[:300]}")
        print()
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("📊 RESPUESTA JSON:")
                print(f"  Status: {result.get('status', 'N/A')}")
                
                if 'solution' in result:
                    solution = result['solution']
                    print(f"  Solución: [{solution[0]:.3f}, {solution[1]:.3f}, {solution[2]:.3f}]")
                    print(f"  Valor óptimo: {result.get('optimal_value', 'N/A')}")
                    
                    # Verificación manual
                    x1, x2, x3 = solution
                    constraint1 = x1 + x2 + x3  # ≤ 30
                    constraint2 = 2*x1 + x2      # ≥ 40
                    constraint3 = 3*x2 + 2*x3    # ≤ 60
                    
                    print(f"  Verificación:")
                    print(f"    Restricción 1: {constraint1:.3f} ≤ 30 {'✓' if constraint1 <= 30.001 else '✗'}")
                    print(f"    Restricción 2: {constraint2:.3f} ≥ 40 {'✓' if constraint2 >= 39.999 else '✗'}")
                    print(f"    Restricción 3: {constraint3:.3f} ≤ 60 {'✓' if constraint3 <= 60.001 else '✗'}")
                    
                    if constraint2 < 39.999:
                        print("  🚨 CONFIRMADO: El bug del método Dos Fases existe también en la API")
                else:
                    print(f"  No se encontró solución")
                    print(f"  Mensaje: {result.get('message', 'N/A')}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing JSON: {e}")
                print(f"   Response text: {response.text}")
                
        else:
            print(f"❌ Error HTTP {response.status_code}")
            print(f"   Response text: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor")
        print("   Asegúrate de que la aplicación esté ejecutándose en localhost:5000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_dosfases_api()
