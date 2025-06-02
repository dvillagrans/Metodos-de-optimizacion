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

def dosfases_solver(c, A, b, eq_constraints=None, ge_constraints=None, minimize=False, track_iterations=False):
    """
    Implements the Two-Phase method to solve linear programming problems with equality and/or inequality constraints.
    
    Args:
        c (list): Coefficients of the objective function.
        A (list of lists): Matrix of constraint coefficients.
        b (list): Right-hand side values of constraints.
        eq_constraints (list): Indices of equality constraints (0-based).
        ge_constraints (list): Indices of >= constraints (0-based).
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

    # Set defaults
    if eq_constraints is None:
        eq_constraints = []
    if ge_constraints is None:
        ge_constraints = []
    
    # Convert to standard form and track what needs artificial variables
    A_std = A.copy()
    b_std = b.copy()
    needs_artificial = []
    
    # Process each constraint
    for i in range(n_constraints):
        if i in eq_constraints:
            # Equality constraint: needs artificial variable
            needs_artificial.append(i)
            # If b < 0, multiply by -1
            if b_std[i] < 0:
                A_std[i, :] = -A_std[i, :]
                b_std[i] = -b_std[i]
                
        elif i in ge_constraints:
            # >= constraint: convert to <= and needs artificial variable
            A_std[i, :] = -A_std[i, :]
            b_std[i] = -b_std[i]
            needs_artificial.append(i)
            
        else:
            # <= constraint: may need artificial if b < 0
            if b_std[i] < 0:
                A_std[i, :] = -A_std[i, :]
                b_std[i] = -b_std[i]
                needs_artificial.append(i)
    
    # If minimizing, convert to maximization
    if minimize:
        c_original = -c
    else:
        c_original = c.copy()
    
    # Setup for tracking
    if track_iterations:
        all_tableau_history = []
        all_pivot_history = []
    
    # Count variables needed
    n_artificial = len(needs_artificial)
    n_slack = n_constraints  # One slack/surplus for each constraint
    
    # PHASE 1: Find basic feasible solution
    # Tableau structure: [original vars | slack vars | artificial vars | RHS]
    total_vars_phase1 = n_vars + n_slack + n_artificial
    tableau1 = np.zeros((n_constraints + 1, total_vars_phase1 + 1))
    
    # Set up Phase 1 objective: minimize sum of artificial variables
    if n_artificial > 0:
        art_start = n_vars + n_slack
        tableau1[0, art_start:art_start + n_artificial] = -1
    
    # Fill constraint rows
    slack_col = n_vars
    art_col = n_vars + n_slack
    
    for i in range(n_constraints):
        # Original variables
        tableau1[i + 1, :n_vars] = A_std[i, :]
        
        # Slack/surplus variable
        if i in ge_constraints:
            # For >= converted to <=, this is a surplus variable (coefficient -1)
            tableau1[i + 1, slack_col] = -1
        else:
            # For <= and = constraints, this is a slack variable (coefficient +1)
            tableau1[i + 1, slack_col] = 1
            
        slack_col += 1
        
        # Artificial variable if needed
        if i in needs_artificial:
            tableau1[i + 1, art_col] = 1
            # Eliminate from objective row
            tableau1[0, :] -= tableau1[i + 1, :]
            art_col += 1
            
        # RHS
        tableau1[i + 1, -1] = b_std[i]
    
    # Phase 1 simplex iterations
    phase1_history = []
    phase1_pivots = []
    max_iterations = 100
    
    for iteration in range(max_iterations):
        if track_iterations:
            phase1_history.append(tableau1.copy())
            
        # Find entering variable (most negative in objective row)
        entering_col = np.argmin(tableau1[0, :-1])
        if tableau1[0, entering_col] >= -1e-10:
            # Optimal solution found for Phase 1
            break
            
        # Find leaving variable (minimum ratio test)
        pivot_col = tableau1[1:, entering_col]
        if np.all(pivot_col <= 0):
            raise UnboundedError("Phase 1 problem is unbounded")
            
        ratios = []
        for i in range(n_constraints):
            if tableau1[i + 1, entering_col] > 1e-10:
                ratio = tableau1[i + 1, -1] / tableau1[i + 1, entering_col]
                ratios.append((ratio, i))
                
        if not ratios:
            raise UnboundedError("Phase 1 problem is unbounded")
            
        _, leaving_row_idx = min(ratios)
        leaving_row = leaving_row_idx + 1
        
        if track_iterations:
            phase1_pivots.append((leaving_row, entering_col))
            
        # Pivot operation
        pivot_element = tableau1[leaving_row, entering_col]
        tableau1[leaving_row, :] /= pivot_element
        
        for i in range(tableau1.shape[0]):
            if i != leaving_row:
                tableau1[i, :] -= tableau1[i, entering_col] * tableau1[leaving_row, :]
    
    # Check if Phase 1 found feasible solution
    if tableau1[0, -1] < -1e-10:
        raise InfeasibleError("Problem is infeasible (no basic feasible solution exists)")
    
    if track_iterations:
        all_tableau_history.extend(phase1_history)
        all_pivot_history.extend(phase1_pivots)
    
    # PHASE 2: Optimize original objective
    # Remove artificial variables and set up original objective
    tableau2 = np.zeros((n_constraints + 1, n_vars + n_slack + 1))
    
    # Copy constraint part without artificial variables
    tableau2[1:, :n_vars + n_slack] = tableau1[1:, :n_vars + n_slack]
    tableau2[1:, -1] = tableau1[1:, -1]
    
    # Set original objective
    tableau2[0, :n_vars] = -c_original
    
    # Eliminate basic variables from objective row
    for j in range(n_vars):
        col = tableau2[1:, j]
        # Check if this is a basic variable (exactly one 1, rest 0)
        nonzero_indices = np.where(np.abs(col) > 1e-10)[0]
        if len(nonzero_indices) == 1 and np.abs(col[nonzero_indices[0]] - 1.0) < 1e-10:
            # This is a basic variable, eliminate from objective
            basic_row = nonzero_indices[0] + 1
            tableau2[0, :] -= tableau2[0, j] * tableau2[basic_row, :]
    
    # Phase 2 simplex iterations
    phase2_history = []
    phase2_pivots = []
    
    for iteration in range(max_iterations):
        if track_iterations:
            phase2_history.append(tableau2.copy())
            
        # Find entering variable
        entering_col = np.argmin(tableau2[0, :-1])
        if tableau2[0, entering_col] >= -1e-10:
            # Optimal solution found
            break
            
        # Find leaving variable
        pivot_col = tableau2[1:, entering_col]
        if np.all(pivot_col <= 0):
            raise UnboundedError("Problem is unbounded")
            
        ratios = []
        for i in range(n_constraints):
            if tableau2[i + 1, entering_col] > 1e-10:
                ratio = tableau2[i + 1, -1] / tableau2[i + 1, entering_col]
                ratios.append((ratio, i))
                
        if not ratios:
            raise UnboundedError("Problem is unbounded")
            
        _, leaving_row_idx = min(ratios)
        leaving_row = leaving_row_idx + 1
        
        if track_iterations:
            phase2_pivots.append((leaving_row, entering_col))
            
        # Pivot operation
        pivot_element = tableau2[leaving_row, entering_col]
        tableau2[leaving_row, :] /= pivot_element
        
        for i in range(tableau2.shape[0]):
            if i != leaving_row:
                tableau2[i, :] -= tableau2[i, entering_col] * tableau2[leaving_row, :]
    
    if track_iterations:
        all_tableau_history.extend(phase2_history)
        all_pivot_history.extend(phase2_pivots)
    
    # Extract solution
    solution = np.zeros(n_vars)
    
    for j in range(n_vars):
        col = tableau2[1:, j]
        nonzero_indices = np.where(np.abs(col) > 1e-10)[0]
        if len(nonzero_indices) == 1 and np.abs(col[nonzero_indices[0]] - 1.0) < 1e-10:
            # Basic variable
            basic_row = nonzero_indices[0] + 1
            solution[j] = tableau2[basic_row, -1]
    
    # Get optimal value
    optimal_value = tableau2[0, -1]
    if minimize:
        optimal_value = -optimal_value
    
    if track_iterations:
        return solution, optimal_value, all_tableau_history, all_pivot_history
    else:
        return solution, optimal_value
