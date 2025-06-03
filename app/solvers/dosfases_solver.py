import numpy as np

# Exception classes for Two-Phase method
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
    Solves linear programming problems using the Two-Phase Method.
    
    Args:
        c: Objective function coefficients
        A: Constraint matrix  
        b: Right-hand side values
        eq_constraints: List of indices for equality constraints
        ge_constraints: List of indices for >= constraints
        minimize: Whether to minimize (True) or maximize (False)
        track_iterations: Whether to track tableau iterations
    
    Returns:
        If track_iterations=False:
            tuple: (solution, optimal_value)
        If track_iterations=True:
            tuple: (solution, optimal_value, tableau_history, pivot_history)
    """
    c = np.array(c, dtype=float)
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float)
    
    if minimize:
        c = -c
    
    m, n = A.shape
    
    # Initialize tracking lists if needed
    tableau_history = [] if track_iterations else None
    pivot_history = [] if track_iterations else None
    
    # Initialize constraint types
    if eq_constraints is None:
        eq_constraints = []
    if ge_constraints is None:
        ge_constraints = []
      # Convert constraints to standard form
    A_std = []
    b_std = []
    artificial_needed = []
    slack_types = []  # Track which variables are slack or surplus
    
    for i in range(m):
        if i in ge_constraints:
            # For >= constraints: Ax >= b becomes Ax - s = b (subtract surplus, add artificial)
            A_std.append(A[i].copy())
            b_std.append(b[i])
            slack_types.append('surplus')  # This will be -1 coefficient
            artificial_needed.append(i)
        elif i in eq_constraints:
            # For = constraints: Ax = b (add artificial directly)
            A_std.append(A[i].copy())
            b_std.append(b[i])
            slack_types.append('none')  # No slack/surplus
            artificial_needed.append(i)
        else:
            # For <= constraints: Ax <= b becomes Ax + s = b (add slack)
            A_std.append(A[i].copy())
            b_std.append(b[i])
            slack_types.append('slack')  # This will be +1 coefficient
    
    A_std = np.array(A_std)
    b_std = np.array(b_std)
    
    # Add slack/surplus variables
    slack_matrix = np.zeros((m, m))
    for i in range(m):
        if slack_types[i] == 'slack':
            slack_matrix[i, i] = 1
        elif slack_types[i] == 'surplus':
            slack_matrix[i, i] = -1
        # For equality constraints, no slack/surplus variable
    
    A_with_slack = np.hstack([A_std, slack_matrix])
    
    if not artificial_needed:
        # No artificial variables needed - can solve directly
        solution, optimal_value, phase_tableau_history, phase_pivot_history = solve_standard_form(
            c, A_with_slack, b_std, minimize, track_iterations
        )
        if track_iterations and solution is not None:
            tableau_history.extend(phase_tableau_history)
            pivot_history.extend(phase_pivot_history)
        
        if track_iterations:
            return solution, optimal_value, tableau_history, pivot_history
        return solution, optimal_value
      # Phase 1: Add artificial variables
    num_artificial = len(artificial_needed)
    artificial_matrix = np.zeros((m, num_artificial))
    
    for idx, constraint_idx in enumerate(artificial_needed):
        artificial_matrix[constraint_idx, idx] = 1
    
    A_phase1 = np.hstack([A_with_slack, artificial_matrix])
    
    # Phase 1 objective: minimize sum of artificial variables
    c_phase1 = np.zeros(A_phase1.shape[1])
    for i in range(num_artificial):
        c_phase1[n + m + i] = 1  # Coefficients for artificial variables
    
    # Create Phase 1 tableau
    tableau1 = create_tableau(c_phase1, A_phase1, b_std, maximize=False)
    
    # Set up initial basic variables
    basic_vars = []
    for i in range(m):
        if i in artificial_needed:
            # Find the artificial variable for this constraint
            art_idx = artificial_needed.index(i)
            basic_vars.append(n + m + art_idx)
        else:
            # Use slack variable
            basic_vars.append(n + i)
    
    # Make artificial variables basic in objective function by eliminating them
    for i, constraint_idx in enumerate(artificial_needed):
        art_var_col = n + m + i
        if abs(tableau1[-1, art_var_col]) > 1e-10:
            # Subtract the constraint row from objective row to make artificial var coefficient 0
            tableau1[-1] -= tableau1[-1, art_var_col] * tableau1[constraint_idx]
    
    if track_iterations:
        tableau_history.append(tableau1.copy())      # Solve Phase 1
    solution1, optimal_value1, phase1_tableau_history, phase1_pivot_history = solve_tableau(
        tableau1, basic_vars, track_iterations=True, minimize=True  # Fase 1 siempre es minimización
    )
    
    if track_iterations and solution1 is not None:
        tableau_history.extend(phase1_tableau_history)
        pivot_history.extend(phase1_pivot_history)
    
    if solution1 is None or optimal_value1 > 1e-8:
        if track_iterations:
            return None, None, tableau_history, pivot_history
        return None, None  # Infeasible
    
    # Check if artificial variables are zero
    artificial_sum = sum(solution1[n + m + i] for i in range(num_artificial))
    if artificial_sum > 1e-8:
        if track_iterations:
            return None, None, tableau_history, pivot_history
        return None, None  # Infeasible      # Phase 2: Remove artificial variables and solve original problem
    A_phase2 = A_phase1[:, :n + m]  # Remove artificial variable columns
    
    # Get the final tableau from Phase 1
    final_tableau1 = tableau_history[-1] if track_iterations else tableau1
    
    # Extract the Phase 2 tableau from the Phase 1 final tableau
    # Remove artificial variable columns but keep constraint and RHS structure
    tableau2 = np.zeros((m + 1, n + m + 1))
    
    # Copy constraint rows (excluding artificial variable columns)
    tableau2[:-1, :n + m] = final_tableau1[:-1, :n + m]
    tableau2[:-1, -1] = final_tableau1[:-1, -1]  # Copy RHS
      # Set up Phase 2 objective function
    c_phase2 = np.zeros(n + m)
    c_phase2[:n] = c  # Original objective coefficients (already negated if minimize=True)
    
    # For tableau: we always use maximization form in the simplex method
    # So if original problem is minimize, c is already negated, use -c_phase2 for tableau
    # If original problem is maximize, c is not negated, use -c_phase2 for tableau  
    tableau2[-1, :n + m] = -c_phase2  # Always negate for maximization form
    tableau2[-1, -1] = 0  # Initial objective value
    
    # Find current basic variables from Phase 1 solution (excluding artificial vars)
    basic_vars_phase2 = []
    for i in range(m):
        found_basic = False
        # Check each non-artificial variable to see if it's basic in row i
        for j in range(n + m):
            # Check if variable j is basic in constraint i
            if abs(final_tableau1[i, j] - 1.0) < 1e-8:
                # Check if it's the only non-zero in its column (among constraint rows)
                is_basic = True
                for k in range(m):
                    if k != i and abs(final_tableau1[k, j]) > 1e-8:
                        is_basic = False
                        break
                if is_basic:
                    basic_vars_phase2.append(j)
                    found_basic = True
                    break
        
        if not found_basic:
            # If no basic variable found for this row, use slack if available
            if n + i < n + m:
                basic_vars_phase2.append(n + i)
    
    # Ensure we have exactly m basic variables
    while len(basic_vars_phase2) < m:
        # Add missing slack variables if needed
        for i in range(m):
            slack_var = n + i
            if slack_var not in basic_vars_phase2 and len(basic_vars_phase2) < m:
                basic_vars_phase2.append(slack_var)
                break
    basic_vars_phase2 = basic_vars_phase2[:m]
    
    # Make basic variables have zero coefficients in objective
    for i, basic_var in enumerate(basic_vars_phase2):
        if basic_var < n + m and abs(tableau2[-1, basic_var]) > 1e-8:
            # Eliminate this basic variable from objective row
            tableau2[-1] -= tableau2[-1, basic_var] * tableau2[i]
    
    if track_iterations:
        tableau_history.append(tableau2.copy())    # Solve Phase 2
    solution2, optimal_value2, phase2_tableau_history, phase2_pivot_history = solve_tableau(
        tableau2, basic_vars_phase2, track_iterations=True, minimize=minimize  # Use original minimize flag
    )
    
    if track_iterations and solution2 is not None:
        tableau_history.extend(phase2_tableau_history)
        pivot_history.extend(phase2_pivot_history)
    
    if solution2 is None:
        if track_iterations:
            return None, None, tableau_history, pivot_history
        return None, None
    
    # Extract original variables
    x = solution2[:n]
    final_value = optimal_value2
    
    if minimize:
        final_value = -final_value
    
    if track_iterations:
        return x, final_value, tableau_history, pivot_history
    return x, final_value


def solve_standard_form(c, A, b, minimize=False, track_iterations=False):
    """Solve LP in standard form without artificial variables."""
    # c is the original objective function coefficients (possibly negated if original problem was MIN)
    # A is A_with_slack (original variables + slack variables)
    
    n_orig = len(c)  # Number of original variables
    n_total_vars_in_A = A.shape[1] # Total columns in A_with_slack (original + slack)

    # Create the full objective vector for the tableau, including zeros for slack variables
    c_tableau = np.zeros(n_total_vars_in_A)
    c_tableau[:n_orig] = c
    
    # When calling create_tableau:
    # If original problem is MAX (minimize=False), then c_tableau is c_orig_padded, and maximize=True for create_tableau.
    #   create_tableau will use -c_tableau in the objective row.
    # If original problem is MIN (minimize=True), then c_tableau is -c_orig_padded, and maximize=False for create_tableau.
    #   create_tableau will use c_tableau (which is already -c_orig_padded) in the objective row.
    # This ensures the objective row is correctly set for maximization form of simplex.
    tableau = create_tableau(c_tableau, A, b, maximize=not minimize)
    
    m, n_total_tableau_cols = tableau.shape # n_total_tableau_cols includes RHS
    
    # Initial basic variables (slack variables)
    basic_vars = list(range(n_orig, n_total_vars_in_A))      # Solve the tableau
    solution, optimal_value, tableau_history, pivot_history = solve_tableau(
        tableau, basic_vars, track_iterations=True, minimize=minimize
    )
    
    if solution is None:
        if track_iterations:
            return None, None, [], []
        return None, None
    
    # Extract just the original variables from solution
    x = solution[:n_orig]
    
    if track_iterations:
        return x, optimal_value, tableau_history, pivot_history
    return x, optimal_value


def create_tableau(c, A, b, maximize=True):
    """Create simplex tableau."""
    m, n = A.shape
    tableau = np.zeros((m + 1, n + 1))
    
    # Constraint rows
    tableau[:-1, :-1] = A
    tableau[:-1, -1] = b
    
    # Objective row
    if maximize:
        tableau[-1, :-1] = -c  # Negative for maximization
    else:
        tableau[-1, :-1] = c
    
    return tableau


def solve_tableau(tableau, basic_vars, track_iterations=False, minimize=False):
    """
    Solve a linear programming problem in tableau form.
    
    Args:
        tableau: The initial tableau
        basic_vars: List of basic variable indices
        track_iterations: Whether to track tableau and pivot history
        minimize: Whether this is a minimization problem
    
    Returns:
        If track_iterations=False:
            tuple: (solution vector, optimal value)
        If track_iterations=True:
            tuple: (solution vector, optimal value, tableau_history, pivot_history)
    """
    m, n = tableau.shape
    n = n - 1  # Adjust for RHS column
    max_iterations = 100  # Safety limit
    iteration = 0
    
    tableau_history = [] if track_iterations else None
    pivot_history = [] if track_iterations else None
    
    if track_iterations:
        tableau_history.append(tableau.copy())
    
    while iteration < max_iterations:
        # Find entering variable based on optimization type
        z_row = tableau[-1, :-1]
        
        if minimize:
            # For minimization: look for most negative coefficient (can improve solution)
            entering_col = np.argmin(z_row)
            optimal_condition = z_row[entering_col] >= -1e-10  # No negative coefficients
        else:
            # For maximization: look for most positive coefficient (can improve solution)
            entering_col = np.argmax(z_row)
            optimal_condition = z_row[entering_col] <= 1e-10  # No positive coefficients
        
        if optimal_condition:  # Optimal solution found
            # Extract solution
            solution = np.zeros(n)
            for i, basic_var in enumerate(basic_vars):
                if basic_var < n:  # Only store original variables
                    solution[basic_var] = tableau[i, -1]
            
            # Get optimal value from tableau
            optimal_value = tableau[-1, -1]
            
            if track_iterations:
                return solution, optimal_value, tableau_history, pivot_history
            return solution, optimal_value
        
        # Find leaving variable (minimum ratio test)
        pivot_ratios = []
        for i in range(m-1):  # Skip objective row
            if tableau[i, entering_col] > 1e-10:
                ratio = tableau[i, -1] / tableau[i, entering_col]
                pivot_ratios.append((ratio, i))
        
        if not pivot_ratios:  # Unbounded solution
            if track_iterations:
                return None, None, tableau_history, pivot_history
            return None, None
        
        # Choose row with minimum positive ratio
        pivot_row = min(pivot_ratios)[1]
        
        if track_iterations:
            pivot_history.append((pivot_row, entering_col))
        
        # Pivot operation
        pivot_element = tableau[pivot_row, entering_col]
        tableau[pivot_row] /= pivot_element
        
        for i in range(m):
            if i != pivot_row:
                tableau[i] -= tableau[i, entering_col] * tableau[pivot_row]
        
        # Update basic variables
        basic_vars[pivot_row] = entering_col
        
        if track_iterations:
            tableau_history.append(tableau.copy())
        
        iteration += 1
    
    # Max iterations reached
    if track_iterations:
        return None, None, tableau_history, pivot_history
    return None, None
