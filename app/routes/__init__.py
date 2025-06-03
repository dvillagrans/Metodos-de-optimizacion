"""
Módulo de rutas de la aplicación.
Contiene todos los blueprints organizados por funcionalidad.
"""

from .main_routes import main_bp
from .api_routes import api_bp

__all__ = ['main_bp', 'api_bp']
