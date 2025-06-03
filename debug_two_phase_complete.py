import numpy as np
from app.solvers.dosfases_solver import dosfases_solver, create_tableau, solve_tableau

# Test the complete two-phase process step by step
c = np.array([3., 2., 3., 0.])
A = np.array([[1., 4., 3., 0.], [2., 1., 0., 1.]])
b = np.array([7., 10.])
ge_constraints = [0, 1]
minimize = True

print("=== TEST COMPLETO DE DOS FASES ===")
print(f"c = {c}")
print(f"A = {A}")
print(f"b = {b}")
print(f"ge_constraints = {ge_constraints}")
print(f"minimize = {minimize}")

# Llamar al solver completo
result = dosfases_solver(c, A, b, ge_constraints=ge_constraints, minimize=minimize)
print(f"\nResultado del solver completo: {result}")

if result[0] is not None:
    solution, optimal_value = result
    print(f"✅ Solución: {solution}")
    print(f"✅ Valor óptimo: {optimal_value}")
else:
    print("❌ El solver retornó None")

print("\n" + "="*50)
print("AHORA HAGAMOS EL PROCESO PASO A PASO...")

# Paso 1: Preparar problema para Phase 1
print("\n=== PASO 1: PREPARAR PHASE 1 ===")
c_neg = -c if minimize else c
print(f"Objetivo negado: {c_neg}")

m, n = A.shape
print(f"Dimensiones: m={m}, n={n}")

# Construir matriz con slack/surplus
A_with_slack = np.hstack([A, np.array([[-1., 0.], [0., -1.]])])
print(f"A con surplus:\n{A_with_slack}")

# Agregar variables artificiales
A_phase1 = np.hstack([A_with_slack, np.eye(m)])
print(f"A_phase1:\n{A_phase1}")

c_phase1 = np.zeros(A_phase1.shape[1])
c_phase1[-m:] = 1  # Minimizar variables artificiales
print(f"c_phase1: {c_phase1}")

basic_vars_phase1 = list(range(A_phase1.shape[1] - m, A_phase1.shape[1]))
print(f"Variables básicas Phase 1: {basic_vars_phase1}")

# Crear tableau Phase 1
tableau1 = create_tableau(c_phase1, A_phase1, b, maximize=False)
print(f"\nTableau Phase 1 inicial:\n{tableau1}")

# Hacer variables artificiales básicas en objetivo
for i, art_var in enumerate(basic_vars_phase1):
    col_idx = art_var
    coef = tableau1[-1, col_idx]
    if abs(coef) > 1e-10:
        tableau1[-1] -= coef * tableau1[i]
print(f"\nTableau Phase 1 ajustado:\n{tableau1}")

# Resolver Phase 1
print("\n=== PASO 2: RESOLVER PHASE 1 ===")
result1 = solve_tableau(tableau1.copy(), basic_vars_phase1.copy(), track_iterations=True, minimize=True)

if result1[0] is not None:
    sol1, val1, hist1, pivots1 = result1
    print(f"✅ Phase 1 exitosa!")
    print(f"Solución Phase 1: {sol1}")
    print(f"Valor óptimo Phase 1: {val1}")
    print(f"Iteraciones: {len(hist1)}")
    
    if abs(val1) > 1e-6:
        print("❌ Problema no factible (variables artificiales > 0)")
    else:
        print("✅ Problema factible (variables artificiales = 0)")
        
        # Extraer tableau final de Phase 1
        final_tableau1 = hist1[-1]
        print(f"\nTableau final Phase 1:\n{final_tableau1}")
        
        # Identificar variables básicas finales
        final_basic_vars = []
        for i in range(m):
            # Buscar la variable básica en la fila i
            for j in range(final_tableau1.shape[1] - 1):
                col = final_tableau1[:-1, j]  # Columna sin fila objetivo
                if abs(col[i] - 1.0) < 1e-6 and sum(abs(col)) < 1 + 1e-6:
                    final_basic_vars.append(j)
                    break
        print(f"Variables básicas finales Phase 1: {final_basic_vars}")
        
        print("\n=== PASO 3: PREPARAR PHASE 2 ===")
        # Remover columnas artificiales
        num_original_vars = n + m  # Variables originales + slack/surplus
        tableau2 = final_tableau1[:, :num_original_vars + 1]  # +1 for RHS
        print(f"Tableau Phase 2 (sin artificiales):\n{tableau2}")
        
        # Nuevo objetivo para Phase 2
        tableau2[-1, :] = 0  # Limpiar fila objetivo
        tableau2[-1, :n] = c_neg  # Colocar objetivo original (negado si minimización)
        print(f"Objetivo Phase 2: {c_neg}")
        print(f"Tableau Phase 2 con nuevo objetivo:\n{tableau2}")
        
        # Variables básicas para Phase 2 (solo las que no son artificiales)
        basic_vars_phase2 = [var for var in final_basic_vars if var < num_original_vars]
        print(f"Variables básicas Phase 2: {basic_vars_phase2}")
        
        # Hacer variables básicas en objetivo = 0
        for i, basic_var in enumerate(basic_vars_phase2):
            if basic_var < tableau2.shape[1] - 1:  # No procesar RHS
                coef = tableau2[-1, basic_var]
                if abs(coef) > 1e-10:
                    tableau2[-1] -= coef * tableau2[i]
        
        print(f"Tableau Phase 2 ajustado:\n{tableau2}")
        
        print("\n=== PASO 4: RESOLVER PHASE 2 ===")
        result2 = solve_tableau(tableau2.copy(), basic_vars_phase2.copy(), track_iterations=True, minimize=minimize)
        
        if result2[0] is not None:
            sol2, val2, hist2, pivots2 = result2
            print(f"✅ Phase 2 exitosa!")
            print(f"Solución Phase 2: {sol2}")
            print(f"Valor óptimo Phase 2: {val2}")
            print(f"Iteraciones Phase 2: {len(hist2)}")
            
            # Extraer solo variables originales
            original_solution = sol2[:n]
            print(f"Solución original: {original_solution}")
            
        else:
            print("❌ Phase 2 falló")
            print(f"Result2: {result2}")
else:
    print("❌ Phase 1 falló")
    print(f"Result1: {result1}")
