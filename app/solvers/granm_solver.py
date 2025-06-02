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
    """
    Big-M method for LP with ≤, ≥, = constraints.

    Args
    ----
    c : list[float]               # objective coefficients
    A : list[list[float]]         # constraint matrix
    b : list[float]               # RHS
    sense : list[str]             # '≤', '≥', '='  (len = m)
    minimize : bool               # default False (maximization)
    track_iterations : bool       # returns tableau & pivot history
    M : float                     # big penalty (default 1e6)

    Returns
    -------
    (solution, z_opt) or
    (solution, z_opt, tableau_history, pivot_history)
    """
    # ── numpy cast & checks ───────────────────────────────
    c = np.asarray(c, dtype=float)
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float)

    n_vars        = len(c)
    n_constraints = len(b)
    if A.shape != (n_constraints, n_vars):
        raise DimensionError(f"A is {A.shape}, expected ({n_constraints}, {n_vars})")

    # ── manejar RHS negativos ─────────────────────────────
    for i in range(n_constraints):
        if b[i] < 0:
            A[i] = -A[i]
            b[i] = -b[i]

    # ── determinar vector sense (retro-compat) ───────────
    if sense is None:
        sense = ['≤'] * n_constraints
        if eq_constraints is not None:
            for i in eq_constraints:
                sense[i] = '='

    # ── marcar filas que necesitan artificial ─────────────
    need_art      = [s in ('≥', '=') for s in sense]
    n_artificial  = sum(need_art)

    # ── convertir ≥ → ≤ (exceso −1) -s────────────────────
    sense_conv = sense.copy()
    for i, s in enumerate(sense):
        if s == '≥':
            A[i]   = -A[i]
            b[i]   = -b[i]
            sense_conv[i] = '≤'          # ahora es ≤

    # ── construir tableau inicial ─────────────────────────
    total_vars = n_vars + n_constraints + n_artificial
    tableau    = np.zeros((n_constraints + 1, total_vars + 1))

    # objetivo (fila 0)
    tableau[0, :n_vars] = -c if not minimize else c

    slack_idx      = n_vars
    artificial_idx = n_vars + n_constraints

    for i in range(n_constraints):
        tableau[i+1, :n_vars] = A[i]

        # slack / exceso (ahora todas son ≤)
        tableau[i+1, slack_idx] = 1
        slack_idx += 1

        # artificial si se requería originalmente
        if need_art[i]:
            tableau[i+1, artificial_idx] = 1
            sign_M = 1 if minimize else -1
            tableau[0, artificial_idx]  = sign_M * M
            # poner Z en forma canónica
            tableau[0] -= sign_M * M * tableau[i+1]
            artificial_idx += 1

        # RHS
        tableau[i+1, -1] = b[i]

    # ── historial opcional ────────────────────────────────
    if track_iterations:
        tableau_history = [tableau.copy()]
        pivot_history   = []

    # ── bucle simplex ─────────────────────────────────────
    max_iter = 10 * total_vars
    for _ in range(max_iter):
        # — selección de columna entrante (costo < 0 y alguna entrada > 0)
        pivot_col = None
        for j in np.argsort(tableau[0, :-1]):      # de más negativo a menos
            if tableau[0, j] >= -1e-10:            # no hay más negativos
                break
            if np.any(tableau[1:, j] > 1e-10):
                pivot_col = j
                break
        if pivot_col is None:                      # óptimo alcanzado
            break

        # — seleccionar fila (razón mínima)
        ratios = np.full(n_constraints, np.inf)
        positive = tableau[1:, pivot_col] > 1e-10
        ratios[positive] = tableau[1:, -1][positive] / tableau[1:, pivot_col][positive]
        pivot_row = ratios.argmin() + 1

        if np.isinf(ratios[pivot_row-1]):
            raise UnboundedError("Problem is unbounded")

        if track_iterations:
            pivot_history.append((pivot_row, pivot_col))

        # — pivotear
        tableau[pivot_row] /= tableau[pivot_row, pivot_col]
        for r in range(tableau.shape[0]):
            if r != pivot_row:
                tableau[r] -= tableau[r, pivot_col] * tableau[pivot_row]

        if track_iterations:
            tableau_history.append(tableau.copy())
    else:
        raise GranMError("Simplex exceeded iteration limit")

    # ── viabilidad final (artificiales en base) ───────────
    art_start = n_vars + n_constraints
    for j in range(art_start, art_start + n_artificial):
        col = tableau[:, j]
        if np.count_nonzero(col) == 1:
            row = np.where(col != 0)[0][0]
            if abs(col[row] - 1) < 1e-10 and tableau[row, -1] > 1e-10:
                raise GranMError("No feasible solution (artificial variable positive in basis)")

    # ── extraer solución ──────────────────────────────────
    solution = np.zeros(n_vars)
    for j in range(n_vars):
        col = tableau[:, j]
        if np.count_nonzero(col) == 1:
            row = np.where(col != 0)[0][0]
            if abs(col[row] - 1) < 1e-10:
                solution[j] = tableau[row, -1]

    z_opt = tableau[0, -1]
    if minimize:
        z_opt = -z_opt

    if track_iterations:
        return solution, z_opt, tableau_history, pivot_history
    return solution, z_opt
