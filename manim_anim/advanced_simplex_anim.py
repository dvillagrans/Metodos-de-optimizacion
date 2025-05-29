from manim import *
import json
import numpy as np

class AdvancedSimplexAnim(Scene):
    def construct(self):
        # Load problem data
        with open("problem_data.json", "r") as f:
            data = json.load(f)
        
        c = np.array(data["c"])
        A = np.array(data["A"])
        b = np.array(data["b"])
        solution = np.array(data["solution"])
        z_opt = data["z_opt"]
        minimize = data["minimize"]
        tableau_history = data.get("tableau_history", [])
        pivot_history = data.get("pivot_history", [])
        
        # Configuration
        title_color = BLUE
        tableau_color = WHITE
        pivot_color = YELLOW
        optimal_color = GREEN
        
        # Title
        title = Text("Método Simplex - Visualización Paso a Paso", font_size=36, color=title_color)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Problem setup
        self.show_problem_setup(c, A, b, minimize)
          # If we have tableau history, show iterations
        if len(tableau_history) > 0:
            self.show_tableau_iterations(tableau_history, pivot_history)
        
        # Show final solution
        self.show_final_solution(solution, z_opt, minimize)
        
        self.wait(2)
    
    def show_problem_setup(self, c, A, b, minimize):
        """Display the initial problem formulation"""
        problem_group = VGroup()
        
        # Problem type
        problem_type = "Minimización" if minimize else "Maximización"
        prob_text = Text(f"Problema de {problem_type}", font_size=28, color=YELLOW)
        problem_group.add(prob_text)
        
        # Objective function
        obj_text = self.format_objective_function(c, minimize)
        obj_func = Text(obj_text, font_size=24)
        obj_func.next_to(prob_text, DOWN, buff=0.4)
        problem_group.add(obj_func)
        
        # Constraints
        constraints_title = Text("Sujeto a:", font_size=22)
        constraints_title.next_to(obj_func, DOWN, buff=0.4)
        constraints_title.align_to(obj_func, LEFT)
        problem_group.add(constraints_title)
        
        # Individual constraints
        for i in range(len(b)):
            constraint_text = self.format_constraint(A[i], b[i], i)
            constraint = Text(constraint_text, font_size=20)
            if i == 0:
                constraint.next_to(constraints_title, DOWN, buff=0.2)
                constraint.align_to(constraints_title, LEFT).shift(RIGHT*0.3)
            else:
                constraint.next_to(problem_group[-1], DOWN, buff=0.15)
                constraint.align_to(problem_group[-1], LEFT)
            problem_group.add(constraint)
          # Position the entire problem group
        problem_group.scale(0.8).to_edge(LEFT).shift(UP*1)
        
        self.play(Write(problem_group))
        self.wait(2)
        # Clear for tableau
        self.play(FadeOut(problem_group))
    
    def format_objective_function(self, c, minimize):
        """Format the objective function string"""
        direction = "Minimizar" if minimize else "Maximizar"
        if len(c) == 0:
            return f"{direction}: Z = 0"
        
        obj_text = f"{direction}: Z = "
        c0_val = float(c[0])  # Convert to Python scalar
        if abs(c0_val) > 1e-10:  # Use absolute value comparison for numerical stability
            if abs(c0_val - 1) < 1e-10:
                obj_text += "x₁"
            elif abs(c0_val + 1) < 1e-10:
                obj_text += "-x₁"
            else:
                obj_text += f"{c0_val:.2g}x₁"
                
                for i in range(1, len(c)):
                    ci_val = float(c[i])  # Convert to Python scalar
                    if abs(ci_val) > 1e-10:  # Use absolute value comparison for numerical stability
                        if ci_val > 0:
                            if abs(ci_val - 1) < 1e-10:
                                obj_text += f" + x₍{i+1}₎"
                            else:
                                obj_text += f" + {ci_val:.2g}x₍{i+1}₎"
                        else:
                            if abs(ci_val + 1) < 1e-10:
                                obj_text += f" - x₍{i+1}₎"
                            else:
                                obj_text += f" - {abs(ci_val):.2g}x₍{i+1}₎"
        return obj_text
    
    def format_constraint(self, A_row, b_val, constraint_num):
        """Format a constraint string"""
        if len(A_row) == 0:
            return f"0 ≤ {b_val}"
        
        constraint_text = ""
        first_term = True
        
        for j, coeff in enumerate(A_row):
            coeff_val = float(coeff)  # Convert to Python scalar
            if abs(coeff_val) > 1e-10:  # Use absolute value comparison for numerical stability
                if not first_term:
                    if coeff_val > 0:
                        if abs(coeff_val - 1) < 1e-10:
                            constraint_text += f" + x₍{j+1}₎"
                        else:
                            constraint_text += f" + {coeff_val:.2g}x₍{j+1}₎"
                    else:
                        if abs(coeff_val + 1) < 1e-10:
                            constraint_text += f" - x₍{j+1}₎"
                        else:
                            constraint_text += f" - {abs(coeff_val):.2g}x₍{j+1}₎"
                else:
                    if abs(coeff_val - 1) < 1e-10:
                        constraint_text += f"x₍{j+1}₎"
                    elif abs(coeff_val + 1) < 1e-10:
                        constraint_text += f"-x₍{j+1}₎"
                    else:
                        constraint_text += f"{coeff_val:.2g}x₍{j+1}₎"
                    first_term = False
        
        constraint_text += f" ≤ {b_val}"
        return constraint_text
    
    def show_tableau_iterations(self, tableau_history, pivot_history):
        """Show the tableau iterations with pivot highlighting"""
        for i, tableau in enumerate(tableau_history):
            self.show_single_tableau(tableau, i, pivot_history)
            if i < len(tableau_history) - 1:
                self.wait(1.5)
    
    def show_single_tableau(self, tableau, iteration, pivot_history):
        """Display a single tableau with optional pivot highlighting"""
        # Clear previous tableau
        if hasattr(self, 'current_tableau_group'):
            self.play(FadeOut(self.current_tableau_group))
        
        # Create title
        title_text = f"Iteración {iteration + 1}"
        if iteration < len(pivot_history):
            pivot_row, pivot_col = pivot_history[iteration]
            title_text += f" - Pivote: ({pivot_row + 1}, {pivot_col + 1})"
        
        iteration_title = Text(title_text, font_size=24, color=BLUE)
        iteration_title.to_edge(UP, buff=1)
        
        # Create tableau
        tableau_group = VGroup()
        tableau_group.add(iteration_title)
        
        # Create table
        rows, cols = len(tableau), len(tableau[0])
        cell_height = 0.4
        cell_width = 0.8
        
        # Create cells
        for row in range(rows):
            for col in range(cols):
                # Create cell rectangle
                cell = Rectangle(
                    height=cell_height, 
                    width=cell_width,
                    color=WHITE,
                    fill_opacity=0.1 if (row + col) % 2 == 0 else 0.05
                )
                
                # Highlight pivot cell
                if (iteration < len(pivot_history) and 
                    row == pivot_history[iteration][0] and 
                    col == pivot_history[iteration][1]):
                    cell.set_fill(YELLOW, opacity=0.3)
                    cell.set_stroke(YELLOW, width=3)
                
                # Position cell
                cell.move_to([
                    (col - cols/2 + 0.5) * cell_width,
                    -(row - rows/2 + 0.5) * cell_height - 1,
                    0
                ])
                
                # Add value text
                value = tableau[row][col]
                if abs(value) < 1e-10:
                    value = 0
                value_text = Text(f"{value:.2f}", font_size=16)
                value_text.move_to(cell.get_center())
                
                tableau_group.add(cell, value_text)
        
        # Scale and position tableau
        tableau_group.scale(0.7)
        
        self.current_tableau_group = tableau_group
        self.play(Write(tableau_group), run_time=1.5)
    
    def show_final_solution(self, solution, z_opt, minimize):
        """Display the final optimal solution"""
        if hasattr(self, 'current_tableau_group'):
            self.play(FadeOut(self.current_tableau_group))
        
        # Solution title
        solution_title = Text("¡Solución Óptima Encontrada!", font_size=32, color=GREEN)
        solution_title.to_edge(UP, buff=1)
        self.play(Write(solution_title))
        
        # Solution values
        solution_group = VGroup()
        
        # Variables
        var_title = Text("Variables:", font_size=24, color=BLUE)
        solution_group.add(var_title)
        
        for i, val in enumerate(solution):
            var_text = Text(f"x₍{i+1}₎ = {val:.4f}", font_size=22)
            if i == 0:
                var_text.next_to(var_title, DOWN, buff=0.3)
            else:
                var_text.next_to(solution_group[-1], DOWN, buff=0.2)
            var_text.align_to(var_title, LEFT).shift(RIGHT*0.5)
            solution_group.add(var_text)
        
        # Optimal value
        direction = "mínimo" if minimize else "máximo"
        opt_text = Text(f"Valor {direction}: Z* = {z_opt:.4f}", 
                       font_size=26, color=GREEN)
        opt_text.next_to(solution_group, DOWN, buff=0.5)
        solution_group.add(opt_text)
        
        # Center the solution group
        solution_group.move_to(ORIGIN)
        
        self.play(Write(solution_group))
        
        # Add celebration effect
        self.add_celebration_effect()
    
    def add_celebration_effect(self):
        """Add a simple celebration effect"""
        # Create some sparkles
        sparkles = VGroup()
        for _ in range(20):
            sparkle = Star(n=4, outer_radius=0.1, color=YELLOW)
            sparkle.move_to([
                np.random.uniform(-6, 6),
                np.random.uniform(-3, 3),
                0
            ])
            sparkles.add(sparkle)
        
        self.play(
            LaggedStart(*[FadeIn(sparkle) for sparkle in sparkles], lag_ratio=0.1),
            run_time=1
        )
        self.play(
            LaggedStart(*[FadeOut(sparkle) for sparkle in sparkles], lag_ratio=0.1),
            run_time=1
        )


class TableauVisualization(Scene):
    """Specialized scene for showing tableau transformations"""
    
    def construct(self):
        with open("problem_data.json", "r") as f:
            data = json.load(f)
        
        tableau_history = data.get("tableau_history", [])
        pivot_history = data.get("pivot_history", [])
        
        if len(tableau_history) == 0:
            # Show message if no tableau history
            message = Text("No hay historial de tablas disponible", font_size=24)
            self.play(Write(message))
            self.wait(2)
            return
        
        # Title
        title = Text("Transformaciones del Tableau Simplex", font_size=30, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        
        # Show each tableau transformation
        for i in range(len(tableau_history)):
            self.show_tableau_step(tableau_history[i], pivot_history, i)
            if i < len(tableau_history) - 1:
                self.wait(2)
    
    def show_tableau_step(self, tableau, pivot_history, step):
        """Show a single tableau step with detailed annotations"""
        # Clear previous content
        if hasattr(self, 'current_content'):
            self.play(FadeOut(self.current_content))
        
        content_group = VGroup()
        
        # Step title
        step_title = Text(f"Paso {step + 1}", font_size=24, color=YELLOW)
        step_title.to_edge(UP, buff=1.5)
        content_group.add(step_title)
        
        # Create detailed tableau
        tableau_visual = self.create_detailed_tableau(tableau, pivot_history, step)
        tableau_visual.next_to(step_title, DOWN, buff=0.5)
        content_group.add(tableau_visual)
        
        # Add pivot explanation if available
        if step < len(pivot_history):
            pivot_row, pivot_col = pivot_history[step]
            explanation = self.create_pivot_explanation(pivot_row, pivot_col, tableau)
            explanation.next_to(tableau_visual, DOWN, buff=0.3)
            content_group.add(explanation)
        
        self.current_content = content_group
        self.play(Write(content_group))
    
    def create_detailed_tableau(self, tableau, pivot_history, step):
        """Create a detailed tableau with labels and highlighting"""
        tableau_group = VGroup()
        
        rows, cols = len(tableau), len(tableau[0])
        cell_size = 0.6
        
        # Create table with borders
        for row in range(rows):
            for col in range(cols):
                # Cell
                cell = Rectangle(
                    height=cell_size, 
                    width=cell_size,
                    color=WHITE,
                    stroke_width=1
                )
                
                # Highlight pivot
                if (step < len(pivot_history) and 
                    row == pivot_history[step][0] and 
                    col == pivot_history[step][1]):
                    cell.set_fill(RED, opacity=0.3)
                    cell.set_stroke(RED, width=3)
                elif (step < len(pivot_history) and 
                      (row == pivot_history[step][0] or col == pivot_history[step][1])):
                    cell.set_fill(BLUE, opacity=0.1)
                
                # Position
                cell.move_to([
                    (col - cols/2 + 0.5) * cell_size,
                    -(row - rows/2 + 0.5) * cell_size,
                    0
                ])
                
                # Value
                value = tableau[row][col]
                if abs(value) < 1e-10:
                    value = 0
                
                value_text = Text(f"{value:.2f}", font_size=14)
                value_text.move_to(cell.get_center())
                
                tableau_group.add(cell, value_text)
        
        return tableau_group
    
    def create_pivot_explanation(self, pivot_row, pivot_col, tableau):
        """Create explanation for the current pivot operation"""
        explanation_group = VGroup()
        
        pivot_value = tableau[pivot_row][pivot_col]
        
        # Pivot info
        pivot_info = Text(
            f"Elemento pivote: ({pivot_row + 1}, {pivot_col + 1}) = {pivot_value:.3f}",
            font_size=18,
            color=RED
        )
        explanation_group.add(pivot_info)
        
        # Operation description
        operation_text = Text(
            "Se normalizará la fila pivote y se eliminarán otros elementos de la columna",
            font_size=16,
            color=YELLOW
        )
        operation_text.next_to(pivot_info, DOWN, buff=0.2)
        explanation_group.add(operation_text)
        
        return explanation_group
