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
    A_std = A.copy()
    b_std = b.copy()
    
    # Convert >= constraints to <= by multiplying by -1
    for i in ge_constraints:
        if i < m:
            A_std[i] = -A_std[i]
            b_std[i] = -b_std[i]
    
    # Add slack variables for <= constraints
    slack_matrix = np.eye(m)
    A_with_slack = np.hstack([A_std, slack_matrix])
    
    # Determine which constraints need artificial variables
    artificial_needed = []
    
    # All equality constraints need artificial variables
    for i in eq_constraints:
        if i < m:
            artificial_needed.append(i)
    
    # Converted >= constraints (now <=) need artificial variables
    for i in ge_constraints:
        if i < m:
            artificial_needed.append(i)
    
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
    
    # Initial basic variables are artificial variables
    basic_vars = [n + m + i for i in range(num_artificial)]
    
    # Make artificial variables basic in objective function
    for i, basic_var in enumerate(basic_vars):
        constraint_row = artificial_needed[i]
        # Subtract constraint row from objective to make coefficient 0
        tableau1[-1] -= tableau1[constraint_row]
    
    if track_iterations:
        tableau_history.append(tableau1.copy())
      # Solve Phase 1
    solution1, optimal_value1, phase1_tableau_history, phase1_pivot_history = solve_tableau(
        tableau1, basic_vars, track_iterations, minimize=True  # Fase 1 siempre es minimización
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
        return None, None  # Infeasible
    
    # Phase 2: Remove artificial variables and solve original problem
    A_phase2 = A_phase1[:, :n + m]  # Remove artificial variable columns
    
    # Update basic variables (remove artificial variables)
    basic_vars_phase2 = []
    for i, var in enumerate(basic_vars):
        if var < n + m:  # Keep only non-artificial basic variables
            basic_vars_phase2.append(var)
        else:
            # Find a suitable non-basic variable to make basic
            for j in range(n + m):
                if j not in basic_vars_phase2:
                    basic_vars_phase2.append(j)
                    break
    
    # Ensure we have m basic variables
    while len(basic_vars_phase2) < m:
        for j in range(n + m):
            if j not in basic_vars_phase2:
                basic_vars_phase2.append(j)
                break
    
    basic_vars_phase2 = basic_vars_phase2[:m]  # Take only m variables
    
    # Create Phase 2 tableau with original objective
    c_phase2 = np.zeros(n + m)
    c_phase2[:n] = c
    
    tableau2 = create_tableau(c_phase2, A_phase2, b_std, maximize=True)
    
    # Make basic variables have zero coefficients in objective
    for i, basic_var in enumerate(basic_vars_phase2):
        if i < m and basic_var < tableau2.shape[1] - 1:
            if abs(tableau2[-1, basic_var]) > 1e-8:
                # Find pivot row for this basic variable
                for row in range(m):
                    if abs(tableau2[row, basic_var] - 1.0) < 1e-8:
                        tableau2[-1] -= tableau2[-1, basic_var] * tableau2[row]
                        break
    
    if track_iterations:
        tableau_history.append(tableau2.copy())    
    # Solve Phase 2
    solution2, optimal_value2, phase2_tableau_history, phase2_pivot_history = solve_tableau(
        tableau2, basic_vars_phase2, track_iterations, minimize  # Fase 2 usa el tipo original
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
    basic_vars = list(range(n_orig, n_total_vars_in_A))
      # Solve the tableau
    solution, optimal_value, tableau_history, pivot_history = solve_tableau(
        tableau, basic_vars, track_iterations, minimize
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
        # Find entering variable (most negative coefficient in objective row)
        z_row = tableau[-1, :-1]
        entering_col = np.argmin(z_row)
        if z_row[entering_col] >= -1e-10:  # Optimal solution found
            # Extract solution
            solution = np.zeros(n)
            for i, basic_var in enumerate(basic_vars):
                if basic_var < n:  # Only store original variables
                    solution[basic_var] = tableau[i, -1]
              # For maximization problems, the tableau objective row contains -c,
            # so the optimal value in tableau[-1, -1] is already the correct positive value.
            # For minimization problems, we need to consider the minimize flag.
            if minimize:
                optimal_value = -tableau[-1, -1]  # Negate for minimization
            else:
                optimal_value = tableau[-1, -1]   # Use directly for maximization
            
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
