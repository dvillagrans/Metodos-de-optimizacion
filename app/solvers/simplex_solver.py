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

def simplex(c, A, b, minimize=False, track_iterations=False):
    """
    Implements the Simplex algorithm to solve linear programming problems.
    
    Args:
        c (list): Coefficients of the objective function.
        A (list of lists): Matrix of constraint coefficients.
        b (list): Right-hand side values of constraints.
        minimize (bool): If True, minimize the objective function; otherwise, maximize.
        track_iterations (bool): If True, return tableau history and pivot history.
    
    Returns:
        If track_iterations is False:
            tuple: (solution, optimal value)
        If track_iterations is True:
            tuple: (solution, optimal value, tableau_history, pivot_history)
    
    Raises:
        DimensionError: If dimensions of input arrays are incompatible.
        NegativeBError: If b contains negative values.
        UnboundedError: If problem is unbounded.
    """
    # Convert inputs to numpy arrays
    c = np.array(c, dtype=float)
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float)
    
    # Verify dimensions
    n_vars = len(c)
    n_constraints = len(b)
    
    if A.shape != (n_constraints, n_vars):
        raise DimensionError(f"Dimensions mismatch: A is {A.shape}, expected ({n_constraints}, {n_vars})")
    
    # Check if any b is negative
    if np.any(b < 0):
        raise NegativeBError("The vector b cannot contain negative values")
    
    # If minimizing, convert to maximization problem
    if minimize:
        c = -c
    
    # Prepare the initial tableau
    # [c | 0]
    # [A | b]
    tableau = np.zeros((n_constraints + 1, n_vars + n_constraints + 1))
    # Set the objective function row (negated)
    tableau[0, :n_vars] = -c
    # Set the constraint coefficients
    tableau[1:, :n_vars] = A
    # Set the slack variables
    for i in range(n_constraints):
        tableau[i + 1, n_vars + i] = 1
    # Set the right-hand side
    tableau[1:, -1] = b
    
    # Initialize history if tracking iterations
    if track_iterations:
        tableau_history = [tableau.copy()]
        pivot_history = []
    
    # Main simplex loop
    max_iterations = 100  # Prevent infinite loops
    for iteration in range(max_iterations):
        # Find the pivot column (most negative in objective row)
        pivot_col = np.argmin(tableau[0, :-1])
        if tableau[0, pivot_col] >= 0:
            # Optimal solution found
            break
        
        # Find the pivot row (smallest ratio of b/a)
        column = tableau[1:, pivot_col]
        if np.all(column <= 0):
            raise UnboundedError("Problem is unbounded")
        
        # Calculate ratios for positive entries in the pivot column
        ratios = []
        for i in range(n_constraints):
            if tableau[i + 1, pivot_col] > 0:
                ratio = tableau[i + 1, -1] / tableau[i + 1, pivot_col]
                ratios.append((i, ratio))
            else:
                ratios.append((i, float('inf')))
        
        # Find the row with minimum ratio
        pivot_row = min(ratios, key=lambda x: x[1])[0] + 1
        
        # Track pivot if needed
        if track_iterations:
            pivot_history.append((pivot_row, pivot_col))
        
        # Pivot element
        pivot_element = tableau[pivot_row, pivot_col]
        
        # Normalize pivot row
        tableau[pivot_row, :] = tableau[pivot_row, :] / pivot_element
        
        # Eliminate pivot column from other rows
        for i in range(tableau.shape[0]):
            if i != pivot_row:
                tableau[i, :] -= tableau[i, pivot_col] * tableau[pivot_row, :]
        
        # Add to history if tracking iterations
        if track_iterations:
            tableau_history.append(tableau.copy())
    
    # Extract solution
    # Initialize solution vector with zeros
    solution = np.zeros(n_vars)
    
    # For each variable, check if it's a basic variable
    for j in range(n_vars):
        # Look for a column with exactly one 1 and all other elements 0
        col = tableau[:, j]
        # Count number of non-zeros
        non_zeros = np.count_nonzero(col)
        
        if non_zeros == 1:
            # Find the row with the non-zero element
            row = np.where(col != 0)[0][0]
            if abs(col[row] - 1.0) < 1e-10:  # Check if it's approximately 1
                # This is a basic variable; its value is in the RHS
                solution[j] = tableau[row, -1]
    
    # Compute optimal value
    z_opt = tableau[0, -1]
    
    # If minimizing, negate the optimal value back
    if minimize:
        z_opt = -z_opt
    
    if track_iterations:
        return solution, z_opt, tableau_history, pivot_history
    else:
        return solution, z_opt
