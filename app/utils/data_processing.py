"""
Módulo para procesamiento de datos y manejo de archivos.
"""

import json
import os
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Ruta al archivo casos.json
CASOS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'manim_anim', 'casos.json')


def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    
    # Handle numpy scalars (including specific types like int64)
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    # Handle Python built-in types with nested numpy
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    # Check if it's any numpy type we missed
    elif hasattr(obj, 'dtype') and 'numpy' in str(type(obj)):
        if obj.ndim == 0:            
            return obj.item()
        else:
            return obj.tolist()
    # Handle any remaining numpy types by checking the type name
    elif 'numpy' in str(type(obj)) or 'int64' in str(type(obj)):
        try:
            return obj.item() if hasattr(obj, 'item') else obj
        except (ValueError, TypeError):
            return str(obj)
    return obj


def ensure_casos_file():
    """Ensure the casos.json file exists"""
    os.makedirs(os.path.dirname(CASOS_PATH), exist_ok=True)
    if not os.path.exists(CASOS_PATH):
        with open(CASOS_PATH, 'w') as f:
            json.dump([], f)


def load_casos():
    """Load examples from the casos.json file"""
    ensure_casos_file()
    try:
        with open(CASOS_PATH, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If file is corrupted, return empty list
        return []


def save_casos(casos):
    """Save examples to the casos.json file"""
    ensure_casos_file()
    with open(CASOS_PATH, 'w') as f:
        json.dump(casos, f, indent=4)


def _to_list(x):
    """Convierte numpy arrays u objetos normales a list."""
    return x.tolist() if hasattr(x, "tolist") else x
