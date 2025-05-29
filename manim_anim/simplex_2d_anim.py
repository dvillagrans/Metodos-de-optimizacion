from manim import *
import json
import numpy as np
from scipy.optimize import linprog

class Simplex2DAnim(Scene):
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
        
        # Only proceed if it's a 2D problem
        if len(c) != 2:
            self.show_error_message()
            return
        
        # Create title
        title = Text("Método Simplex en 2D", font_size=36, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Setup coordinate system
        axes = Axes(
            x_range=[-1, 8, 1],
            y_range=[-1, 8, 1],
            x_length=6,
            y_length=6,
            axis_config={"color": WHITE, "include_numbers": True}
        )
        axes_labels = axes.get_axis_labels(x_label="x_1", y_label="x_2")
        
        self.play(Create(axes), Write(axes_labels))
        self.wait(1)
        
        # Show objective function
        self.show_objective_function(c, minimize, axes)
        
        # Draw constraints and feasible region
        constraint_lines, feasible_region = self.draw_constraints_and_region(A, b, axes)
        
        # Find and show vertices of feasible region
        vertices = self.find_feasible_vertices(A, b)
        vertex_dots = self.show_vertices(vertices, axes)
        
        # Animate simplex path through vertices
        self.animate_simplex_path(vertices, solution, axes, c, minimize)
        
        # Show final solution
        self.show_final_solution(solution, z_opt, axes, minimize)
        
        self.wait(3)
    
    def show_error_message(self):
        """Show error message for non-2D problems"""
        error_text = Text("Esta animación requiere un problema 2D", font_size=32, color=RED)
        self.play(Write(error_text))
        self.wait(2)
    
    def show_objective_function(self, c, minimize, axes):
        """Display the objective function"""
        obj_type = "Minimizar" if minimize else "Maximizar"
        obj_text = f"{obj_type}: Z = {c[0]}x₁ + {c[1]}x₂"
        obj_label = Text(obj_text, font_size=24, color=GREEN)
        obj_label.to_corner(UL).shift(DOWN * 1.5)
        
        self.play(Write(obj_label))
        self.wait(1)
        
        return obj_label
    
    def draw_constraints_and_region(self, A, b, axes):
        """Draw constraint lines and shade feasible region"""
        constraint_lines = VGroup()
        constraint_labels = VGroup()
        
        # Draw each constraint line
        for i, (a_row, b_val) in enumerate(zip(A, b)):
            # Find intersection points with axes bounds
            x_vals = np.linspace(-1, 8, 100)
            if abs(a_row[1]) > 1e-10:  # Avoid division by zero
                y_vals = (b_val - a_row[0] * x_vals) / a_row[1]
                # Filter points within axes range
                valid_mask = (y_vals >= -1) & (y_vals <= 8)
                x_vals = x_vals[valid_mask]
                y_vals = y_vals[valid_mask]
                
                if len(x_vals) > 1:
                    line_points = [axes.coords_to_point(x, y) for x, y in zip(x_vals, y_vals)]
                    constraint_line = Line(line_points[0], line_points[-1], color=YELLOW)
                    constraint_lines.add(constraint_line)
                    
                    # Add constraint label
                    constraint_text = f"{a_row[0]}x₁ + {a_row[1]}x₂ ≤ {b_val}"
                    label = Text(constraint_text, font_size=16, color=YELLOW)
                    label.next_to(constraint_line, UP, buff=0.1)
                    constraint_labels.add(label)
        
        # Animate constraint lines
        for line, label in zip(constraint_lines, constraint_labels):
            self.play(Create(line), Write(label), run_time=1)
            self.wait(0.5)
        
        # Create and show feasible region
        feasible_region = self.create_feasible_region(A, b, axes)
        if feasible_region:
            self.play(FadeIn(feasible_region), run_time=2)
            self.wait(1)
        
        return constraint_lines, feasible_region
    
    def create_feasible_region(self, A, b, axes):
        """Create the feasible region polygon"""
        vertices = self.find_feasible_vertices(A, b)
        if len(vertices) < 3:
            return None
        
        # Sort vertices in counterclockwise order
        center = np.mean(vertices, axis=0)
        angles = np.arctan2(vertices[:, 1] - center[1], vertices[:, 0] - center[0])
        sorted_indices = np.argsort(angles)
        sorted_vertices = vertices[sorted_indices]
        
        # Convert to manim points
        polygon_points = [axes.coords_to_point(v[0], v[1]) for v in sorted_vertices]
        
        # Create polygon
        feasible_region = Polygon(*polygon_points, fill_opacity=0.3, fill_color=BLUE, stroke_color=BLUE)
        
        return feasible_region
    
    def find_feasible_vertices(self, A, b):
        """Find vertices of the feasible region"""
        vertices = []
        n_constraints = len(A)
        
        # Check intersection of each pair of constraints
        for i in range(n_constraints):
            for j in range(i + 1, n_constraints):
                # Solve system of equations for constraints i and j
                A_sys = np.array([A[i], A[j]])
                b_sys = np.array([b[i], b[j]])
                
                try:
                    vertex = np.linalg.solve(A_sys, b_sys)
                    
                    # Check if vertex satisfies all constraints
                    if self.is_feasible(vertex, A, b):
                        vertices.append(vertex)
                except np.linalg.LinAlgError:
                    continue
        
        # Add axis intersections
        for i in range(n_constraints):
            # Intersection with x-axis (x2 = 0)
            if abs(A[i][0]) > 1e-10:
                x1 = b[i] / A[i][0]
                vertex = np.array([x1, 0])
                if self.is_feasible(vertex, A, b):
                    vertices.append(vertex)
            
            # Intersection with y-axis (x1 = 0)
            if abs(A[i][1]) > 1e-10:
                x2 = b[i] / A[i][1]
                vertex = np.array([0, x2])
                if self.is_feasible(vertex, A, b):
                    vertices.append(vertex)
        
        # Add origin if feasible
        if self.is_feasible(np.array([0, 0]), A, b):
            vertices.append(np.array([0, 0]))
        
        # Remove duplicates
        if vertices:
            vertices = np.array(vertices)
            unique_vertices = []
            for v in vertices:
                is_duplicate = False
                for uv in unique_vertices:
                    if np.linalg.norm(v - uv) < 1e-6:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_vertices.append(v)
            return np.array(unique_vertices) if unique_vertices else np.array([[0, 0]])
        
        return np.array([[0, 0]])
    
    def is_feasible(self, point, A, b):
        """Check if a point satisfies all constraints"""
        if point[0] < 0 or point[1] < 0:  # Non-negativity constraints
            return False
        
        for i in range(len(A)):
            if np.dot(A[i], point) > b[i] + 1e-6:  # Allow small numerical error
                return False
        
        return True
    
    def show_vertices(self, vertices, axes):
        """Show vertices of the feasible region"""
        vertex_dots = VGroup()
        vertex_labels = VGroup()
        
        for i, vertex in enumerate(vertices):
            dot = Dot(axes.coords_to_point(vertex[0], vertex[1]), color=RED, radius=0.08)
            label = Text(f"({vertex[0]:.1f}, {vertex[1]:.1f})", font_size=14, color=WHITE)
            label.next_to(dot, UR, buff=0.1)
            
            vertex_dots.add(dot)
            vertex_labels.add(label)
            
            self.play(Create(dot), Write(label), run_time=0.5)
        
        self.wait(1)
        return vertex_dots, vertex_labels
    
    def animate_simplex_path(self, vertices, solution, axes, c, minimize):
        """Animate the simplex algorithm path through vertices"""
        # Calculate objective function values at vertices
        obj_values = []
        for vertex in vertices:
            obj_val = np.dot(c, vertex)
            if minimize:
                obj_val = -obj_val
            obj_values.append(obj_val)
        
        # Sort vertices by objective function value (for simplex path simulation)
        sorted_indices = np.argsort(obj_values)
        if not minimize:
            sorted_indices = sorted_indices[::-1]  # Reverse for maximization
        
        # Create moving dot to show simplex path
        moving_dot = Dot(axes.coords_to_point(vertices[sorted_indices[0]][0], vertices[sorted_indices[0]][1]), 
                        color=ORANGE, radius=0.12)
        
        path_text = Text("Recorrido del Simplex", font_size=24, color=ORANGE)
        path_text.to_corner(UR).shift(DOWN * 1.5)
        
        self.play(Create(moving_dot), Write(path_text))
        self.wait(1)
        
        # Animate movement through vertices
        for i in range(1, len(sorted_indices)):
            current_vertex = vertices[sorted_indices[i]]
            target_point = axes.coords_to_point(current_vertex[0], current_vertex[1])
            
            # Show objective function value
            obj_val = np.dot(c, current_vertex)
            value_text = Text(f"Z = {obj_val:.2f}", font_size=20, color=ORANGE)
            value_text.next_to(moving_dot, DOWN, buff=0.3)
            
            self.play(
                moving_dot.animate.move_to(target_point),
                Write(value_text),
                run_time=1.5
            )
            self.wait(1)
            self.play(FadeOut(value_text), run_time=0.5)
        
        return moving_dot
    
    def show_final_solution(self, solution, z_opt, axes, minimize):
        """Show the final optimal solution"""
        # Create optimal point
        optimal_dot = Dot(axes.coords_to_point(solution[0], solution[1]), 
                         color=GOLD, radius=0.15)
        
        # Create solution text
        solution_text = Text(f"Solución Óptima: ({solution[0]:.2f}, {solution[1]:.2f})", 
                           font_size=24, color=GOLD)
        solution_text.to_corner(DR).shift(UP * 1.5)
        
        optimal_value_text = Text(f"Valor Óptimo: Z = {z_opt:.2f}", 
                                font_size=24, color=GOLD)
        optimal_value_text.next_to(solution_text, DOWN, buff=0.3)
        
        # Animate final solution
        self.play(
            Create(optimal_dot),
            Write(solution_text),
            Write(optimal_value_text),
            run_time=2
        )
        
        # Flash effect for emphasis
        self.play(Flash(optimal_dot, color=GOLD), run_time=1)
        self.wait(1)
        
        return optimal_dot
