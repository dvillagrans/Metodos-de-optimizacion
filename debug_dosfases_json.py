import requests
import json
import traceback

def test_dosfases_debug():
    """Test Two-Phase method with detailed error debugging"""
    print("🔧 Debug - Método de Dos Fases JSON Serialization")
    print("=" * 70)
    
    # Test data
    test_data = {
        'c': '3,2,1',
        'A': '1,1,1\n2,1,-1\n1,2,1',
        'b': '6,4,8',
        'eq_constraints': '1,2',
        'minimize': '',  # False
        'track_iterations': 'on'  # True
    }
    
    url = 'http://localhost:5000/resolver/dosfases'
    
    print("📊 Datos de entrada:")
    print(json.dumps({
        'c': [3, 2, 1],
        'A': [[1, 1, 1], [2, 1, -1], [1, 2, 1]],
        'b': [6, 4, 8],
        'eq_constraints': [1, 2],
        'minimize': False,
        'track_iterations': True
    }, indent=2))
    print()
    
    try:
        response = requests.post(url, data=test_data, timeout=30)
        print(f"📡 Código de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Respuesta exitosa!")
            # Try to parse as HTML or text first
            content = response.text
            print("📄 Tipo de contenido:", response.headers.get('content-type', 'unknown'))
            
            if 'text/html' in response.headers.get('content-type', ''):
                # Look for error messages in HTML
                if 'Error inesperado:' in content:
                    start = content.find('Error inesperado:')
                    end = content.find('<', start)
                    if end == -1:
                        end = start + 200
                    error_msg = content[start:end]
                    print(f"🚨 Error encontrado en HTML: {error_msg}")
                else:
                    print("✅ HTML response appears successful")
            
        else:
            print(f"❌ Error en la respuesta: {response.status_code}")
            print(f"📝 Contenido de error: {response.text[:500]}")
            
    except requests.exceptions.RequestException as e:
        print(f"🔌 Error de conexión: {e}")
    except Exception as e:
        print(f"💥 Error inesperado: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_dosfases_debug()
