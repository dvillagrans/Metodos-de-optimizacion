import numpy as np

# ──────────────────── Excepciones ────────────────────────
class GranMError(Exception):
	"""Base exception for Gran M algorithm errors."""
	pass

class DimensionError(GranMError):
	"""Dimensions of input arrays are incompatible."""
	pass

class UnboundedError(GranMError):
	"""LP is unbounded."""
	pass

# ──────────────────── Solver Big-M ───────────────────────
def granm_solver(c, A, b, sense=None, eq_constraints=None,
                 minimize=False, track_iterations=False, M=1e6):

    c = np.asarray(c, dtype=float)
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float)

    n_vars = len(c)
    n_constraints = len(b)

    if A.shape != (n_constraints, n_vars):
        raise DimensionError(f"A is {A.shape}, expected ({n_constraints}, {n_vars})")

    if sense is None:
        sense = ['≤'] * n_constraints
        if eq_constraints:
            for idx in eq_constraints:
                sense[idx] = '='

    slack = 0
    surplus = 0
    artificial = 0
    for s in sense:
        if s == '≤':
            slack += 1
        elif s == '≥':
            surplus += 1
            artificial += 1
        elif s == '=':
            artificial += 1

    total_vars = n_vars + slack + surplus + artificial
    tableau = np.zeros((n_constraints + 1, total_vars + 1))

    slack_idx = n_vars
    surplus_idx = slack_idx + slack
    artificial_idx = surplus_idx + surplus

    art_map = {}

    for i in range(n_constraints):
        tableau[i+1, :n_vars] = A[i]
        tableau[i+1, -1] = b[i]

        if sense[i] == '≤':
            tableau[i+1, slack_idx] = 1
            slack_idx += 1
        elif sense[i] == '≥':
            tableau[i+1, surplus_idx] = -1
            surplus_idx += 1
            tableau[i+1, artificial_idx] = 1
            art_map[artificial_idx] = i + 1
            artificial_idx += 1
        elif sense[i] == '=':
            tableau[i+1, artificial_idx] = 1
            art_map[artificial_idx] = i + 1
            artificial_idx += 1

    tableau[0, :n_vars] = c if minimize else -c

    for j, row in art_map.items():
        sign = -1 if minimize else 1
        tableau[0, j] = sign * M
        tableau[0] -= sign * M * tableau[row]

    if track_iterations:
        tableau_history = [tableau.copy()]
        pivot_history = []

    max_iter = 1000
    for _ in range(max_iter):
        cost_row = tableau[0, :-1]
        if minimize:
            col_candidates = np.where(cost_row > 1e-8)[0]
        else:
            col_candidates = np.where(cost_row < -1e-8)[0]

        if col_candidates.size == 0:
            break

        pivot_col = col_candidates[0]
        col = tableau[1:, pivot_col]
        rhs = tableau[1:, -1]
        ratios = np.where(col > 1e-8, rhs / col, np.inf)

        if np.all(np.isinf(ratios)):
            raise UnboundedError("Problem is unbounded")

        pivot_row = np.argmin(ratios) + 1

        if track_iterations:
            pivot_history.append((pivot_row, pivot_col))

        tableau[pivot_row] /= tableau[pivot_row, pivot_col]
        for r in range(tableau.shape[0]):
            if r != pivot_row:
                tableau[r] -= tableau[r, pivot_col] * tableau[pivot_row]

        if track_iterations:
            tableau_history.append(tableau.copy())

    solution = np.zeros(n_vars)
    for j in range(n_vars):
        col = tableau[1:, j]
        if np.count_nonzero(np.abs(col - 1) < 1e-8) == 1 and np.count_nonzero(col > 1e-8) == 1:
            row = np.where(np.abs(col - 1) < 1e-8)[0][0] + 1
            solution[j] = tableau[row, -1]

    z_opt = np.dot(c, solution)

    if track_iterations:
        return solution, z_opt, tableau_history, pivot_history
    return solution, z_opt
