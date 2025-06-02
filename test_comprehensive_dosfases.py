import requests
import json
import time

def test_comprehensive_dosfases():
    """Comprehensive test of Two-Phase method JSON serialization"""
    print("🔧 Prueba Comprehensiva - Método de Dos Fases")
    print("=" * 60)
    
    base_url = 'http://localhost:5000'
    
    # Test cases
    test_cases = [
        {
            'name': 'Caso básico con igualdades',
            'data': {
                'c': '3,2,1',
                'A': '1,1,1\n2,1,-1\n1,2,1',
                'b': '6,4,8',
                'eq_constraints': '1,2',
                'minimize': '',
                'track_iterations': 'on'
            }
        },
        {
            'name': 'Problema de maximización simple',
            'data': {
                'c': '2,3',
                'A': '1,2\n2,1',
                'b': '4,6',
                'eq_constraints': '',
                'minimize': '',
                'track_iterations': 'on'
            }
        },
        {
            'name': 'Problema de minimización',
            'data': {
                'c': '1,2,3',
                'A': '1,1,1\n2,1,3',
                'b': '6,10',
                'eq_constraints': '',
                'minimize': 'on',
                'track_iterations': 'on'
            }
        },
        {
            'name': 'Sin seguimiento de iteraciones',
            'data': {
                'c': '1,1',
                'A': '1,2\n2,1',
                'b': '3,3',
                'eq_constraints': '',
                'minimize': '',
                'track_iterations': ''
            }
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Caso {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            response = requests.post(
                f"{base_url}/resolver/dosfases", 
                data=test_case['data'], 
                timeout=30
            )
            
            if response.status_code == 200:
                content = response.text
                
                # Check for error messages
                if 'Error inesperado:' in content:
                    start = content.find('Error inesperado:')
                    end = content.find('<', start)
                    if end == -1:
                        end = start + 200
                    error_msg = content[start:end]
                    print(f"❌ Error: {error_msg}")
                    results.append(False)
                elif 'Error en el método Dos Fases:' in content:
                    start = content.find('Error en el método Dos Fases:')
                    end = content.find('<', start)
                    if end == -1:
                        end = start + 200
                    error_msg = content[start:end]
                    print(f"❌ Error del método: {error_msg}")
                    results.append(False)
                else:
                    print("✅ Procesado exitosamente")
                    results.append(True)
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"💥 Excepción: {e}")
            results.append(False)
        
        time.sleep(0.5)  # Small delay between requests
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS COMPREHENSIVAS:")
    passed = sum(results)
    total = len(results)
    
    for i, (test_case, result) in enumerate(zip(test_cases, results), 1):
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"  • Caso {i} ({test_case['name']}): {status}")
    
    print(f"\n🎯 Total: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El sistema está funcionando correctamente.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar los errores anteriores.")
    
    return passed == total

if __name__ == "__main__":
    test_comprehensive_dosfases()
