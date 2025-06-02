import numpy as np

class SimplexError(Exception):
    """Base exception for Simplex algorithm errors."""
    pass

class DimensionError(SimplexError):
    """Exception raised when dimensions of input arrays are incompatible."""
    pass

class NegativeBError(SimplexError):
    """Exception raised when b contains negative values."""
    pass

class UnboundedError(SimplexError):
    """Exception raised when problem is unbounded."""
    pass

def simplex(c, A, b, minimize=False, track_iterations=False, tol=1e-10, max_iter=100):
    """
    Simplex clásico para restricciones tipo ≤ y c ≥ 0.
    Si alguna columna NO tiene coeficiente positivo, la salta
    (evita falsos 'unbounded' y permite detectar múltipl. óptimos).
    """
    c = np.asarray(c, dtype=float)
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float)

    m, n = A.shape
    if len(b) != m or len(c) != n:
        raise DimensionError("Dimensiones incompatibles")

    if np.any(b < -tol):
        raise NegativeBError("b no puede contener valores negativos (en esta versión)")

    # Maximizar ⇒ Z fila con -c
    if minimize:
        c = -c

    # ─ construir tableau inicial ─
    tableau = np.zeros((m + 1, n + m + 1))
    tableau[0, :n]    = -c
    tableau[1:, :n]   = A
    tableau[1:, n:n+m] = np.eye(m)
    tableau[1:, -1]   = b

    if track_iterations:
        T_hist = [tableau.copy()]
        pivots = []

    # ─ bucle principal ─
    for _ in range(max_iter):
        # 1. columna entrante (costo reducido más negativo QUE TENGA ALGO > 0)
        pivot_col = None
        z_row = tableau[0, :-1]

        for j in np.argsort(z_row):          # de más negativo a menos
            if z_row[j] >= -tol:
                break                        # no hay más negativos
            if np.any(tableau[1:, j] > tol):
                pivot_col = j
                break
        if pivot_col is None:                # óptimo alcanzado
            break

        # 2. fila pivote (razón mínima)
        col      = tableau[1:, pivot_col]
        rhs      = tableau[1:, -1]
        valid    = col > tol
        if not np.any(valid):
            raise UnboundedError("Problema no acotado")

        ratios   = rhs[valid] / col[valid]
        pivot_row = np.where(valid)[0][np.argmin(ratios)] + 1  # +1 por fila Z

        # 3. pivotear
        tableau[pivot_row] /= tableau[pivot_row, pivot_col]
        for r in range(tableau.shape[0]):
            if r != pivot_row:
                tableau[r] -= tableau[r, pivot_col] * tableau[pivot_row]

        if track_iterations:
            pivots.append((pivot_row, pivot_col))
            T_hist.append(tableau.copy())
    else:
        raise RuntimeError("Se alcanzó max_iter sin converger")

    # ─ extraer solución ─
    solution = np.zeros(n)
    for j in range(n):
        col = tableau[1:, j]
        if np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0, atol=tol):
            row_bas = np.where(np.isclose(col, 1.0, atol=tol))[0][0] + 1
            solution[j] = tableau[row_bas, -1]

    z_opt = tableau[0, -1]
    if minimize:
        z_opt = -z_opt

    if track_iterations:
        return solution, z_opt, T_hist, pivots
    return solution, z_opt
