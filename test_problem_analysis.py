import requests
import json

def test_problem_corrected():
    """Test del problema con configuración corregida"""
    print("🔧 Prueba Corregida del Problema de Optimización")
    print("=" * 55)
    print("MAX Z = 2x₁ + 3x₂ + 4x₃")
    print("s.a.")
    print("  x₁ + x₂ + x₃ ≤ 30     ← (1) desigualdad tipo ≤")
    print("  2x₁ + x₂     ≥ 40     ← (2) desigualdad tipo ≥")
    print("  3x₂ + 2x₃    ≤ 60     ← (3) desigualdad tipo ≤")
    print("  x₁, x₂, x₃   ≥ 0")
    print("=" * 55)
    
    # Para el método de Dos Fases, voy a convertir la restricción ≥ a forma estándar
    # La restricción 2x₁ + x₂ ≥ 40 se convierte en:
    # 2x₁ + x₂ - s₂ = 40 (donde s₂ ≥ 0 es la variable de exceso)
    # Pero como s₂ aparece con signo negativo, necesitamos variable artificial
    
    # Para simplificar el análisis, voy a probar diferentes configuraciones:
    
    print("\n🔍 ANÁLISIS DEL PROBLEMA:")
    print("1. Revisemos si el problema es factible manualmente:")
    print("   - Para x₃ = 30: satisface x₁ + x₂ + x₃ ≤ 30 → 0 + 0 + 30 = 30 ✓")
    print("   - Para x₃ = 30: restricción 2x₁ + x₂ ≥ 40 → 0 + 0 = 0 < 40 ✗")
    print("   - Conclusión: x₃ = 30, x₁ = x₂ = 0 NO es factible")
    print()
    
    print("2. Busquemos una solución factible:")
    print("   - Si x₁ = 20, x₂ = 0, x₃ = 0:")
    print("     * x₁ + x₂ + x₃ = 20 ≤ 30 ✓")
    print("     * 2x₁ + x₂ = 40 ≥ 40 ✓") 
    print("     * 3x₂ + 2x₃ = 0 ≤ 60 ✓")
    print("     * Z = 2(20) + 3(0) + 4(0) = 40")
    print()
    
    print("   - Si x₁ = 0, x₂ = 40, x₃ = 0:")
    print("     * x₁ + x₂ + x₃ = 40 > 30 ✗")
    print("     * No es factible")
    print()
    
    print("   - Probemos x₁ = 10, x₂ = 20, x₃ = 0:")
    print("     * x₁ + x₂ + x₃ = 30 ≤ 30 ✓")
    print("     * 2x₁ + x₂ = 40 ≥ 40 ✓")
    print("     * 3x₂ + 2x₃ = 60 ≤ 60 ✓") 
    print("     * Z = 2(10) + 3(20) + 4(0) = 80")
    print()
    
    # Ahora voy a probar con diferentes configuraciones para ver si puedo obtener el resultado correcto
    
    # Configuración 1: Problema original
    print("🧪 Configuración 1: Problema original")
    test_config_1 = {
        'c': '2,3,4',
        'A': '1,1,1\n2,1,0\n0,3,2',
        'b': '30,40,60',
        'eq_constraints': '1',  # Restricción 2 necesita artificial
        'minimize': '',
        'track_iterations': 'on'
    }
    
    test_configuration("Original", test_config_1)
    
    # Configuración 2: Convertir ≥ a ≤ multiplicando por -1
    print("\n🧪 Configuración 2: Convertir 2x₁ + x₂ ≥ 40 a -2x₁ - x₂ ≤ -40")
    test_config_2 = {
        'c': '2,3,4',
        'A': '1,1,1\n-2,-1,0\n0,3,2',  # Segunda fila multiplicada por -1
        'b': '30,-40,60',                # Segunda componente multiplicada por -1
        'eq_constraints': '',             # Ahora todas son ≤
        'minimize': '',
        'track_iterations': 'on'
    }
    
    test_configuration("Convertida a ≤", test_config_2)
    
    # Configuración 3: Usar todas como igualdades para Dos Fases
    print("\n🧪 Configuración 3: Tratar todas como igualdades")
    test_config_3 = {
        'c': '2,3,4',
        'A': '1,1,1\n2,1,0\n0,3,2',
        'b': '30,40,60',
        'eq_constraints': '0,1,2',  # Todas las restricciones como igualdades
        'minimize': '',
        'track_iterations': 'on'
    }
    
    test_configuration("Todas igualdades", test_config_3)

def test_configuration(name, config):
    """Test una configuración específica"""
    print(f"   Probando: {name}")
    
    url = 'http://localhost:5000/api/resolver/dosfases'
    
    # Convertir formato de formulario a API
    api_data = {
        'c': [float(x) for x in config['c'].split(',')],
        'A': [[float(x) for x in row.split(',')] for row in config['A'].split('\n')],
        'b': [float(x) for x in config['b'].split(',')],
        'eq_constraints': [int(x) for x in config['eq_constraints'].split(',')] if config['eq_constraints'] else [],
        'minimize': False,
        'track_iterations': True
    }
    
    try:
        response = requests.post(
            url, 
            json=api_data, 
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('success'):
                    print(f"   ✅ Éxito: {result.get('solution', 'N/A')}, Z = {result.get('optimal_value', 'N/A')}")
                else:
                    print(f"   ⚠️ Procesado pero no exitoso: {result.get('solution', 'N/A')}")
            except json.JSONDecodeError:
                print("   ❌ Error JSON")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   💥 Error: {e}")

if __name__ == "__main__":
    test_problem_corrected()
