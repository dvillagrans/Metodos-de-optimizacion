import numpy as np

def two_phase_simplex_corrected(c, A, b, eq_constraints=None, ge_constraints=None, minimize=False):
    """
    Solver de dos fases corregido para el problema específico.
    """
    c = np.array(c, dtype=float)
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float)
    
    if eq_constraints is None:
        eq_constraints = []
    if ge_constraints is None:
        ge_constraints = []
    
    m, n = A.shape
    
    print(f"Problema inicial:")
    print(f"c = {c}")
    print(f"A = \n{A}")
    print(f"b = {b}")
    print(f"Minimizar: {minimize}")
    print(f"Restricciones >=: {ge_constraints}")
    
    # PASO 1: Convertir a forma estándar
    A_std = A.copy()
    b_std = b.copy()
    
    # Convertir >= a <= multiplicando por -1
    for i in ge_constraints:
        A_std[i] = -A_std[i]
        b_std[i] = -b_std[i]
    
    print(f"\nDespués de convertir >= a <=:")
    print(f"A_std = \n{A_std}")
    print(f"b_std = {b_std}")
    
    # PASO 2: Agregar variables de holgura
    A_with_slack = np.hstack([A_std, np.eye(m)])
    
    print(f"\nCon variables de holgura:")
    print(f"A_with_slack = \n{A_with_slack}")
    
    # PASO 3: Verificar si necesitamos variables artificiales
    need_artificial = np.any(b_std < 0) or len(eq_constraints) > 0
    
    if not need_artificial:
        print("\nNo se necesitan variables artificiales")
        return solve_standard_simplex(c, A_with_slack, b_std, minimize)
    
    print(f"\nSe necesitan variables artificiales para restricciones con b < 0")
    
    # PASO 4: FASE I - Agregar variables artificiales
    artificial_indices = []
    for i in range(m):
        if b_std[i] < 0 or i in eq_constraints:
            artificial_indices.append(i)
    
    num_artificial = len(artificial_indices)
    print(f"Variables artificiales necesarias en restricciones: {artificial_indices}")
    
    # Crear matriz con variables artificiales
    A_artificial = np.zeros((m, num_artificial))
    for idx, row in enumerate(artificial_indices):
        A_artificial[row, idx] = 1
    
    A_phase1 = np.hstack([A_with_slack, A_artificial])
    
    print(f"\nMatriz Fase I:")
    print(f"A_phase1 = \n{A_phase1}")
    print(f"b_std = {b_std}")
    
    # Objetivo Fase I: minimizar suma de variables artificiales
    c_phase1 = np.zeros(A_phase1.shape[1])
    for i in range(num_artificial):
        c_phase1[n + m + i] = 1  # Coeficientes para variables artificiales
    
    print(f"Objetivo Fase I: {c_phase1}")
    
    # Crear tableau Fase I
    tableau1 = create_tableau_corrected(c_phase1, A_phase1, b_std, minimize=True)
    
    print(f"\nTableau inicial Fase I:")
    print(tableau1)
    
    # Las variables básicas iniciales son las artificiales
    basic_vars = [n + m + i for i in range(num_artificial)]
    print(f"Variables básicas iniciales: {basic_vars}")
    
    # Hacer que las variables artificiales tengan coeficiente 0 en la función objetivo
    for i, basic_var in enumerate(basic_vars):
        constraint_row = artificial_indices[i]
        # Restar la fila de restricción de la fila objetivo
        tableau1[-1] -= tableau1[constraint_row]
    
    print(f"\nTableau Fase I después de ajustar función objetivo:")
    print(tableau1)
    
    # Resolver Fase I
    solution1, optimal_value1 = solve_simplex_tableau(tableau1, basic_vars)
    
    print(f"\nSolución Fase I:")
    print(f"solution = {solution1}")
    print(f"optimal_value = {optimal_value1}")
    
    # Verificar factibilidad
    if optimal_value1 > 1e-8:
        print("❌ Problema INFACTIBLE")
        return None, None
    
    # Verificar que variables artificiales sean 0
    artificial_sum = sum(solution1[n + m + i] for i in range(num_artificial))
    if artificial_sum > 1e-8:
        print("❌ Problema INFACTIBLE (variables artificiales no son 0)")
        return None, None
    
    print("✅ Fase I completada - Problema factible")
    
    # PASO 5: FASE II - Resolver problema original
    print("\n=== INICIANDO FASE II ===")
    
    # Remover columnas de variables artificiales
    A_phase2 = A_phase1[:, :n + m]
    
    # Objetivo original
    c_phase2 = np.zeros(n + m)
    c_phase2[:n] = c if not minimize else -c
    
    print(f"Objetivo Fase II: {c_phase2}")
    
    # Encontrar variables básicas actuales (sin artificiales)
    basic_vars_phase2 = []
    for var in basic_vars:
        if var < n + m:
            basic_vars_phase2.append(var)
    
    # Si faltan variables básicas, encontrar otras
    while len(basic_vars_phase2) < m:
        for j in range(n + m):
            if j not in basic_vars_phase2:
                # Verificar si esta variable puede ser básica
                col = A_phase2[:, j]
                if np.count_nonzero(col) == 1 and np.max(np.abs(col)) == 1:
                    basic_vars_phase2.append(j)
                    break
    
    print(f"Variables básicas Fase II: {basic_vars_phase2}")
    
    # Crear tableau Fase II
    tableau2 = create_tableau_corrected(c_phase2, A_phase2, b_std, minimize=minimize)
    
    print(f"\nTableau inicial Fase II:")
    print(tableau2)
    
    # Resolver Fase II
    solution2, optimal_value2 = solve_simplex_tableau(tableau2, basic_vars_phase2)
    
    if solution2 is None:
        print("❌ Error en Fase II")
        return None, None
    
    # Extraer solo las variables originales
    final_solution = solution2[:n]
    final_value = optimal_value2
    
    if minimize:
        final_value = -final_value
    
    print(f"\n✅ SOLUCIÓN FINAL:")
    print(f"x = {final_solution}")
    print(f"Z = {final_value}")
    
    return final_solution, final_value


def create_tableau_corrected(c, A, b, minimize=False):
    """Crear tableau corregido"""
    m, n = A.shape
    tableau = np.zeros((m + 1, n + 1))
    
    # Filas de restricciones
    tableau[:-1, :-1] = A
    tableau[:-1, -1] = b
    
    # Fila objetivo
    if minimize:
        tableau[-1, :-1] = c  # Para minimización, usamos c directamente
    else:
        tableau[-1, :-1] = -c  # Para maximización, usamos -c
    
    return tableau


def solve_simplex_tableau(tableau, basic_vars, max_iter=100):
    """Resolver tableau usando simplex"""
    m, n = tableau.shape
    
    for iteration in range(max_iter):
        print(f"\n--- Iteración {iteration} ---")
        print(f"Tableau:")
        print(tableau)
        print(f"Variables básicas: {basic_vars}")
        
        # Encontrar variable entrante (costo reducido más negativo)
        obj_row = tableau[-1, :-1]
        entering_col = np.argmin(obj_row)
        
        if obj_row[entering_col] >= -1e-8:
            print("✅ Óptimo alcanzado")
            break
        
        print(f"Variable entrante: {entering_col} (costo reducido: {obj_row[entering_col]})")
        
        # Encontrar variable saliente (test de razón)
        col = tableau[:-1, entering_col]
        rhs = tableau[:-1, -1]
        
        ratios = []
        for i in range(len(col)):
            if col[i] > 1e-8:
                ratios.append(rhs[i] / col[i])
            else:
                ratios.append(float('inf'))
        
        if all(r == float('inf') for r in ratios):
            print("❌ Problema no acotado")
            return None, None
        
        leaving_row = np.argmin(ratios)
        print(f"Variable saliente: {basic_vars[leaving_row]} (fila: {leaving_row})")
        
        # Pivotear
        pivot = tableau[leaving_row, entering_col]
        tableau[leaving_row] /= pivot
        
        for i in range(m):
            if i != leaving_row:
                tableau[i] -= tableau[i, entering_col] * tableau[leaving_row]
        
        # Actualizar variables básicas
        basic_vars[leaving_row] = entering_col
    
    # Extraer solución
    solution = np.zeros(n - 1)  # -1 porque la última columna es RHS
    for i, var in enumerate(basic_vars):
        if var < len(solution):
            solution[var] = tableau[i, -1]
    
    optimal_value = tableau[-1, -1]
    
    return solution, optimal_value


def solve_standard_simplex(c, A, b, minimize=False):
    """Resolver simplex estándar sin variables artificiales"""
    print("Resolviendo problema estándar (sin variables artificiales)")
    
    c_tableau = np.zeros(A.shape[1])
    c_tableau[:len(c)] = c if not minimize else -c
    
    tableau = create_tableau_corrected(c_tableau, A, b, minimize=minimize)
    
    # Variables básicas iniciales son las de holgura
    m, n = A.shape
    basic_vars = list(range(len(c), A.shape[1]))
    
    solution, optimal_value = solve_simplex_tableau(tableau, basic_vars)
    
    if solution is not None:
        final_solution = solution[:len(c)]
        final_value = optimal_value
        if minimize:
            final_value = -final_value
        return final_solution, final_value
    
    return None, None


if __name__ == "__main__":
    # Test del problema específico
    c = [3, 2, 3]
    A = [
        [1, 4, 1],    # x1 + 4x2 + x3 >= 7
        [2, 1, 1]     # 2x1 + x2 + x3 >= 10
    ]
    b = [7, 10]
    
    solution, optimal_value = two_phase_simplex_corrected(
        c, A, b, 
        eq_constraints=[],
        ge_constraints=[0, 1],
        minimize=True
    )
    
    if solution is not None:
        print(f"\n🎉 RESULTADO FINAL:")
        print(f"x1 = {solution[0]:.6f}")
        print(f"x2 = {solution[1]:.6f}")
        print(f"x3 = {solution[2]:.6f}")
        print(f"Z = {optimal_value:.6f}")
        
        # Verificar restricciones
        r1 = solution[0] + 4*solution[1] + solution[2]
        r2 = 2*solution[0] + solution[1] + solution[2]
        print(f"\nVerificación:")
        print(f"Restricción 1: {r1:.6f} >= 7 {'✓' if r1 >= 7-1e-6 else '✗'}")
        print(f"Restricción 2: {r2:.6f} >= 10 {'✓' if r2 >= 10-1e-6 else '✗'}")
    else:
        print("❌ No se pudo resolver el problema")
