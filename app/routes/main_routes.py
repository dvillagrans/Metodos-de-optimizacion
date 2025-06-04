"""
Rutas principales de la interfaz web.
"""

import json
import time
import logging
from flask import Blueprint, request, render_template, flash, redirect, url_for, make_response

from ..solvers import simplex, granm_solver, dosfases_solver
from ..solvers import SimplexError, GranMError, DosFasesError, UnboundedError, DimensionError, InfeasibleError
from ..utils import (
    convert_numpy_types, validate_dimensions, validate_form_data,
    detect_multiple_solutions, format_multiple_solutions_result
)

logger = logging.getLogger(__name__)

# Main pages blueprint (no URL prefix)
main_bp = Blueprint('main', __name__)


# ===== PÁGINAS PRINCIPALES =====

@main_bp.route('/')
def index():
    return render_template('inicio.html')


@main_bp.route('/simplex')
def simplex_page():
    return render_template('simplex.html')


@main_bp.route('/granm')
def granm_page():
    return render_template('granm.html')


@main_bp.route('/dosfases')
def dosfases_page():
    return render_template('dosfases.html')


# ===== RESOLUCIÓN DE MÉTODOS =====

@main_bp.route('/resolver/simplex', methods=['POST'])
def resolver_simplex():
    try:
        # Obtener datos del formulario y mantenerlos
        form_data = {
            'c': request.form['c'],
            'A': request.form['A'],
            'b': request.form['b'],
            'minimize': request.form.get('minimize') == 'on',
            'track_iterations': request.form.get('track_iterations') == 'on'
        }
        
        # Validar y procesar datos
        processed_data = validate_form_data(form_data)
        c, A, b = processed_data['c'], processed_data['A'], processed_data['b']
        minimize = processed_data['minimize']
        track_iterations = processed_data['track_iterations']
        
        # Validaciones de dimensiones
        validate_dimensions(A, b, c)
        # Resolver
        if track_iterations:
            solution, optimal_value, tableau_history, pivot_history = simplex(
                c, A, b, minimize=minimize, track_iterations=True
            )
            # Convertir valores numpy a tipos nativos de Python antes de serializar
            resultado = {
                'solution': [float(x) for x in solution],
                'optimal_value': float(optimal_value),
                'tableau_history': [t.tolist() for t in tableau_history],
                'pivot_history': [[int(r), int(c)] for r, c in pivot_history],
                'success': True
            }
            # ─ Detectar soluciones múltiples óptimas con nuevo detector ─
            final_tableau = tableau_history[-1]
            n_vars = len(c)
            
            # Usar el nuevo detector mejorado
            multiple_solutions_result = detect_multiple_solutions(final_tableau, n_vars, c, minimize)
            formatted_result = format_multiple_solutions_result(multiple_solutions_result)
            
            # Convertir cualquier tipo numpy en los resultados de soluciones múltiples
            formatted_result = convert_numpy_types(formatted_result)
            
            # Agregar información de soluciones múltiples al resultado
            resultado.update(formatted_result)
        else:
            solution, optimal_value = simplex(c, A, b, minimize=minimize)
            resultado = {
                'solution': [float(x) for x in solution],
                'optimal_value': float(optimal_value),
                'success': True
            }
        
        # Aplicar conversión final de numpy a todos los datos del resultado
        resultado = convert_numpy_types(resultado)
        return render_template('simplex.html', resultado=resultado, form_data=form_data)
        
    except (SimplexError, DimensionError, UnboundedError) as e:
        flash(f'Error en el método Simplex: {str(e)}', 'danger')
        return redirect(url_for('main.simplex_page'))
    except Exception as e:
        flash(f'Error inesperado: {str(e)}', 'error')
        return redirect(url_for('main.simplex_page'))


@main_bp.route('/descargar/simplex_json', methods=['POST'])
def descargar_simplex_json():
    try:
        # Obtener datos del formulario enviados desde el botón de descarga
        resultado_json = request.form.get('resultado_json')
        
        if not resultado_json:
            flash('No hay resultado para descargar', 'error')
            return redirect(url_for('main.simplex_page'))
        
        # Parsear los datos del resultado
        resultado = json.loads(resultado_json)
        
        # Recoger los datos del formulario directamente
        form_data = {
            'c': request.form.get('c', ''),
            'A': request.form.get('A', ''),
            'b': request.form.get('b', ''),
            'minimize': request.form.get('minimize') == 'on',
            'track_iterations': request.form.get('track_iterations') == 'on'
        }
        
        # Crear estructura completa para el JSON
        data_export = {
            'metodo': 'Simplex',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'datos_entrada': {
                'funcion_objetivo': form_data.get('c', ''),
                'matriz_restricciones': form_data.get('A', ''),
                'vector_recursos': form_data.get('b', ''),
                'minimizar': form_data.get('minimize', False),
                'mostrar_iteraciones': form_data.get('track_iterations', False)
            },
            'resultado': resultado
        }
        
        # Crear respuesta de descarga
        response = make_response(json.dumps(data_export, indent=2, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=simplex_resultado_{int(time.time())}.json'
        
        return response
    
    except Exception as e:
        flash(f'Error al descargar: {str(e)}', 'error')
        return redirect(url_for('main.simplex_page'))


@main_bp.route('/resolver/granm', methods=['POST'])
def resolver_granm():
    try:
        # ── 1. Leer campo por campo ──────────────────────
        c_str   = request.form['c']
        A_str   = request.form['A']
        b_str   = request.form['b']

        eq_str  = request.form.get('eq_constraints', '')
        ge_str  = request.form.get('ge_constraints', '')
        min_sw  = request.form.get('minimize')           # 'on' ó None
        iter_sw = request.form.get('track_iterations')   # 'on' ó None
        M_str   = request.form.get('M', '1e6')

        form_data = {
            "c": request.form.get("c"),
            "A": request.form.get("A"),
            "b": request.form.get("b"),
            "M": request.form.get("M"),
            "eq_constraints": request.form.get("eq_constraints"),
            "ge_constraints": request.form.get("ge_constraints"),
            "minimize": request.form.get("minimize"),
            "track_iterations": request.form.get("track_iterations")
        }

        # ── 2. Parseo de listas numéricas ───────────────
        c = [float(x) for x in c_str.split(',') if x.strip()]
        A = [[float(num) for num in row.split(',') if num.strip()]
             for row in A_str.strip().split('\n') if row.strip()]
        b = [float(x) for x in b_str.split(',') if x.strip()]

        # Validaciones básicas
        validate_dimensions(A, b, c)

        # ── 3. Construir vector sense ───────────────────
        m = len(b)
        eq_idxs = [int(i) for i in eq_str.split(',') if i.strip().isdigit()]
        ge_idxs = [int(i) for i in ge_str.split(',') if i.strip().isdigit()]
        
        minimize = bool(min_sw)  
        sense = ['≤'] * m
        for i in eq_idxs:
            if 0 <= i < m:
                sense[i] = '='
        for i in ge_idxs:
            if 0 <= i < m:
                sense[i] = '≥'
               
             
        track_iterations = bool(iter_sw)
        M_val = float(M_str)

        if track_iterations:
            sol, z, T_hist, piv_hist = granm_solver(
                c, A, b, sense,
                minimize=minimize, track_iterations=True, M=M_val
            )
            # Convertir valores numpy a tipos nativos de Python antes de serializar
            resultado = {
                'solution': [float(x) for x in sol],
                'optimal_value': float(z),
                'tableau_history': [t.tolist() for t in T_hist],
                'pivot_history': [[int(r), int(c)] for r, c in piv_hist],
                'success': True
            }
        else:
            sol, z = granm_solver(c, A, b, sense, minimize=minimize, M=M_val)
            resultado = {
                'solution': [float(x) for x in sol],
                'optimal_value': float(z),
                'success': True
            }

        # Aplicar conversión final de numpy a todos los datos del resultado
        resultado = convert_numpy_types(resultado)

        return render_template('granm.html',
                               resultado=resultado,
                               form_data=form_data)
                               
    except (GranMError, DimensionError, UnboundedError) as e:
        flash(f'Error en el método Gran M: {str(e)}', 'danger')
        return redirect(url_for('main.granm_page'))
    except Exception as e:
        flash(f'Error inesperado: {e}', 'error')
        logger.error(f"Error in resolver_granm: {e}", exc_info=True)
        return redirect(url_for('main.granm_page'))


@main_bp.route('/descargar/granm_json', methods=['POST'])
def descargar_granm_json():
    try:
        # Obtener datos del formulario enviados desde el botón de descarga
        resultado_json = request.form.get('resultado_json')
        
        if not resultado_json:
            flash('No hay resultado para descargar', 'error')
            return redirect(url_for('main.granm_page'))
        
        # Parsear los datos del resultado
        resultado = json.loads(resultado_json)
        
        # Recoger los datos del formulario directamente
        form_data = {
            'c': request.form.get('c', ''),
            'A': request.form.get('A', ''),
            'b': request.form.get('b', ''),
            'M': request.form.get('M', ''),
            'minimize': request.form.get('minimize') == 'on',
            'track_iterations': request.form.get('track_iterations') == 'on'
        }
        
        # Crear estructura completa para el JSON
        data_export = {
            'metodo': 'Gran M',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'datos_entrada': {
                'funcion_objetivo': form_data.get('c', ''),
                'matriz_restricciones': form_data.get('A', ''),
                'vector_recursos': form_data.get('b', ''),
                'valor_M': form_data.get('M', '1000'),
                'minimizar': form_data.get('minimize', False),
                'mostrar_iteraciones': form_data.get('track_iterations', False)
            },
            'resultado': resultado
        }
        
        # Crear respuesta de descarga
        response = make_response(json.dumps(data_export, indent=2, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=granm_resultado_{int(time.time())}.json'
        
        return response
    
    except Exception as e:
        flash(f'Error al descargar: {str(e)}', 'error')
        return redirect(url_for('main.granm_page'))


@main_bp.route('/resolver/dosfases', methods=['POST'])
def resolver_dosfases():
    try:
        # Obtener datos del formulario
        form_data = {
            'c': request.form.get('c', ''),
            'A': request.form.get('A', ''),
            'b': request.form.get('b', ''),
            'eq_constraints': request.form.get('eq_constraints', ''),
            'ge_constraints': request.form.get('ge_constraints', ''),
            'minimize': request.form.get('minimize') == 'on',
            'track_iterations': request.form.get('track_iterations') == 'on'
        }
        
        # Validar que los campos requeridos no estén vacíos
        if not form_data['c'].strip():
            flash('La función objetivo es requerida', 'error')
            return render_template('dosfases.html', form_data=form_data)
        
        if not form_data['A'].strip():
            flash('La matriz de restricciones es requerida', 'error')
            return render_template('dosfases.html', form_data=form_data)
            
        if not form_data['b'].strip():
            flash('El vector b es requerido', 'error')
            return render_template('dosfases.html', form_data=form_data)
        
        c = list(map(float, form_data['c'].split(',')))
        A_rows = form_data['A'].strip().split('\n')
        A = [list(map(float, row.split(','))) for row in A_rows]
        b = list(map(float, form_data['b'].split(',')))
        
        eq_constraints = None
        if form_data['eq_constraints'].strip():
            eq_constraints = [int(x) for x in form_data['eq_constraints'].split(',')]
        
        ge_constraints = None
        if form_data['ge_constraints'].strip():
            ge_constraints = [int(x) for x in form_data['ge_constraints'].split(',')]
        
        minimize = form_data['minimize']
        track_iterations = form_data['track_iterations']        # Resolver
        if track_iterations:
            solution, optimal_value, tableau_history, pivot_history = dosfases_solver(
                c, A, b, eq_constraints=eq_constraints, ge_constraints=ge_constraints, 
                minimize=minimize, track_iterations=True
            )
            
            # Verificar si la solución es válida
            if solution is None or optimal_value is None:
                flash('El problema no tiene solución factible', 'warning')
                return render_template('dosfases.html', form_data=form_data)
              # Convertir valores numpy a tipos nativos de Python antes de serializar
            resultado = {
                'solution': [float(x) for x in solution],
                'optimal_value': float(optimal_value),
                'tableau_history': [t.tolist() for t in tableau_history] if tableau_history else [],
                'pivot_history': [[int(r), int(c)] for r, c in pivot_history] if pivot_history else [],
                'success': True
            }
            
            # Detectar soluciones múltiples si hay tableau_history
            if tableau_history and len(tableau_history) > 0:
                final_tableau = tableau_history[-1]
                n_vars = len(c)
                
                # Usar el detector de soluciones múltiples
                multiple_solutions_result = detect_multiple_solutions(final_tableau, n_vars, c, minimize)
                formatted_result = format_multiple_solutions_result(multiple_solutions_result)
                
                # Convertir cualquier tipo numpy en los resultados de soluciones múltiples
                formatted_result = convert_numpy_types(formatted_result)
                
                # Agregar información de soluciones múltiples al resultado
                resultado.update(formatted_result)
        else:
            solution, optimal_value = dosfases_solver(c, A, b, eq_constraints=eq_constraints, ge_constraints=ge_constraints, minimize=minimize)
            
            # Verificar si la solución es válida
            if solution is None or optimal_value is None:
                flash('El problema no tiene solución factible', 'warning')
                return render_template('dosfases.html', form_data=form_data)
                
            resultado = {
                'solution': [float(x) for x in solution],
                'optimal_value': float(optimal_value),
                'success': True
            }

        # Aplicar conversión final de numpy a todos los datos del resultado
        resultado = convert_numpy_types(resultado)
        return render_template('dosfases.html', resultado=resultado, form_data=form_data)
        
    except (DosFasesError, DimensionError, UnboundedError, InfeasibleError) as e:
        flash(f'Error en el método Dos Fases: {str(e)}', 'danger')
        return redirect(url_for('main.dosfases_page'))
    except Exception as e:
        flash(f'Error inesperado: {str(e)}', 'error')
        return redirect(url_for('main.dosfases_page'))


@main_bp.route('/descargar/dosfases_json', methods=['POST'])
def descargar_dosfases_json():
    try:
        # Obtener datos del formulario enviados desde el botón de descarga
        resultado_json = request.form.get('resultado_json')
        
        if not resultado_json:
            flash('No hay resultado para descargar', 'error')
            return redirect(url_for('main.dosfases_page'))
        
        # Parsear los datos del resultado
        resultado = json.loads(resultado_json)
        
        # Recoger los datos del formulario directamente
        form_data = {
            'c': request.form.get('c', ''),
            'A': request.form.get('A', ''),
            'b': request.form.get('b', ''),
            'eq_constraints': request.form.get('eq_constraints', ''),
            'minimize': request.form.get('minimize') == 'on',
            'track_iterations': request.form.get('track_iterations') == 'on'
        }
        
        # Crear estructura completa para el JSON
        data_export = {
            'metodo': 'Dos Fases',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'datos_entrada': {
                'funcion_objetivo': form_data.get('c', ''),
                'matriz_restricciones': form_data.get('A', ''),
                'vector_recursos': form_data.get('b', ''),
                'restricciones_igualdad': form_data.get('eq_constraints', ''),
                'minimizar': form_data.get('minimize', False),
                'mostrar_iteraciones': form_data.get('track_iterations', False)
            },
            'resultado': resultado
        }
        
        # Crear respuesta de descarga
        response = make_response(json.dumps(data_export, indent=2, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=dosfases_resultado_{int(time.time())}.json'
        
        return response
    
    except Exception as e:
        flash(f'Error al descargar: {str(e)}', 'error')
        return redirect(url_for('main.dosfases_page'))
