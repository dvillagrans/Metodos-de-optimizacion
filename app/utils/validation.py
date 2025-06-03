"""
Módulo para validaciones de datos de entrada.
"""

from ..solvers import DimensionError


def validate_dimensions(A, b, c):
    """
    Valida que las dimensiones de las matrices sean consistentes.
    
    Args:
        A: Matriz de restricciones
        b: Vector de recursos
        c: Vector de coeficientes de la función objetivo
        
    Raises:
        DimensionError: Si las dimensiones no son consistentes
    """
    if len(A) != len(b):
        raise DimensionError(f"La matriz A tiene {len(A)} filas pero el vector b tiene {len(b)} elementos")
    
    if any(len(row) != len(c) for row in A):
        raise DimensionError(f"La matriz A debe tener {len(c)} columnas para coincidir con el vector c")


def validate_form_data(form_data):
    """
    Valida que los datos del formulario sean válidos.
    
    Args:
        form_data: Diccionario con los datos del formulario
        
    Returns:
        dict: Datos validados y procesados
        
    Raises:
        ValueError: Si los datos no son válidos
    """
    required_fields = ['c', 'A', 'b']
    for field in required_fields:
        if field not in form_data or not form_data[field].strip():
            raise ValueError(f"El campo '{field}' es requerido")
    
    # Procesar datos
    try:
        c = [float(x) for x in form_data['c'].split(',') if x.strip()]
        A_rows = form_data['A'].strip().split('\n')
        A = [[float(num) for num in row.split(',') if num.strip()] 
             for row in A_rows if row.strip()]
        b = [float(x) for x in form_data['b'].split(',') if x.strip()]
        
        # Validar que no estén vacíos
        if not c:
            raise ValueError("El vector de coeficientes c no puede estar vacío")
        if not A:
            raise ValueError("La matriz A no puede estar vacía")
        if not b:
            raise ValueError("El vector b no puede estar vacío")
            
        return {
            'c': c,
            'A': A,
            'b': b,
            'minimize': form_data.get('minimize', False),
            'track_iterations': form_data.get('track_iterations', False)
        }
        
    except ValueError as e:
        if "could not convert string to float" in str(e):
            raise ValueError("Todos los valores deben ser números válidos")
        raise
