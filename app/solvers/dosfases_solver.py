import numpy as np

class DosFasesError(Exception):
    """Base exception for Two-Phase method errors."""
    pass

class DimensionError(DosFasesError):
    """Exception raised when dimensions of input arrays are incompatible."""
    pass

class UnboundedError(DosFasesError):
    """Exception raised when problem is unbounded."""
    pass

class InfeasibleError(DosFasesError):
    """Exception raised when problem is infeasible."""
    pass

def dosfases_solver(c, A, b, eq_constraints=None, minimize=False, track_iterations=False):
    """
    Implements the Two-Phase method to solve linear programming problems with equality and/or inequality constraints.
    
    Args:
        c (list): Coefficients of the objective function.
        A (list of lists): Matrix of constraint coefficients.
        b (list): Right-hand side values of constraints.
        eq_constraints (list): Indices of equality constraints (0-based).
        minimize (bool): If True, minimize the objective function; otherwise, maximize.
        track_iterations (bool): If True, return tableau history and pivot history.
    
    Returns:
        If track_iterations is False:
            tuple: (solution, optimal value)
        If track_iterations is True:
            tuple: (solution, optimal value, tableau_history, pivot_history)
    
    Raises:
        DimensionError: If dimensions of input arrays are incompatible.
        UnboundedError: If problem is unbounded.
        InfeasibleError: If problem is infeasible.
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

    # Handle negative b values by multiplying the constraint by -1
    for i in range(n_constraints):
        if b[i] < 0:
            A[i, :] = -A[i, :]
            b[i] = -b[i]
    
    # By default, all constraints are inequalities
    if eq_constraints is None:
        eq_constraints = []
    
    # If minimizing, convert to maximization problem
    if minimize:
        c_original = -c
    else:
        c_original = c.copy()
    
    # History tracking setup
    if track_iterations:
        all_tableau_history = []
        all_pivot_history = []
    
    # PHASE 1: Find a basic feasible solution
    # Count number of artificial variables needed
    n_artificial = len(eq_constraints) + np.sum(b < 0)
    
    # Prepare Phase 1 tableau
    # Columns: original variables | slack variables | artificial variables | RHS
    total_vars_phase1 = n_vars + n_constraints + n_artificial
    tableau1 = np.zeros((n_constraints + 1, total_vars_phase1 + 1))
    
    # Phase 1 objective: minimize sum of artificial variables
    tableau1[0, n_vars + n_constraints:total_vars_phase1] = -1
    
    # Set the constraint coefficients and slack variables
    slack_var_index = n_vars
    artificial_var_index = n_vars + n_constraints
    artificial_vars_added = 0
    
    for i in range(n_constraints):
        # Add constraint coefficients
        tableau1[i + 1, :n_vars] = A[i, :]
        
        # Add slack variable for this constraint if it's an inequality
        if i not in eq_constraints:
            tableau1[i + 1, slack_var_index] = 1
            slack_var_index += 1
        
        # Add artificial variable for equality constraints or negative b values
        if i in eq_constraints:
            tableau1[i + 1, artificial_var_index] = 1
            # Add contribution to the objective function
            tableau1[0, :] -= tableau1[i + 1, :]
            artificial_var_index += 1
            artificial_vars_added += 1
        
        # Set the right-hand side
        tableau1[i + 1, -1] = b[i]
    
    # Phase 1 iterations
    phase1_history = []
    phase1_pivots = []
    
    # Main simplex loop for Phase 1
    max_iterations = 100  # Prevent infinite loops
    for iteration in range(max_iterations):
        if track_iterations:
            phase1_history.append(tableau1.copy())
        
        # Find the pivot column (most negative in objective row)
        pivot_col = np.argmin(tableau1[0, :-1])
        if tableau1[0, pivot_col] >= -1e-10:  # Use small threshold for numerical stability
            # Phase 1 optimal solution found
            break
        
        # Find the pivot row (smallest ratio of b/a)
        column = tableau1[1:, pivot_col]
        if np.all(column <= 0):
            raise UnboundedError("Phase 1 problem is unbounded (this shouldn't happen)")
        
        # Calculate ratios for positive entries in the pivot column
        ratios = []
        for i in range(n_constraints):
            if tableau1[i + 1, pivot_col] > 0:
                ratio = tableau1[i + 1, -1] / tableau1[i + 1, pivot_col]
                ratios.append((i, ratio))
            else:
                ratios.append((i, float('inf')))
        
        # Find the row with minimum ratio
        pivot_row = min(ratios, key=lambda x: x[1])[0] + 1
        
        if track_iterations:
            phase1_pivots.append((pivot_row, pivot_col))
        
        # Pivot element
        pivot_element = tableau1[pivot_row, pivot_col]
        
        # Normalize pivot row
        tableau1[pivot_row, :] = tableau1[pivot_row, :] / pivot_element
        
        # Eliminate pivot column from other rows
        for i in range(tableau1.shape[0]):
            if i != pivot_row:
                tableau1[i, :] -= tableau1[i, pivot_col] * tableau1[pivot_row, :]
    
    # Check if Phase 1 found a feasible solution
    if tableau1[0, -1] < -1e-10:
        raise InfeasibleError("Problem is infeasible (no basic feasible solution exists)")
    
    # Add Phase 1 history to overall history
    if track_iterations:
        all_tableau_history.extend(phase1_history)
        all_pivot_history.extend(phase1_pivots)
    
    # PHASE 2: Optimize the original objective function
    # Prepare Phase 2 tableau by removing artificial variables and setting original objective
    # Columns: original variables | slack variables | RHS
    total_vars_phase2 = n_vars + n_constraints - n_artificial
    tableau2 = np.zeros((n_constraints + 1, total_vars_phase2 + 1))
    
    # Copy the feasible solution part without artificial variables
    tableau2[1:, :total_vars_phase2] = tableau1[1:, :total_vars_phase2]
    tableau2[1:, -1] = tableau1[1:, -1]
    
    # Set the original objective function
    tableau2[0, :n_vars] = -c_original
    
    # Adjust the objective function based on basic variables
    for j in range(n_vars):
        col = tableau2[1:, j]
        basic_var = False
        basic_row = -1
        
        # Check if this is a basic variable
        for i in range(n_constraints):
            if abs(col[i] - 1.0) < 1e-10 and np.count_nonzero(col) == 1:
                basic_var = True
                basic_row = i
                break
        
        if basic_var:
            # Adjust objective row for this basic variable
            tableau2[0, :] -= tableau2[0, j] * tableau2[basic_row + 1, :]
    
    # Phase 2 iterations
    phase2_history = []
    phase2_pivots = []
    
    # Main simplex loop for Phase 2
    for iteration in range(max_iterations):
        if track_iterations:
            phase2_history.append(tableau2.copy())
        
        # Find the pivot column (most negative in objective row)
        pivot_col = np.argmin(tableau2[0, :-1])
        if tableau2[0, pivot_col] >= -1e-10:  # Use small threshold for numerical stability
            # Phase 2 optimal solution found
            break
        
        # Find the pivot row (smallest ratio of b/a)
        column = tableau2[1:, pivot_col]
        if np.all(column <= 0):
            raise UnboundedError("Problem is unbounded")
        
        # Calculate ratios for positive entries in the pivot column
        ratios = []
        for i in range(n_constraints):
            if tableau2[i + 1, pivot_col] > 0:
                ratio = tableau2[i + 1, -1] / tableau2[i + 1, pivot_col]
                ratios.append((i, ratio))
            else:
                ratios.append((i, float('inf')))
        
        # Find the row with minimum ratio
        pivot_row = min(ratios, key=lambda x: x[1])[0] + 1
        
        if track_iterations:
            phase2_pivots.append((pivot_row, pivot_col))
        
        # Pivot element
        pivot_element = tableau2[pivot_row, pivot_col]
        
        # Normalize pivot row
        tableau2[pivot_row, :] = tableau2[pivot_row, :] / pivot_element
        
        # Eliminate pivot column from other rows
        for i in range(tableau2.shape[0]):
            if i != pivot_row:
                tableau2[i, :] -= tableau2[i, pivot_col] * tableau2[pivot_row, :]
    
    # Add Phase 2 history to overall history
    if track_iterations:
        all_tableau_history.extend(phase2_history)
        all_pivot_history.extend(phase2_pivots)
    
    # Extract solution
    # Initialize solution vector with zeros
    solution = np.zeros(n_vars)
    
    # For each original variable, check if it's a basic variable
    for j in range(n_vars):
        # Look for a column with exactly one 1 and all other elements 0
        col = tableau2[1:, j]
        # Count number of non-zeros
        non_zeros = np.count_nonzero(col)
        
        if non_zeros == 1:
            # Find the row with the non-zero element
            row = np.where(col != 0)[0][0]
            if abs(col[row] - 1.0) < 1e-10:  # Check if it's approximately 1
                # This is a basic variable; its value is in the RHS
                solution[j] = tableau2[row + 1, -1]
    
    # Compute optimal value
    z_opt = tableau2[0, -1]
    
    # If minimizing, negate the optimal value back
    if minimize:
        z_opt = -z_opt
    
    if track_iterations:
        return solution, z_opt, all_tableau_history, all_pivot_history
    else:
        return solution, z_opt
