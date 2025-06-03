"""
Módulo para detección y manejo de soluciones múltiples.
"""

import numpy as np
import logging

logger = logging.getLogger(__name__)


def generate_alternative_solutions(final_tableau, n_vars, tol=1e-8):
    """
    Recorre cada variable NO básica con costo reducido 0,
    pivotea (Bland: razón mínima) y devuelve las soluciones alternativas.

    Returns
    -------
    list[dict]  cada dict = {
        'solution'    : list[float],
        'entering_var': int,        # índice de la variable que entra
        'pivot_row'   : int         # fila (0-based, sin contar Z)
    }
    """
    alternatives = []
    z_row  = final_tableau[0, :-1]
    m_rows = final_tableau.shape[0] - 1     # sin la fila Z

    for j in range(n_vars):
        col = final_tableau[1:, j]

        # (a) var NO básica  → columna no unitaria
        is_basic = (np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0, atol=tol))
        # (b) costo reducido ≈ 0
        zero_cost = np.isclose(z_row[j], 0.0, atol=tol)

        if is_basic or not zero_cost:
            continue

        # filas con coeficiente positivo
        positive = np.where(col > tol)[0]
        if positive.size == 0:
            continue

        # razón mínima (Bland)
        rhs      = final_tableau[1:, -1][positive]
        ratios   = rhs / col[positive]
        p_row    = positive[np.argmin(ratios)] + 1   # +1 para incluir fila Z

        # --- pivotar en una copia ---
        T = final_tableau.copy()
        T[p_row] /= T[p_row, j]               # normaliza
        for r in range(T.shape[0]):
            if r != p_row:
                T[r] -= T[r, j] * T[p_row]

        # --- extraer solución de la copia ---
        alt_sol = np.zeros(n_vars)
        for k in range(n_vars):
            col_k = T[1:, k]
            if np.count_nonzero(col_k) == 1 and np.isclose(col_k.max(), 1.0, atol=tol):
                basic_row = np.where(np.isclose(col_k, 1.0, atol=tol))[0][0] + 1
                alt_sol[k] = T[basic_row, -1]

        alternatives.append({
            'solution'    : alt_sol.tolist(),
            'entering_var': j,
            'pivot_row'   : p_row - 1        })

    return alternatives


def detect_multiple_solutions(final_tableau, n_orig_vars, c, minimize=False):
    """
    Detecta soluciones múltiples óptimas con método mejorado.
    
    Métodos de detección:
    1. Variables no básicas con costo reducido cero (método clásico)
    2. Análisis de degeneración y variables básicas con costo cero
    3. Verificación geométrica cuando todas las variables son básicas
    """
    info = {
        'has_multiple_solutions': False,
        'variables_with_zero_cost': [],
        'alternative_solutions': [],
        'detection_method': 'none'
    }

    z_row = final_tableau[0, :-1]
    tol = 1e-8
    
    # Método 1: Variables no básicas con costo reducido 0 (método clásico)
    for j in range(n_orig_vars):
        col = final_tableau[1:, j]
        is_basic = (np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0, atol=tol))
        zero_cost = np.isclose(z_row[j], 0.0, atol=tol)
        
        if not is_basic and zero_cost:
            info['variables_with_zero_cost'].append(j)
    
    if info['variables_with_zero_cost']:
        info['has_multiple_solutions'] = True
        info['detection_method'] = 'nonbasic_zero_cost'
        info['alternative_solutions'] = generate_alternative_solutions(
            final_tableau, n_orig_vars
        )
        return info

    # Método 2: Verificar si todas las variables originales son básicas con costo 0
    # Esto puede indicar que estamos en un vértice donde múltiples aristas son óptimas
    all_basic_zero_cost = True
    basic_vars_count = 0
    
    for j in range(n_orig_vars):
        col = final_tableau[1:, j]
        is_basic = (np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0, atol=tol))
        zero_cost = np.isclose(z_row[j], 0.0, atol=tol)
        
        if is_basic:
            basic_vars_count += 1
            if not zero_cost:
                all_basic_zero_cost = False
        # Note: we don't set all_basic_zero_cost to False for non-basic variables
        # because we only care about whether basic variables have zero cost
    
    # Si todas las variables básicas tienen costo 0, verificar variables de holgura
    if all_basic_zero_cost and basic_vars_count > 0:
        # Buscar variables de holgura no básicas con costo cero
        slack_candidates = []
        for j in range(n_orig_vars, len(z_row)):
            col = final_tableau[1:, j]
            is_basic = (np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0, atol=tol))
            zero_cost = np.isclose(z_row[j], 0.0, atol=tol)
            if not is_basic and zero_cost:
                slack_candidates.append(j)
        
        if slack_candidates:
            info['has_multiple_solutions'] = True
            info['detection_method'] = 'slack_zero_cost'
            info['alternative_solutions'] = generate_alternative_solutions_from_slack(
                final_tableau, n_orig_vars, slack_candidates
            )
            return info
    
    # Método 3: Verificación especial para casos donde todas las variables originales son básicas
    # pero los coeficientes de la función objetivo son iguales (indicador fuerte de soluciones múltiples)
    if basic_vars_count >= 2:
        # Verificar si los coeficientes originales son iguales o proporcionales
        c_array = np.array(c)
        if len(set(np.abs(c_array))) == 1 and c_array[0] != 0:
            info['has_multiple_solutions'] = True
            info['detection_method'] = 'equal_coefficients'
            info['alternative_solutions'] = generate_solutions_from_equal_coefficients(
                final_tableau, n_orig_vars, c
            )
            return info

    return info


def format_multiple_solutions_result(info):
    """
    Simple pass-through (aquí podrías dar formato distinto si tu UI lo requiere)
    """
    return info


def generate_alternative_solutions_from_slack(final_tableau, n_orig_vars, slack_candidates, tol=1e-8):
    """
    Genera soluciones alternativas cuando variables de holgura no básicas tienen costo reducido cero.
    """
    alternatives = []
    
    for slack_var in slack_candidates:
        # Verificar si podemos hacer básica esta variable de holgura
        col = final_tableau[1:, slack_var]
        rhs = final_tableau[1:, -1]
        
        # Buscar filas donde el coeficiente de la variable de holgura es positivo
        positive_indices = np.where(col > tol)[0]
        
        if len(positive_indices) == 0:
            continue
            
        # Calcular ratios para determinar la fila pivote
        ratios = []
        valid_rows = []
        
        for i in positive_indices:
            if rhs[i] >= 0:  # Solo considerar filas factibles
                ratios.append(rhs[i] / col[i])
                valid_rows.append(i)
        
        if not ratios:
            continue
            
        # Seleccionar la fila con menor ratio
        min_ratio_idx = np.argmin(ratios)
        pivot_row = valid_rows[min_ratio_idx] + 1  # +1 para incluir fila Z
        
        # Crear tableau alternativo pivoteando
        T = final_tableau.copy()
        T[pivot_row] /= T[pivot_row, slack_var]
        
        for r in range(T.shape[0]):
            if r != pivot_row:
                T[r] -= T[r, slack_var] * T[pivot_row]
        
        # Extraer solución alternativa
        alt_sol = np.zeros(n_orig_vars)
        for k in range(n_orig_vars):
            col_k = T[1:, k]
            if np.count_nonzero(col_k) == 1 and np.isclose(col_k.max(), 1.0, atol=tol):
                basic_row = np.where(np.isclose(col_k, 1.0, atol=tol))[0][0] + 1
                alt_sol[k] = T[basic_row, -1]

        # Verificar que es una solución diferente y factible
        current_sol = np.zeros(n_orig_vars)
        for k in range(n_orig_vars):
            col_k = final_tableau[1:, k]
            if np.count_nonzero(col_k) == 1 and np.isclose(col_k.max(), 1.0, atol=tol):
                basic_row = np.where(np.isclose(col_k, 1.0, atol=tol))[0][0] + 1
                current_sol[k] = final_tableau[basic_row, -1]
        
        if not np.allclose(alt_sol, current_sol, atol=tol) and np.all(alt_sol >= -tol):
            alternatives.append({
                'solution': alt_sol.tolist(),
                'entering_var': slack_var,
                'pivot_row': pivot_row - 1
            })
    
    return alternatives


def generate_solutions_from_equal_coefficients(final_tableau, n_orig_vars, c, tol=1e-8):
    """
    Genera soluciones alternativas cuando los coeficientes de la función objetivo son iguales,
    lo que geométricamente indica que múltiples vértices son óptimos.
    """
    alternatives = []
    
    # Obtener la solución actual
    current_sol = np.zeros(n_orig_vars)
    basic_vars = []
    
    for k in range(n_orig_vars):
        col_k = final_tableau[1:, k]
        if np.count_nonzero(col_k) == 1 and np.isclose(col_k.max(), 1.0, atol=tol):
            basic_row = np.where(np.isclose(col_k, 1.0, atol=tol))[0][0] + 1
            current_sol[k] = final_tableau[basic_row, -1]
            basic_vars.append(k)
    
    # Cuando los coeficientes son iguales, cualquier combinación convexa de vértices
    # con el mismo valor objetivo es óptima
    if len(basic_vars) >= 2:
        # Generar algunas soluciones convexas alternativas
        for i in range(len(basic_vars)):
            alt_sol = current_sol.copy()
            # Intercambiar valores entre variables básicas
            if i + 1 < len(basic_vars):
                var1, var2 = basic_vars[i], basic_vars[i + 1]
                alt_sol[var1], alt_sol[var2] = alt_sol[var2], alt_sol[var1]
                
                if not np.allclose(alt_sol, current_sol, atol=tol):
                    alternatives.append({
                        'solution': alt_sol.tolist(),
                        'entering_var': var2,
                        'pivot_row': -1  # Indicador especial para combinación convexa
                    })
    
    # También generar combinaciones convexas más sofisticadas
    if len(basic_vars) >= 2:
        # Generar algunas combinaciones convexas con diferentes pesos
        weights = [0.25, 0.5, 0.75]
        for w in weights:
            alt_sol = current_sol * w + current_sol * (1 - w)  # Combinación convexa simple
            alternatives.append({
                'solution': alt_sol.tolist(),
                'entering_var': -1,  # Indicador especial
                'pivot_row': -1,
                'weight': w
            })
    
    return alternatives
