from manim import *
import json
import numpy as np

class BasicSimplexAnim(Scene):
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
        method = data.get("method", "simplex")
        
        # Create title animation
        method_names = {
            "simplex": "Método Simplex",
            "granm": "Método Gran M",
            "dosfases": "Método Dos Fases"
        }
        
        title = Text(method_names.get(method, "Método Simplex"), font_size=40)
        title.to_edge(UP)
        
        # Animated title entrance
        self.play(Write(title), run_time=2)
        self.wait(0.5)
        
        # Problem description with color
        problem_type = "Minimización" if minimize else "Maximización"
        prob_desc = Text(f"Problema de {problem_type}", font_size=30, color=BLUE)
        prob_desc.next_to(title, DOWN)
        self.play(FadeIn(prob_desc, shift=DOWN), run_time=1.5)
        self.wait(0.5)
        
        # Objective function with animation
        obj_text = ""
        if len(c) > 0:
            obj_text = f"Z = {float(c[0])}x₁"
            for i in range(1, len(c)):
                c_val = float(c[i])
                if c_val >= 0:
                    obj_text += f" + {c_val}x₍{i+1}₎"
                else:
                    obj_text += f" - {abs(c_val)}x₍{i+1}₎"
        
        obj_func = Text(obj_text, font_size=24, color=GREEN)
        obj_func.next_to(prob_desc, DOWN, buff=0.5)
        self.play(Write(obj_func), run_time=2)
        self.wait(1)
        
        # Constraints section
        constraints_title = Text("Sujeto a:", font_size=24, color=YELLOW)
        constraints_title.next_to(obj_func, DOWN, buff=0.5)
        constraints_title.align_to(obj_func, LEFT)
        self.play(Write(constraints_title), run_time=1)
        
        # Display each constraint with animation
        constraints_group = VGroup()
        for i in range(len(b)):
            constraint_text = ""
            if len(A[i]) > 0:
                constraint_text = f"{float(A[i][0])}x₁"
                for j in range(1, len(A[i])):
                    a_val = float(A[i][j])
                    if a_val >= 0:
                        constraint_text += f" + {a_val}x₍{j+1}₎"
                    else:
                        constraint_text += f" - {abs(a_val)}x₍{j+1}₎"
                constraint_text += f" ≤ {float(b[i])}"
            
            constraint = Text(constraint_text, font_size=20)
            if i == 0:
                constraint.next_to(constraints_title, DOWN, buff=0.3)
                constraint.align_to(constraints_title, LEFT).shift(RIGHT*0.5)
            else:
                constraint.next_to(constraints_group[-1], DOWN, buff=0.2)
                constraint.align_to(constraints_group[-1], LEFT)
            
            constraints_group.add(constraint)
            self.play(FadeIn(constraint, shift=UP), run_time=1)
            self.wait(0.3)
        
        self.wait(1)
        
        # Transition animation
        self.play(
            *[FadeOut(mob, shift=LEFT) for mob in [prob_desc, obj_func, constraints_title, constraints_group]], 
            run_time=2
        )
        
        # Solution section with highlighted appearance
        solution_title = Text("Solución Óptima:", font_size=36, color=RED)
        solution_title.move_to(ORIGIN).shift(UP)
        
        # Create highlight rectangle
        highlight_rect = SurroundingRectangle(solution_title, color=RED, buff=0.3)
        
        self.play(
            Write(solution_title),
            Create(highlight_rect),
            run_time=2
        )
        self.wait(0.5)
        
        # Display solution values with animation
        solution_text = ""
        for i in range(len(solution)):
            solution_text += f"x₍{i+1}₎ = {solution[i]:.4f}"
            if i < len(solution) - 1:
                solution_text += ", "
        
        sol_values = Text(solution_text, font_size=28, color=WHITE)
        sol_values.next_to(solution_title, DOWN, buff=0.8)
        self.play(Write(sol_values), run_time=2)
        self.wait(0.5)
        
        # Optimal value with emphasis
        opt_text = f"Valor óptimo: Z = {z_opt:.4f}"
        opt_value = Text(opt_text, font_size=32, color=GOLD)
        opt_value.next_to(sol_values, DOWN, buff=0.8)
        
        # Create emphasis rectangle
        opt_rect = SurroundingRectangle(opt_value, color=GOLD, buff=0.2)
        
        self.play(
            Write(opt_value),
            Create(opt_rect),
            run_time=2
        )
        
        # Flash effect for emphasis
        self.play(Flash(opt_value, color=GOLD), run_time=1)
        
        # Final animation - pulse all elements
        final_group = VGroup(solution_title, highlight_rect, sol_values, opt_value, opt_rect)
        self.play(
            final_group.animate.scale(1.1).set_opacity(0.9),
            run_time=1
        )
        self.play(
            final_group.animate.scale(1/1.1).set_opacity(1),
            run_time=1
        )
        
        # Hold final frame
        self.wait(3)
