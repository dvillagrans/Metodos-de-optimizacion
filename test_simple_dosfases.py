import requests
import json

def test_simple_problem():
    """Test con un problema más simple para verificar el método de Dos Fases"""
    print("🧪 PRUEBA CON PROBLEMA SIMPLE")
    print("=" * 40)
    
    # Problema simple sin restricciones ≥
    print("Problema 1: Solo restricciones ≤")
    print("MAX Z = x₁ + x₂")
    print("s.a. x₁ + x₂ ≤ 3")
    print("     x₁, x₂ ≥ 0")
    
    test_data_1 = {
        'c': [1, 1],
        'A': [[1, 1]],
        'b': [3],
        'eq_constraints': [],
        'minimize': False,
        'track_iterations': True
    }
    
    print("Resultado esperado: x₁=3, x₂=0 o x₁=0, x₂=3 o cualquier combinación con Z=3")
    test_api("Problema simple ≤", test_data_1)
    
    print("\n" + "-" * 40)
    
    # Problema con una igualdad
    print("\nProblema 2: Con una igualdad")
    print("MAX Z = x₁ + x₂")
    print("s.a. x₁ + x₂ = 3")
    print("     x₁, x₂ ≥ 0")
    
    test_data_2 = {
        'c': [1, 1],
        'A': [[1, 1]],
        'b': [3],
        'eq_constraints': [0],  # Primera restricción es igualdad
        'minimize': False,
        'track_iterations': True
    }
    
    print("Resultado esperado: x₁=3, x₂=0 o x₁=0, x₂=3 con Z=3")
    test_api("Problema con igualdad", test_data_2)
    
    print("\n" + "-" * 40)
    
    # Problema con restricción ≥ marcada como igualdad (esto puede ser el problema)
    print("\nProblema 3: Con restricción ≥ simulada")
    print("MAX Z = x₁ + x₂")
    print("s.a. x₁ + x₂ ≥ 2")
    print("     x₁ + x₂ ≤ 4")
    print("     x₁, x₂ ≥ 0")
    
    test_data_3 = {
        'c': [1, 1],
        'A': [
            [1, 1],    # x₁ + x₂ ≥ 2 (será eq_constraints)
            [1, 1]     # x₁ + x₂ ≤ 4
        ],
        'b': [2, 4],
        'eq_constraints': [0],  # Primera restricción marcada como "igualdad" (≥)
        'minimize': False,
        'track_iterations': True
    }
    
    print("Resultado esperado: x₁=4, x₂=0 o x₁=0, x₂=4 con Z=4")
    test_api("Problema con ≥", test_data_3)
    
    print("\n" + "=" * 40)
    print("🔍 ANÁLISIS:")
    print("Si el problema 3 no funciona correctamente, entonces")
    print("hay un bug en cómo el solver maneja las restricciones ≥")

def test_api(name, data):
    """Test una configuración con la API"""
    url = 'http://localhost:5000/api/resolver/dosfases'
    
    try:
        response = requests.post(
            url, 
            json=data, 
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            success = result.get('success', False)
            solution = result.get('solution', [])
            optimal_value = result.get('optimal_value', 'N/A')
            
            print(f"  {name}:")
            print(f"    Estado: {'✅ Exitoso' if success else '⚠️ No exitoso'}")
            print(f"    Solución: {solution}")
            print(f"    Valor óptimo: {optimal_value}")
            
            # Verificar factibilidad para el problema original
            if len(solution) >= 2 and len(data['A'][0]) >= 2:
                print(f"    Verificación:")
                for i, (constraint, b_val) in enumerate(zip(data['A'], data['b'])):
                    if len(constraint) >= 2:
                        lhs = sum(constraint[j] * solution[j] for j in range(min(len(constraint), len(solution))))
                        if i in data.get('eq_constraints', []):
                            print(f"      Restricción {i+1}: {lhs:.3f} = {b_val} ({'✓' if abs(lhs - b_val) < 0.001 else '✗'})")
                        else:
                            print(f"      Restricción {i+1}: {lhs:.3f} ≤ {b_val} ({'✓' if lhs <= b_val + 0.001 else '✗'})")
        else:
            print(f"  {name}: ❌ Error HTTP {response.status_code}")
            
    except Exception as e:
        print(f"  {name}: 💥 Error {e}")

if __name__ == "__main__":
    test_simple_problem()
