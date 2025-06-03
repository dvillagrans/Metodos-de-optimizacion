import numpy as np
from app.solvers.dosfases_solver import solve_tableau

# Test the solve_tableau function with a simple tableau
# This is the Phase 1 tableau from our debug output:
tableau = np.array([
    [ 1.0,  4.0,  3.0,  0.0, -1.0,  0.0,  1.0,  0.0,  7.0],
    [ 2.0,  1.0,  0.0,  1.0,  0.0, -1.0,  0.0,  1.0, 10.0],
    [-3.0, -5.0, -3.0, -1.0,  1.0,  1.0,  0.0,  0.0, -17.0]
])

basic_vars = [6, 7]  # artificial variables are basic

print("=== TEST SOLVE_TABLEAU ===")
print("Tableau inicial:")
for i, row in enumerate(tableau):
    if i < len(tableau) - 1:
        print(f"{i+1:1} | " + " ".join(f"{x:8.3f}" for x in row))
    else:
        print(f"Z | " + " ".join(f"{x:8.3f}" for x in row))

print(f"\nVariables básicas: {basic_vars}")
print("Objetivo: minimizar (Phase 1)")

# Test with minimize=True
print("\n=== LLAMANDO solve_tableau(minimize=True) ===")
result = solve_tableau(tableau.copy(), basic_vars.copy(), track_iterations=True, minimize=True)

if result[0] is not None:
    solution, optimal_value, tableau_history, pivot_history = result
    print(f"Solución: {solution}")
    print(f"Valor óptimo: {optimal_value}")
    print(f"Iteraciones: {len(tableau_history)}")
    print(f"Pivots: {pivot_history}")
    
    print("\nTableau final:")
    final_tableau = tableau_history[-1]
    for i, row in enumerate(final_tableau):
        if i < len(final_tableau) - 1:
            print(f"{i+1:1} | " + " ".join(f"{x:8.3f}" for x in row))
        else:
            print(f"Z | " + " ".join(f"{x:8.3f}" for x in row))
else:
    print("❌ solve_tableau retornó None")
    if len(result) >= 3:
        tableau_history = result[2]
        print(f"Iteraciones realizadas: {len(tableau_history)}")
        
        # Analizar por qué falla
        if len(tableau_history) > 1:
            print("\nTableau después de primera iteración:")
            final_tableau = tableau_history[-1]
            for i, row in enumerate(final_tableau):
                if i < len(final_tableau) - 1:
                    print(f"{i+1:1} | " + " ".join(f"{x:8.3f}" for x in row))
                else:
                    print(f"Z | " + " ".join(f"{x:8.3f}" for x in row))

print("\n=== ANÁLISIS MANUAL ===")
print("En el tableau inicial:")
print("Fila Z: [-3.0, -5.0, -3.0, -1.0, 1.0, 1.0, 0.0, 0.0, -17.0]")
print("Para minimización, buscamos el coeficiente MÁS NEGATIVO")
print("El más negativo es -5.0 en columna 1 (x2)")
print("Variable entrante debería ser x2 (columna 1)")

z_row = tableau[-1, :-1]
print(f"z_row = {z_row}")
print(f"argmin(z_row) = {np.argmin(z_row)} (índice del valor más negativo)")
print(f"Valor más negativo: {z_row[np.argmin(z_row)]}")
