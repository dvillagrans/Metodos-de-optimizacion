from manim import *
import json
import numpy as np

class GranMDosFasesAnim(Scene):
    def construct(self):
        # Load problem data
        with open("problem_data.json", "r") as f:
            data = json.load(f)
        
        method = data.get("method", "simplex")
        tableau_history = data.get("tableau_history", [])
        artificial_vars = data.get("artificial_variables", [])
        phase_transition = data.get("phase_transition", None)
        
        if method not in ["granm", "dosfases"]:
            self.show_error_message()
            return
        
        # Create title based on method
        method_names = {
            "granm": "Método de la Gran M",
            "dosfases": "Método de Dos Fases"
        }
        
        title = Text(method_names[method], font_size=36, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        if method == "granm":
            self.animate_gran_m_method(tableau_history, artificial_vars)
        else:
            self.animate_dos_fases_method(tableau_history, artificial_vars, phase_transition)
        
        self.wait(3)
    
    def show_error_message(self):
        """Show error message for wrong method"""
        error_text = Text("Esta animación requiere método Gran M o Dos Fases", font_size=28, color=RED)
        self.play(Write(error_text))
        self.wait(2)
    
    def animate_gran_m_method(self, tableau_history, artificial_vars):
        """Animate the Gran M method showing artificial variables"""
        # Introduction to Gran M
        intro_text = Text("El Método de la Gran M utiliza variables artificiales", 
                         font_size=24, color=YELLOW)
        intro_text.move_to(ORIGIN).shift(UP * 2)
        self.play(Write(intro_text))
        self.wait(2)
        
        # Show artificial variables concept
        if artificial_vars:
            self.show_artificial_variables_concept(artificial_vars)
        
        # Show tableau evolution
        if tableau_history:
            self.animate_tableau_sequence(tableau_history, "Gran M")
        
        # Show M penalty explanation
        self.show_m_penalty_explanation()
    
    def animate_dos_fases_method(self, tableau_history, artificial_vars, phase_transition):
        """Animate the Dos Fases method showing phase transition"""
        # Phase 1 introduction
        phase1_text = Text("FASE I: Eliminación de Variables Artificiales", 
                          font_size=28, color=ORANGE)
        phase1_text.move_to(ORIGIN).shift(UP * 2)
        self.play(Write(phase1_text))
        self.wait(2)
        
        # Show artificial variables
        if artificial_vars:
            self.show_artificial_variables_concept(artificial_vars)
        
        # Show Phase 1 tableaus
        if tableau_history and phase_transition:
            phase1_tableaus = tableau_history[:phase_transition]
            self.animate_tableau_sequence(phase1_tableaus, "Fase I")
            
            # Phase transition animation
            self.animate_phase_transition()
            
            # Phase 2
            phase2_text = Text("FASE II: Optimización del Problema Original", 
                              font_size=28, color=GREEN)
            phase2_text.move_to(ORIGIN).shift(UP * 2)
            self.play(Transform(phase1_text, phase2_text))
            self.wait(2)
            
            # Show Phase 2 tableaus
            phase2_tableaus = tableau_history[phase_transition:]
            self.animate_tableau_sequence(phase2_tableaus, "Fase II")
    
    def show_artificial_variables_concept(self, artificial_vars):
        """Show concept of artificial variables"""
        concept_text = Text("Variables Artificiales:", font_size=24, color=PINK)
        concept_text.move_to(ORIGIN)
        
        # Show artificial variables
        vars_text = ""
        for i, var in enumerate(artificial_vars):
            vars_text += f"a{i+1}"
            if i < len(artificial_vars) - 1:
                vars_text += ", "
        
        vars_display = Text(f"[{vars_text}]", font_size=20, color=PINK)
        vars_display.next_to(concept_text, DOWN, buff=0.5)
        
        explanation = Text("Se añaden temporalmente para obtener solución inicial factible", 
                          font_size=18, color=WHITE)
        explanation.next_to(vars_display, DOWN, buff=0.5)
        
        self.play(Write(concept_text))
        self.wait(1)
        self.play(Write(vars_display))
        self.wait(1)
        self.play(Write(explanation))
        self.wait(2)
        
        # Fade out
        self.play(FadeOut(concept_text), FadeOut(vars_display), FadeOut(explanation))
    
    def animate_tableau_sequence(self, tableaus, phase_name):
        """Animate sequence of tableaus with transitions"""
        if not tableaus:
            return
        
        for i, tableau in enumerate(tableaus):
            # Create tableau table
            tableau_table = self.create_tableau_table(tableau, f"{phase_name} - Iteración {i+1}")
            
            if i == 0:
                self.play(Create(tableau_table), run_time=2)
            else:
                # Transform from previous tableau
                self.play(Transform(current_tableau, tableau_table), run_time=2)
            
            current_tableau = tableau_table
            self.wait(1.5)
            
            # Highlight pivot element if available
            if i < len(tableaus) - 1:
                self.highlight_pivot_element(tableau)
                self.wait(1)
        
        # Keep final tableau visible
        self.wait(2)
        self.play(FadeOut(current_tableau))
    
    def create_tableau_table(self, tableau, title):
        """Create a visual representation of a simplex tableau"""
        # Create title
        table_title = Text(title, font_size=20, color=BLUE)
        table_title.to_edge(UP).shift(DOWN * 1.5)
        
        # Create table structure
        rows = len(tableau)
        cols = len(tableau[0]) if rows > 0 else 0
        
        # Create table as a group of text elements
        table_group = VGroup()
        table_group.add(table_title)
        
        # Create grid of values
        cell_width = 0.8
        cell_height = 0.4
        
        for i in range(rows):
            row_group = VGroup()
            for j in range(cols):
                value = tableau[i][j]
                if isinstance(value, (int, float)):
                    cell_text = Text(f"{value:.2f}", font_size=14, color=WHITE)
                else:
                    cell_text = Text(str(value), font_size=14, color=WHITE)
                
                # Position cell
                cell_text.move_to([
                    (j - cols/2) * cell_width,
                    -(i - rows/2) * cell_height - 1,
                    0
                ])
                
                # Create cell background
                cell_rect = Rectangle(
                    width=cell_width * 0.9,
                    height=cell_height * 0.9,
                    color=GRAY,
                    fill_opacity=0.1
                )
                cell_rect.move_to(cell_text.get_center())
                
                row_group.add(cell_rect, cell_text)
            
            table_group.add(row_group)
        
        return table_group
    
    def highlight_pivot_element(self, tableau):
        """Highlight the pivot element in the tableau"""
        # For demonstration, highlight a random element
        # In real implementation, this would highlight the actual pivot
        if len(tableau) > 1 and len(tableau[0]) > 1:
            pivot_highlight = Circle(radius=0.3, color=YELLOW, fill_opacity=0.3)
            pivot_highlight.move_to([0, -1, 0])  # Approximate position
            
            self.play(Create(pivot_highlight))
            self.wait(0.5)
            self.play(FadeOut(pivot_highlight))
    
    def show_m_penalty_explanation(self):
        """Show explanation of M penalty in Gran M method"""
        explanation_title = Text("Penalización con Gran M", font_size=24, color=RED)
        explanation_title.move_to(ORIGIN).shift(UP * 1.5)
        
        penalty_text = Text("M es un número muy grande que penaliza las variables artificiales", 
                           font_size=18, color=WHITE)
        penalty_text.next_to(explanation_title, DOWN, buff=0.5)
        
        formula_text = Text("Objetivo modificado: min Z + M·(suma de variables artificiales)", 
                           font_size=16, color=YELLOW)
        formula_text.next_to(penalty_text, DOWN, buff=0.5)
        
        self.play(Write(explanation_title))
        self.wait(1)
        self.play(Write(penalty_text))
        self.wait(1)
        self.play(Write(formula_text))
        self.wait(2)
        
        # Fade out
        self.play(FadeOut(explanation_title), FadeOut(penalty_text), FadeOut(formula_text))
    
    def animate_phase_transition(self):
        """Animate transition between phases in Dos Fases method"""
        transition_title = Text("TRANSICIÓN ENTRE FASES", font_size=32, color=ORANGE)
        transition_title.move_to(ORIGIN)
        
        # Create transition effect
        transition_rect = Rectangle(
            width=config.frame_width,
            height=config.frame_height,
            fill_color=ORANGE,
            fill_opacity=0.3,
            stroke_width=0
        )
        
        step1 = Text("1. Verificar que todas las variables artificiales = 0", 
                    font_size=18, color=WHITE)
        step1.next_to(transition_title, DOWN, buff=0.8)
        
        step2 = Text("2. Eliminar columnas de variables artificiales", 
                    font_size=18, color=WHITE)
        step2.next_to(step1, DOWN, buff=0.3)
        
        step3 = Text("3. Restaurar función objetivo original", 
                    font_size=18, color=WHITE)
        step3.next_to(step2, DOWN, buff=0.3)
        
        step4 = Text("4. Continuar con optimización", 
                    font_size=18, color=WHITE)
        step4.next_to(step3, DOWN, buff=0.3)
        
        # Animate transition
        self.play(FadeIn(transition_rect), run_time=1)
        self.play(Write(transition_title), run_time=1)
        self.wait(1)
        
        # Show steps one by one
        steps = [step1, step2, step3, step4]
        for step in steps:
            self.play(Write(step), run_time=1)
            self.wait(0.8)
        
        self.wait(2)
        
        # Fade out transition
        self.play(
            FadeOut(transition_rect),
            FadeOut(transition_title),
            *[FadeOut(step) for step in steps],
            run_time=2
        )


class TableauVisualization(Scene):
    """Helper class for creating detailed tableau visualizations"""
    
    def create_detailed_tableau(self, tableau_data, title, highlight_pivot=None):
        """Create a detailed tableau with headers and formatting"""
        # This would contain more sophisticated tableau creation
        # with proper headers, basis variables, etc.
        pass
    
    def animate_row_operations(self, from_tableau, to_tableau, pivot_row, pivot_col):
        """Animate the row operations in simplex method"""
        # This would show the actual mathematical operations
        # being performed on the tableau
        pass
