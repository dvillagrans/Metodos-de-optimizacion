"""
Módulo principal de rutas - Punto de entrada para todos los blueprints.
Este archivo mantiene la compatibilidad con el código existente.
"""

# Importar todos los blueprints de los módulos organizados
from .routes.main_routes import main_bp
from .routes.api_routes import api_bp  
from .routes.animation_routes import animation_bp

# Importar funciones comunes que se usan desde otros archivos
from .utils.multiple_solutions import detect_multiple_solutions, generate_alternative_solutions

# Para mantener compatibilidad con código existente
bp = main_bp

# Exportar todos los blueprints y funciones
__all__ = ['main_bp', 'api_bp', 'animation_bp', 'bp', 'detect_multiple_solutions', 'generate_alternative_solutions']
