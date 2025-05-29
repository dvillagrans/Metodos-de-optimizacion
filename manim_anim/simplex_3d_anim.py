from manim import *
import json
import numpy as np

class Simplex3DAnim(ThreeDScene):
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
        
        # Only proceed if it's a 3D problem
        if len(c) != 3:
            self.show_error_message()
            return
        
        # Setup 3D scene
        self.set_camera_orientation(phi=75 * DEGREES, theta=45 * DEGREES)
        
        # Create title
        title = Text("Método Simplex en 3D", font_size=36, color=BLUE)
        title.to_edge(UP)
        self.add_fixed_in_frame_mobjects(title)
        self.play(Write(title))
        self.wait(1)
        
        # Setup 3D coordinate system
        axes = ThreeDAxes(
            x_range=[-1, 6, 1],
            y_range=[-1, 6, 1],
            z_range=[-1, 6, 1],
            x_length=6,
            y_length=6,
            z_length=6,
            axis_config={"color": WHITE}
        )
        
        # Add axis labels
        x_label = Text("x₁", font_size=20, color=WHITE)
        y_label = Text("x₂", font_size=20, color=WHITE)
        z_label = Text("x₃", font_size=20, color=WHITE)
        
        x_label.next_to(axes.x_axis.get_end(), RIGHT)
        y_label.next_to(axes.y_axis.get_end(), UP)
        z_label.next_to(axes.z_axis.get_end(), OUT)
        
        self.play(Create(axes))
        self.add_fixed_in_frame_mobjects(x_label, y_label, z_label)
        self.play(Write(x_label), Write(y_label), Write(z_label))
        self.wait(1)
        
        # Show objective function
        self.show_objective_function(c, minimize)
        
        # Draw constraint planes and feasible region
        self.draw_constraint_planes(A, b, axes)
        
        # Find and show vertices of feasible region (polyhedron)
        vertices = self.find_feasible_vertices_3d(A, b)
        vertex_dots = self.show_vertices_3d(vertices, axes)
        
        # Animate simplex path through vertices
        self.animate_simplex_path_3d(vertices, solution, axes, c, minimize)
        
        # Show final solution
        self.show_final_solution_3d(solution, z_opt, axes, minimize)
        
        self.wait(3)
    
    def show_error_message(self):
        """Show error message for non-3D problems"""
        error_text = Text("Esta animación requiere un problema 3D", font_size=32, color=RED)
        self.add_fixed_in_frame_mobjects(error_text)
        self.play(Write(error_text))
        self.wait(2)
    
    def show_objective_function(self, c, minimize):
        """Display the objective function"""
        obj_type = "Minimizar" if minimize else "Maximizar"
        obj_text = f"{obj_type}: Z = {c[0]}x₁ + {c[1]}x₂ + {c[2]}x₃"
        obj_label = Text(obj_text, font_size=20, color=GREEN)
        obj_label.to_corner(UL).shift(DOWN * 1.5)
        
        self.add_fixed_in_frame_mobjects(obj_label)
        self.play(Write(obj_label))
        self.wait(1)
        
        return obj_label
    
    def draw_constraint_planes(self, A, b, axes):
        """Draw constraint planes in 3D"""
        constraint_planes = VGroup()
        
        for i, (a_row, b_val) in enumerate(zip(A, b)):
            # Create a plane for each constraint
            # ax + by + cz = d defines a plane
            plane_color = [YELLOW, ORANGE, PINK, PURPLE, TEAL][i % 5]
            
            # Create a surface representing the constraint plane
            # We'll create a limited portion of the plane within our viewing area
            try:
                plane_surface = self.create_constraint_plane_surface(a_row, b_val, axes, plane_color)
                if plane_surface:
                    constraint_planes.add(plane_surface)
                    self.play(Create(plane_surface), run_time=1.5)
                    self.wait(0.5)
            except:
                continue
        
        return constraint_planes
    
    def create_constraint_plane_surface(self, a_row, b_val, axes, color):
        """Create a surface representing a constraint plane"""
        # Define the plane equation: a[0]*x + a[1]*y + a[2]*z = b_val
        # We'll create a parametric surface within the bounds
        
        def plane_func(u, v):
            # Choose two parameters and solve for the third
            if abs(a_row[2]) > 1e-6:  # Solve for z
                x = u
                y = v
                z = (b_val - a_row[0] * x - a_row[1] * y) / a_row[2]
                return axes.coords_to_point(x, y, z)
            elif abs(a_row[1]) > 1e-6:  # Solve for y
                x = u
                z = v
                y = (b_val - a_row[0] * x - a_row[2] * z) / a_row[1]
                return axes.coords_to_point(x, y, z)
            elif abs(a_row[0]) > 1e-6:  # Solve for x
                y = u
                z = v
                x = (b_val - a_row[1] * y - a_row[2] * z) / a_row[0]
                return axes.coords_to_point(x, y, z)
            else:
                return axes.coords_to_point(0, 0, 0)
        
        # Create the surface with limited range
        try:
            surface = Surface(
                plane_func,
                u_range=[0, 5],
                v_range=[0, 5],
                resolution=(10, 10),
                fill_opacity=0.3,
                stroke_color=color,
                fill_color=color
            )
            return surface
        except:
            return None
    
    def find_feasible_vertices_3d(self, A, b):
        """Find vertices of the 3D feasible region (polyhedron)"""
        vertices = []
        n_constraints = len(A)
        
        # Check intersection of each triplet of constraints
        for i in range(n_constraints):
            for j in range(i + 1, n_constraints):
                for k in range(j + 1, n_constraints):
                    # Solve system of equations for constraints i, j, k
                    A_sys = np.array([A[i], A[j], A[k]])
                    b_sys = np.array([b[i], b[j], b[k]])
                    
                    try:
                        vertex = np.linalg.solve(A_sys, b_sys)
                        
                        # Check if vertex satisfies all constraints
                        if self.is_feasible_3d(vertex, A, b):
                            vertices.append(vertex)
                    except np.linalg.LinAlgError:
                        continue
        
        # Add axis intersections and face intersections
        self.add_boundary_vertices_3d(vertices, A, b)
        
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
                if not is_duplicate and all(coord >= -1e-6 for coord in v):  # Non-negativity
                    unique_vertices.append(v)
            return np.array(unique_vertices) if unique_vertices else np.array([[0, 0, 0]])
        
        return np.array([[0, 0, 0]])
    
    def add_boundary_vertices_3d(self, vertices, A, b):
        """Add vertices on coordinate planes and axes"""
        # Intersections with coordinate planes
        for i in range(len(A)):
            for j in range(i + 1, len(A)):
                # Intersection with xy-plane (z=0)
                try:
                    A_sys = np.array([A[i][:2], A[j][:2]])
                    b_sys = np.array([b[i], b[j]])
                    xy_solution = np.linalg.solve(A_sys, b_sys)
                    vertex = np.array([xy_solution[0], xy_solution[1], 0])
                    if self.is_feasible_3d(vertex, A, b):
                        vertices.append(vertex)
                except:
                    pass
                
                # Intersection with xz-plane (y=0)
                try:
                    A_sys = np.array([[A[i][0], A[i][2]], [A[j][0], A[j][2]]])
                    b_sys = np.array([b[i], b[j]])
                    xz_solution = np.linalg.solve(A_sys, b_sys)
                    vertex = np.array([xz_solution[0], 0, xz_solution[1]])
                    if self.is_feasible_3d(vertex, A, b):
                        vertices.append(vertex)
                except:
                    pass
                
                # Intersection with yz-plane (x=0)
                try:
                    A_sys = np.array([[A[i][1], A[i][2]], [A[j][1], A[j][2]]])
                    b_sys = np.array([b[i], b[j]])
                    yz_solution = np.linalg.solve(A_sys, b_sys)
                    vertex = np.array([0, yz_solution[0], yz_solution[1]])
                    if self.is_feasible_3d(vertex, A, b):
                        vertices.append(vertex)
                except:
                    pass
        
        # Add axis intersections
        for i in range(len(A)):
            # x-axis intersection
            if abs(A[i][0]) > 1e-6:
                x_val = b[i] / A[i][0]
                vertex = np.array([x_val, 0, 0])
                if self.is_feasible_3d(vertex, A, b):
                    vertices.append(vertex)
            
            # y-axis intersection
            if abs(A[i][1]) > 1e-6:
                y_val = b[i] / A[i][1]
                vertex = np.array([0, y_val, 0])
                if self.is_feasible_3d(vertex, A, b):
                    vertices.append(vertex)
            
            # z-axis intersection
            if abs(A[i][2]) > 1e-6:
                z_val = b[i] / A[i][2]
                vertex = np.array([0, 0, z_val])
                if self.is_feasible_3d(vertex, A, b):
                    vertices.append(vertex)
        
        # Add origin if feasible
        if self.is_feasible_3d(np.array([0, 0, 0]), A, b):
            vertices.append(np.array([0, 0, 0]))
    
    def is_feasible_3d(self, point, A, b):
        """Check if a point satisfies all constraints in 3D"""
        if any(coord < -1e-6 for coord in point):  # Non-negativity constraints
            return False
        
        for i in range(len(A)):
            if np.dot(A[i], point) > b[i] + 1e-6:  # Allow small numerical error
                return False
        
        return True
    
    def show_vertices_3d(self, vertices, axes):
        """Show vertices of the 3D feasible region"""
        vertex_dots = VGroup()
        
        for i, vertex in enumerate(vertices):
            dot = Dot3D(
                axes.coords_to_point(vertex[0], vertex[1], vertex[2]), 
                color=RED, 
                radius=0.08
            )
            vertex_dots.add(dot)
            self.play(Create(dot), run_time=0.5)
        
        self.wait(1)
        return vertex_dots
    
    def animate_simplex_path_3d(self, vertices, solution, axes, c, minimize):
        """Animate the simplex algorithm path through vertices in 3D"""
        if len(vertices) == 0:
            return
        
        # Calculate objective function values at vertices
        obj_values = []
        for vertex in vertices:
            obj_val = np.dot(c, vertex)
            if minimize:
                obj_val = -obj_val
            obj_values.append(obj_val)
        
        # Sort vertices by objective function value
        sorted_indices = np.argsort(obj_values)
        if not minimize:
            sorted_indices = sorted_indices[::-1]
        
        # Create moving dot to show simplex path
        start_vertex = vertices[sorted_indices[0]]
        moving_dot = Dot3D(
            axes.coords_to_point(start_vertex[0], start_vertex[1], start_vertex[2]), 
            color=ORANGE, 
            radius=0.15
        )
        
        # Add path text
        path_text = Text("Recorrido del Simplex 3D", font_size=20, color=ORANGE)
        path_text.to_corner(UR).shift(DOWN * 2)
        self.add_fixed_in_frame_mobjects(path_text)
        
        self.play(Create(moving_dot), Write(path_text))
        self.wait(1)
        
        # Animate movement through vertices
        for i in range(1, min(len(sorted_indices), 5)):  # Limit to 5 vertices for clarity
            current_vertex = vertices[sorted_indices[i]]
            target_point = axes.coords_to_point(current_vertex[0], current_vertex[1], current_vertex[2])
            
            self.play(moving_dot.animate.move_to(target_point), run_time=2)
            self.wait(1)
        
        return moving_dot
    
    def show_final_solution_3d(self, solution, z_opt, axes, minimize):
        """Show the final optimal solution in 3D"""
        # Create optimal point
        optimal_dot = Dot3D(
            axes.coords_to_point(solution[0], solution[1], solution[2]), 
            color=GOLD, 
            radius=0.2
        )
        
        # Create solution text
        solution_text = Text(
            f"Solución Óptima:\n({solution[0]:.2f}, {solution[1]:.2f}, {solution[2]:.2f})", 
            font_size=18, 
            color=GOLD
        )
        solution_text.to_corner(DR)
        
        optimal_value_text = Text(f"Valor Óptimo: Z = {z_opt:.2f}", 
                                font_size=18, color=GOLD)
        optimal_value_text.next_to(solution_text, DOWN, buff=0.3)
        
        # Add to fixed frame for readability
        self.add_fixed_in_frame_mobjects(solution_text, optimal_value_text)
        
        # Animate final solution
        self.play(
            Create(optimal_dot),
            Write(solution_text),
            Write(optimal_value_text),
            run_time=2
        )
        
        # Flash effect and camera movement for emphasis
        self.play(Flash(optimal_dot, color=GOLD), run_time=1)
        
        # Rotate camera around the optimal point
        self.begin_ambient_camera_rotation(rate=0.2)
        self.wait(3)
        self.stop_ambient_camera_rotation()
        
        return optimal_dot
