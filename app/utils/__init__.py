"""
Módulo de utilidades de la aplicación.
Contiene funciones helper y utilitarios comunes.
"""

from .data_processing import convert_numpy_types, ensure_casos_file, load_casos, save_casos, _to_list
from .validation import validate_dimensions, validate_form_data
from .multiple_solutions import (
    detect_multiple_solutions, 
    format_multiple_solutions_result,
    generate_alternative_solutions,
    generate_alternative_solutions_from_slack,
    generate_solutions_from_equal_coefficients
)

__all__ = [
    'convert_numpy_types',
    '_to_list',
    'ensure_casos_file', 
    'load_casos',
    'save_casos',
    'validate_dimensions',
    'validate_form_data',
    'detect_multiple_solutions',
    'format_multiple_solutions_result',
    'generate_alternative_solutions',
    'generate_alternative_solutions_from_slack',
    'generate_solutions_from_equal_coefficients'
]
