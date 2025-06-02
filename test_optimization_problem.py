import requests
import json

def test_optimization_problem():
    """Test del problema de optimización específico"""
    print("🔧 Prueba del Problema de Optimización")
    print("=" * 50)
    print("MAX Z = 2x₁ + 3x₂ + 4x₃")
    print("s.a.")
    print("  x₁ + x₂ + x₃ ≤ 30     ← (1) desigualdad tipo ≤")
    print("  2x₁ + x₂     ≥ 40     ← (2) desigualdad tipo ≥")
    print("  3x₂ + 2x₃    ≤ 60     ← (3) desigualdad tipo ≤")
    print("  x₁, x₂, x₃   ≥ 0")
    print("=" * 50)
    
    # Configuración para método de Dos Fases
    # Para forma estándar necesitamos:
    # x₁ + x₂ + x₃ + s₁ = 30          (restricción 1 con variable de holgura)
    # 2x₁ + x₂ - s₂ + a₁ = 40         (restricción 2 con variable artificial)
    # 3x₂ + 2x₃ + s₃ = 60             (restricción 3 con variable de holgura)
    
    # Matriz A (coeficientes de las restricciones)
    # Considerando solo las variables originales x₁, x₂, x₃
    A_matrix = [
        [1, 1, 1],    # x₁ + x₂ + x₃ ≤ 30
        [2, 1, 0],    # 2x₁ + x₂ ≥ 40 
        [0, 3, 2]     # 3x₂ + 2x₃ ≤ 60
    ]
    
    # Vector c (coeficientes de la función objetivo)
    c_vector = [2, 3, 4]  # MAX Z = 2x₁ + 3x₂ + 4x₃
    
    # Vector b (lado derecho)
    b_vector = [30, 40, 60]
    
    # eq_constraints: restricciones que necesitan variables artificiales
    # En este caso, la restricción 2 (índice 1) tiene ≥, así que necesita artificial
    eq_constraints = [1]  # Restricción 2 (base 0)
    
    # Datos para el formulario web
    form_data = {
        'c': ','.join(map(str, c_vector)),
        'A': '\n'.join([','.join(map(str, row)) for row in A_matrix]),
        'b': ','.join(map(str, b_vector)),
        'eq_constraints': ','.join(map(str, eq_constraints)),
        'minimize': '',  # False (maximización)
        'track_iterations': 'on'  # True
    }
    
    print("\n📊 Configuración para Dos Fases:")
    print(f"c (función objetivo): {form_data['c']}")
    print(f"A (matriz restricciones):")
    for i, row in enumerate(A_matrix):
        print(f"  Restricción {i+1}: {row}")
    print(f"b (lado derecho): {form_data['b']}")
    print(f"eq_constraints (necesitan artificiales): {form_data['eq_constraints']}")
    print()
    
    # Test 1: Método de Dos Fases (formulario web)
    print("🧪 Probando método de Dos Fases (formulario web)...")
    url_dosfases = 'http://localhost:5000/resolver/dosfases'
    
    try:
        response = requests.post(url_dosfases, data=form_data, timeout=30)
        
        if response.status_code == 200:
            content = response.text
            
            if 'Error inesperado:' in content or 'Error en el método Dos Fases:' in content:
                # Extraer mensaje de error
                for error_type in ['Error inesperado:', 'Error en el método Dos Fases:']:
                    if error_type in content:
                        start = content.find(error_type)
                        end = content.find('<', start)
                        if end == -1:
                            end = start + 300
                        error_msg = content[start:end].strip()
                        print(f"❌ {error_msg}")
                        break
            else:
                print("✅ Dos Fases procesado exitosamente!")
                
                # Intentar extraer algunos resultados básicos del HTML
                if 'Solución óptima encontrada' in content:
                    print("🎯 Solución óptima encontrada")
                elif 'Solución:' in content:
                    print("🎯 Solución encontrada")
                
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Error en Dos Fases: {e}")
    
    # Test 2: API de Dos Fases
    print("\n🧪 Probando API de Dos Fases...")
    url_api = 'http://localhost:5000/api/resolver/dosfases'
    
    api_data = {
        'c': c_vector,
        'A': A_matrix,
        'b': b_vector,
        'eq_constraints': eq_constraints,
        'minimize': False,
        'track_iterations': True
    }
    
    try:
        response = requests.post(
            url_api, 
            json=api_data, 
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ API Dos Fases exitosa!")
                print(f"🎯 Solución: {result.get('solution', 'N/A')}")
                print(f"💰 Valor óptimo: {result.get('optimal_value', 'N/A')}")
                print(f"📊 Iteraciones: {len(result.get('tableau_history', []))}")
                print(f"✨ Éxito: {result.get('success', False)}")
                
                if result.get('has_multiple_solutions'):
                    print(f"🔀 Múltiples soluciones detectadas")
                    print(f"   Variables con costo reducido cero: {result.get('multiple_solution_vars', [])}")
                
            except json.JSONDecodeError:
                print("❌ Error: Respuesta API no es JSON válido")
        else:
            print(f"❌ Error API: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Error en API: {e}")
    
    # Test 3: Para comparar, también probemos Gran M
    print("\n🧪 Probando Gran M para comparación...")
    url_granm = 'http://localhost:5000/resolver/granm'
    
    granm_data = form_data.copy()
    granm_data['ge_constraints'] = '1'  # Restricción 2 es ≥
    granm_data['M'] = '1000'  # Valor de M grande
    
    try:
        response = requests.post(url_granm, data=granm_data, timeout=30)
        
        if response.status_code == 200:
            content = response.text
            
            if 'Error inesperado:' in content or 'Error en el método Gran M:' in content:
                print("❌ Error en Gran M")
            else:
                print("✅ Gran M procesado exitosamente!")
        else:
            print(f"❌ Error HTTP Gran M: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Error en Gran M: {e}")
    
    print("\n" + "=" * 50)
    print("📋 ANÁLISIS DEL PROBLEMA:")
    print("• Este problema tiene una restricción ≥ (restricción 2)")
    print("• El método de Dos Fases debería manejar esto correctamente")
    print("• La restricción 2x₁ + x₂ ≥ 40 requiere variable artificial")
    print("• Las otras restricciones solo necesitan variables de holgura")
    print("• Se espera una solución óptima factible para las tres variables")

if __name__ == "__main__":
    test_optimization_problem()
