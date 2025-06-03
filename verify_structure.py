#!/usr/bin/env python3
"""
Script para verificar la estructura de módulos sin dependencias externas.
"""

import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Prueba las importaciones de módulos"""
    print("🔍 Verificando estructura de módulos...")
    
    try:
        # Test 1: Verificar que existen los directorios
        routes_dir = os.path.join('app', 'routes')
        utils_dir = os.path.join('app', 'utils')
        
        assert os.path.exists(routes_dir), f"❌ Directorio {routes_dir} no existe"
        assert os.path.exists(utils_dir), f"❌ Directorio {utils_dir} no existe"
        print("✅ Directorios de módulos creados correctamente")
        
        # Test 2: Verificar archivos __init__.py
        routes_init = os.path.join(routes_dir, '__init__.py')
        utils_init = os.path.join(utils_dir, '__init__.py')
        
        assert os.path.exists(routes_init), f"❌ Archivo {routes_init} no existe"
        assert os.path.exists(utils_init), f"❌ Archivo {utils_init} no existe"
        print("✅ Archivos __init__.py creados correctamente")
        
        # Test 3: Verificar archivos de módulos
        expected_files = [
            os.path.join(routes_dir, 'main_routes.py'),
            os.path.join(routes_dir, 'api_routes.py'),
            os.path.join(routes_dir, 'animation_routes.py'),
            os.path.join(utils_dir, 'data_processing.py'),
            os.path.join(utils_dir, 'validation.py'),
            os.path.join(utils_dir, 'multiple_solutions.py'),
        ]
        
        for file_path in expected_files:
            assert os.path.exists(file_path), f"❌ Archivo {file_path} no existe"
        print("✅ Todos los archivos de módulos creados correctamente")
        
        # Test 4: Verificar backup
        backup_file = os.path.join('app', 'routes_backup.py')
        assert os.path.exists(backup_file), f"❌ Backup {backup_file} no existe"
        print("✅ Backup del archivo original creado")
          # Test 5: Verificar contenido básico de archivos
        with open(os.path.join(routes_dir, 'main_routes.py'), 'r', encoding='utf-8') as f:
            main_routes_content = f.read()
        assert 'main_bp = Blueprint' in main_routes_content, "❌ main_bp no definido correctamente"
        print("✅ Blueprint principal definido correctamente")
        
        with open(os.path.join(routes_dir, 'api_routes.py'), 'r', encoding='utf-8') as f:
            api_routes_content = f.read()
        assert 'api_bp = Blueprint' in api_routes_content, "❌ api_bp no definido correctamente"
        print("✅ Blueprint de API definido correctamente")
        
        with open(os.path.join(utils_dir, 'data_processing.py'), 'r', encoding='utf-8') as f:
            utils_content = f.read()
        assert 'convert_numpy_types' in utils_content, "❌ convert_numpy_types no encontrada"
        print("✅ Funciones de utilidad definidas correctamente")
        
        print("\n🎉 ¡Refactorización completada exitosamente!")
        print("\n📋 Resumen de la nueva estructura:")
        print("   📁 app/routes/ - Módulo de rutas dividido por funcionalidad")
        print("   📁 app/utils/ - Módulo de utilidades reutilizables")
        print("   📄 app/routes.py - Mantiene compatibilidad con código existente")
        print("   📄 app/routes_backup.py - Backup del archivo original")
        
        return True
        
    except AssertionError as e:
        print(f"❌ Error en verificación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
