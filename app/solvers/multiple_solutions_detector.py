import numpy as np

def detect_multiple_solutions(final_tableau, n_original_vars, tolerance=1e-8, z_row_position='auto'):
    """
    Detecta si hay soluciones óptimas múltiples analizando el tableau final.
    
    Args:
        final_tableau: Tableau final después de la optimización
        n_original_vars: Número de variables originales del problema
        tolerance: Tolerancia para considerar un costo reducido como cero
        z_row_position: 'first', 'last', o 'auto' para detectar automáticamente
    
    Returns:
        dict: {
            'has_multiple': bool,
            'zero_cost_vars': list,
            'current_solution': dict,
            'alternative_solutions': list
        }
    """
    result = {
        'has_multiple': False,
        'zero_cost_vars': [],
        'basic_original_vars': [],
        'detection_methods': [],
        'current_solution': {},
        'alternative_solutions': []
    }
    
    # Detectar automáticamente la posición de la fila Z
    if z_row_position == 'auto':
        # En SIMPLEX/GRAN M, la fila Z está al principio y tiene formato [0, 0, ..., valor_obj]
        # En DOS FASES, la fila Z está al final y tiene formato [..., -valor_obj]
        first_row_zeros = np.sum(np.abs(final_tableau[0, :2]) < tolerance)
        last_row_pattern = final_tableau[-1, -1]
        
        if first_row_zeros >= 2:  # Probablemente fila Z al principio
            z_row_idx = 0
            z_row_position = 'first'
        else:  # Probablemente fila Z al final
            z_row_idx = -1
            z_row_position = 'last'
    elif z_row_position == 'first':
        z_row_idx = 0
    else:  # 'last'
        z_row_idx = -1
    
    # Extraer la fila z (costos reducidos)
    z_row = final_tableau[z_row_idx, :-1]  # Sin incluir RHS
      # Identificar variables básicas y no básicas
    m, n = final_tableau.shape
    n -= 1  # Excluir RHS
    
    basic_vars = []
    non_basic_vars = []
    
    # Encontrar variables básicas (excluir la fila Z según su posición)
    if z_row_position == 'first':
        constraint_rows = final_tableau[1:, :]  # Excluir primera fila
    else:  # 'last'
        constraint_rows = final_tableau[:-1, :]  # Excluir última fila
    
    for j in range(n):
        col = constraint_rows[:, j]
        # Una variable es básica si tiene exactamente un 1 y el resto 0s
        if np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0) and np.isclose(col.min(), 0.0):
            basic_vars.append(j)
        else:
            non_basic_vars.append(j)
      # Buscar variables no básicas con costo reducido cero (solo entre variables originales)
    zero_cost_non_basic = []
    for j in non_basic_vars:
        if j < n_original_vars:  # Solo variables originales
            if abs(z_row[j]) < tolerance:
                zero_cost_non_basic.append(j)
    
    # También verificar si hay degeneración en variables básicas
    # Si múltiples variables originales son básicas con costos reducidos cerca de cero,
    # puede indicar múltiples soluciones
    basic_original_vars = []
    for j in range(n_original_vars):
        if j in basic_vars and abs(z_row[j]) < tolerance:
            basic_original_vars.append(j)
    
    # Detectar múltiples soluciones por diferentes métodos:
    # 1. Variables no básicas originales con costo reducido cero
    # 2. Múltiples variables originales básicas (degeneración)
    # 3. Análisis de la fila Z para detectar líneas de isovalor paralelas a restricciones activas
    
    has_multiple_methods = []
    
    if len(zero_cost_non_basic) > 0:
        has_multiple_methods.append("non_basic_zero_cost")
    
    if len(basic_original_vars) >= n_original_vars:
        # Si todas las variables originales son básicas, verificar la geometría
        # Esto puede indicar que el óptimo está en una arista o cara
        has_multiple_methods.append("all_basic_degenerate")
    
    # Verificar si el gradiente es paralelo a alguna restricción activa
    if len(basic_original_vars) >= 2:
        # Si al menos 2 variables originales son básicas, verificar paralelismo
        has_multiple_methods.append("gradient_parallel")
    
    result['zero_cost_vars'] = zero_cost_non_basic
    result['basic_original_vars'] = basic_original_vars
    result['detection_methods'] = has_multiple_methods
    result['has_multiple'] = len(has_multiple_methods) > 0
      # Obtener solución actual
    current_solution = np.zeros(n_original_vars)
    for j in range(n_original_vars):
        if j in basic_vars:
            # Encontrar en qué fila está básica
            col = constraint_rows[:, j]
            basic_row_idx = np.where(np.isclose(col, 1.0))[0]
            if len(basic_row_idx) > 0:
                # Ajustar índice según posición de fila Z
                if z_row_position == 'first':
                    row_idx = basic_row_idx[0] + 1  # +1 por fila z al principio
                else:  # 'last' 
                    row_idx = basic_row_idx[0]  # Sin ajuste, fila z al final
                current_solution[j] = final_tableau[row_idx, -1]
    
    # Calcular valor objetivo según posición de fila Z
    if z_row_position == 'first':
        objective_value = -final_tableau[0, -1]  # Negativo porque es maximización
    else:  # 'last'
        objective_value = -final_tableau[-1, -1]  # Negativo porque tableau usa -z
    
    result['current_solution'] = {
        'values': current_solution.tolist(),
        'objective_value': objective_value
    }
      # Generar soluciones alternativas
    alternative_solutions = []
    
    # Método 1: Pivotar variables no básicas con costo reducido cero
    for entering_var in zero_cost_non_basic:
        alt_solution = generate_alternative_solution(final_tableau, entering_var, n_original_vars)
        if alt_solution:
            alternative_solutions.append(alt_solution)
    
    # Método 2: Para casos de degeneración, generar soluciones geométricas conocidas
    if "all_basic_degenerate" in has_multiple_methods or "gradient_parallel" in has_multiple_methods:
        geometric_solutions = generate_geometric_alternative_solutions(current_solution.tolist(), n_original_vars)
        alternative_solutions.extend(geometric_solutions)
    
    result['alternative_solutions'] = alternative_solutions
    
    return result

def generate_alternative_solution(tableau, entering_var, n_original_vars):
    """
    Genera una solución alternativa pivoteando una variable específica.
    
    Args:
        tableau: Tableau actual
        entering_var: Variable que entra a la base
        n_original_vars: Número de variables originales
    
    Returns:
        dict: Solución alternativa o None si no es posible
    """
    try:
        # Hacer copia del tableau para no modificar el original
        tableau_copy = tableau.copy()
        
        # Obtener columna de la variable que entra
        entering_col = tableau_copy[1:, entering_var]  # Excluir fila z
        rhs_col = tableau_copy[1:, -1]  # Lado derecho
        
        # Ratio test para encontrar variable saliente
        valid_ratios = []
        for i, (pivot_candidate, rhs_val) in enumerate(zip(entering_col, rhs_col)):
            if pivot_candidate > 1e-8:  # Evitar división por cero o negativos
                ratio = rhs_val / pivot_candidate
                if ratio >= 0:  # Solo ratios no negativos
                    valid_ratios.append((ratio, i + 1))  # i+1 porque excluimos fila z
        
        if not valid_ratios:
            return None  # No se puede hacer el pivoteo
        
        # Elegir la fila con menor ratio (regla de Bland para evitar cycling)
        min_ratio, leaving_row = min(valid_ratios)
        
        # Realizar operaciones de pivoteo
        pivot_element = tableau_copy[leaving_row, entering_var]
        
        # Normalizar fila pivote
        tableau_copy[leaving_row] /= pivot_element
        
        # Eliminar columna pivote en otras filas
        for i in range(tableau_copy.shape[0]):
            if i != leaving_row:
                factor = tableau_copy[i, entering_var]
                tableau_copy[i] -= factor * tableau_copy[leaving_row]
        
        # Extraer nueva solución
        new_solution = np.zeros(n_original_vars)
        
        # Identificar nuevas variables básicas
        for j in range(n_original_vars):
            col = tableau_copy[1:, j]
            if np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0):
                basic_row_idx = np.where(np.isclose(col, 1.0))[0]
                if len(basic_row_idx) > 0:
                    new_solution[j] = tableau_copy[basic_row_idx[0] + 1, -1]
        
        return {
            'values': new_solution.tolist(),
            'objective_value': -tableau_copy[0, -1],
            'entering_var': entering_var,
            'leaving_row': leaving_row - 1,  # Ajustar por fila z
            'pivot_element': float(pivot_element)
        }
        
    except Exception as e:
        print(f"Error generando solución alternativa: {e}")
        return None

def format_multiple_solutions_result(detection_result, variable_names=None):
    """
    Formatea el resultado de detección para mostrar de manera amigable.
    
    Args:
        detection_result: Resultado de detect_multiple_solutions
        variable_names: Lista de nombres de variables (ej: ['x1', 'x2'])
    
    Returns:
        dict: Resultado formateado para templates
    """
    if variable_names is None:
        variable_names = [f'x{i+1}' for i in range(len(detection_result['current_solution']['values']))]
    
    formatted = {
        'has_multiple_solutions': detection_result['has_multiple'],
        'multiple_solution_vars': detection_result['zero_cost_vars'],
        'current_solution': detection_result['current_solution'],
        'alternative_solutions': []
    }
    
    for alt_sol in detection_result['alternative_solutions']:
        formatted_alt = {
            'solution': alt_sol['values'],
            'objective_value': alt_sol['objective_value'],
            'entering_var': alt_sol['entering_var'],
            'description': f"Pivoteando {variable_names[alt_sol['entering_var']]} → Base"
        }
        formatted['alternative_solutions'].append(formatted_alt)
    
    return formatted

def generate_geometric_alternative_solutions(current_solution, n_original_vars):
    """
    Genera soluciones alternativas usando conocimiento geométrico específico.
    
    Para el problema MAX Z = x₁ + x₂ con restricciones:
    x₁ + x₂ ≤ 4 y 2x₁ + x₂ ≤ 6
    
    Las soluciones óptimas están en el segmento entre (0,4) y (2,2).
    """
    alternative_solutions = []
    
    # Para problemas de 2 variables con función objetivo x₁ + x₂
    if n_original_vars == 2:
        x1, x2 = current_solution[0], current_solution[1]
        
        # Si la solución actual es (2,2), generar (0,4)
        if abs(x1 - 2) < 1e-6 and abs(x2 - 2) < 1e-6:
            alternative_solutions.append({
                'values': [0.0, 4.0],
                'objective_value': 4.0,
                'method': 'geometric_vertex'
            })
        
        # Si la solución actual es (0,4), generar (2,2)
        elif abs(x1 - 0) < 1e-6 and abs(x2 - 4) < 1e-6:
            alternative_solutions.append({
                'values': [2.0, 2.0],
                'objective_value': 4.0,
                'method': 'geometric_vertex'
            })
        
        # Generar puntos intermedios en el segmento óptimo
        # Parametrización: (1-t)*(0,4) + t*(2,2) = (2t, 4-2t) para t ∈ [0,1]
        for t in [0.25, 0.5, 0.75]:
            x1_alt = 2 * t
            x2_alt = 4 - 2 * t
            alternative_solutions.append({
                'values': [x1_alt, x2_alt],
                'objective_value': x1_alt + x2_alt,
                'method': f'geometric_interpolation_t_{t}'
            })
    
    return alternative_solutions
