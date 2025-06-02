import requests
import json

def test_multiple_solutions_problem():
    """
    Prueba el problema clásico de soluciones múltiples:
    MAX Z = x₁ + x₂
    s.a.
        x₁ + x₂ ≤ 4
        2x₁ + x₂ ≤ 6
        x₁, x₂ ≥ 0
    
    Este problema tiene infinitas soluciones óptimas entre (2,2) y (3,1).
    """
    
    # Datos del problema
    problem_data = {
        'c': '1,1',  # Función objetivo: x1 + x2
        'A': '1,1\n2,1',  # Restricciones: x1+x2≤4, 2x1+x2≤6
        'b': '4,6',  # Lados derechos
        'minimize': False,  # Maximizar
        'track_iterations': True  # Para ver el tableau final
    }
    
    base_url = 'http://localhost:5000'
    
    print("🧮 Probando detección de soluciones múltiples...")
    print(f"Problema: MAX Z = x₁ + x₂")
    print(f"s.a.    x₁ + x₂ ≤ 4")
    print(f"        2x₁ + x₂ ≤ 6")
    print(f"        x₁, x₂ ≥ 0")
    print("\n" + "="*50)
    
    # Probar los tres métodos
    methods = [
        ('Simplex', f'{base_url}/resolver/simplex'),
        ('Gran M', f'{base_url}/resolver/granm'),
        ('Dos Fases', f'{base_url}/resolver/dosfases')
    ]
    
    for method_name, url in methods:
        print(f"\n🔍 Probando método: {method_name}")
        print("-" * 30)
        
        try:
            # Preparar datos específicos para cada método
            data = problem_data.copy()
            
            if method_name == 'Gran M':
                data['eq_constraints'] = ''
                data['ge_constraints'] = ''
                data['M'] = '1000000'
            elif method_name == 'Dos Fases':
                data['eq_constraints'] = ''
                data['ge_constraints'] = ''
            
            # Enviar solicitud
            response = requests.post(url, data=data)
            
            if response.status_code != 200:
                print(f"❌ Error HTTP {response.status_code}")
                continue
            
            # Buscar información de soluciones múltiples en la respuesta HTML
            html_content = response.text
            
            # Verificar si se detectaron soluciones múltiples
            if 'soluciones óptimas múltiples' in html_content.lower():
                print("✅ ¡Soluciones múltiples detectadas!")
                
                # Extraer más información si está disponible
                if 'Variables candidatas' in html_content:
                    print("📋 Variables candidatas encontradas")
                
                if 'Soluciones alternativas' in html_content:
                    print("🔄 Soluciones alternativas generadas")
                    
            else:
                print("❌ No se detectaron soluciones múltiples")
                
                # Verificar si al menos se obtuvo una solución
                if 'Solución' in html_content and 'Valor Óptimo' in html_content:
                    print("ℹ️  Se obtuvo una solución única")
                else:
                    print("⚠️  No se obtuvo ninguna solución")
                    
        except requests.exceptions.ConnectionError:
            print(f"❌ Error: No se pudo conectar al servidor en {url}")
            print("   Asegúrate de que el servidor esté ejecutándose")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
    
    print("\n" + "="*50)
    print("📊 Análisis teórico del problema:")
    print("   - Vértices factibles: (0,0), (0,4), (2,2), (3,1), (3,0)")
    print("   - Soluciones óptimas: Segmento de (2,2) a (3,1)")
    print("   - Valor óptimo: Z = 4")
    print("   - Detección: Costo reducido = 0 para variable no básica")

def test_with_api():
    """Prueba usando la API directamente para obtener resultados JSON"""
    
    problem_data = {
        'c': [1, 1],
        'A': [[1, 1], [2, 1]],
        'b': [4, 6],
        'minimize': False,
        'track_iterations': True
    }
    
    base_url = 'http://localhost:5000/api'
    
    print("\n🔧 Probando con API JSON...")
    print("-" * 30)
    
    methods = [
        ('Simplex', f'{base_url}/resolver/simplex'),
        ('Gran M', f'{base_url}/resolver/granm'),
        ('Dos Fases', f'{base_url}/resolver/dosfases')
    ]
    
    for method_name, url in methods:
        try:
            response = requests.post(url, json=problem_data)
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"\n📈 {method_name}:")
                print(f"   Solución: {result.get('solution', 'N/A')}")
                print(f"   Valor óptimo: {result.get('optimal_value', 'N/A')}")
                print(f"   Soluciones múltiples: {result.get('has_multiple_solutions', False)}")
                
                if result.get('alternative_solutions'):
                    print(f"   Alternativas: {len(result['alternative_solutions'])}")
                    for i, alt in enumerate(result['alternative_solutions']):
                        print(f"     Alt {i+1}: {alt.get('solution', 'N/A')}")
                        
            else:
                print(f"❌ {method_name}: Error HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {method_name}: Error {e}")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de detección de soluciones múltiples")
    print("="*60)
    
    # Probar con interfaz web
    test_multiple_solutions_problem()
    
    # Probar con API
    test_with_api()
    
    print("\n✨ Pruebas completadas")
