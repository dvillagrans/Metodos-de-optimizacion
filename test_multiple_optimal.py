#!/usr/bin/env python3
"""
Test de múltiple óptimo para:
  MAX Z = 2 x₁ + x₂
  s.a. x₁ + x₂ ≥ 4
       x₁ + 2 x₂ ≤ 6
       x₁, x₂ ≥ 0
"""

from app.solvers.simplex_solver import simplex
from app.solvers.granm_solver import granm_solver
from app.solvers.dosfases_solver import dosfases_solver
from app.solvers.multiple_solutions_detector import detect_multiple_solutions
import numpy as np

def main():
    # Función objetivo
    c = [2, 1]
    # Convertimos ≥ a ≤ multiplicando por -1
    A_simplex = [[-1, -1],  # -(x₁ + x₂) ≤ -4
                 [1,  2]]  # x₁ + 2x₂ ≤ 6
    b_simplex = [-4, 6]

    # Para Gran M / Dos Fases mantenemos el A original e indicamos ge_constraints=[0]
    A_api = [[1, 1],
             [1, 2]]
    b_api = [4, 6]
    ge = [0]  # la primera restricción es ≥


    print("\n=== Gran M (ge_constraints=[0]) ===")
    sol, z, tab_hist, piv_hist = granm_solver(c, A_api, b_api,
                                              sense=None,
                                              eq_constraints=[],
                                              ge_constraints=ge,
                                              minimize=False,
                                              track_iterations=True)
    print("Solución:", sol, "Z =", z)
    final_tab = tab_hist[-1]
    ms = detect_multiple_solutions(final_tab, len(c))
    print("Múltiples?", ms['has_multiple'], "vars:", ms['zero_cost_vars'])
    print()

    print("\n=== Dos Fases (ge_constraints=[0]) ===")
    sol, z, tab_hist, piv_hist = dosfases_solver(c, A_api, b_api,
                                                 eq_constraints=[],
                                                 ge_constraints=ge,
                                                 minimize=False,
                                                 track_iterations=True)
    print("Solución:", sol, "Z =", z)
    final_tab = tab_hist[-1]
    ms = detect_multiple_solutions(final_tab, len(c))
    print("Múltiples?", ms['has_multiple'], "vars:", ms['zero_cost_vars'])
    print()

if __name__ == '__main__':
    main()