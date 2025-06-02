from flask import Blueprint, request, jsonify, send_from_directory, current_app, render_template, flash, redirect, url_for
import json
import os
import time
import logging
import numpy as np
from .solvers import simplex, granm_solver, dosfases_solver
from .solvers import SimplexError, GranMError, DosFasesError, UnboundedError, DimensionError, InfeasibleError
from .solvers.multiple_solutions_detector import detect_multiple_solutions, format_multiple_solutions_result
from .manim_renderer import generate_manim_animation
import uuid

# Configure logger
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Main pages blueprint (no URL prefix)
main_bp = Blueprint('main', __name__)

# API blueprint with /api prefix
api_bp = Blueprint('api', __name__, url_prefix='/api')

# ===== RUTAS PARA LA INTERFAZ WEB =====

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

# Rutas para procesar los métodos
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
        
        c = list(map(float, form_data['c'].split(',')))
        A_rows = form_data['A'].strip().split('\n')
        A = [list(map(float, row.split(','))) for row in A_rows]
        b = list(map(float, form_data['b'].split(',')))
        minimize = form_data['minimize']
        track_iterations = form_data['track_iterations']
        
        # Validaciones básicas de dimensiones
        if len(A) != len(b):
            raise ValueError("El número de filas en A y en b no coincide")
        if any(len(row) != len(c) for row in A):
            raise ValueError("Cada fila de A debe tener la misma cantidad de columnas que c")
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
            
            # Integrar resultados al resultado principal
            resultado.update(formatted_result)
        else:
            solution, optimal_value = simplex(c, A, b, minimize=minimize)
            # Convertir valores numpy a tipos nativos de Python antes de serializar
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
        from flask import make_response
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

        form_data = {         # para mantener los valores en el formulario
            'c' : c_str, 'A' : A_str, 'b' : b_str,
            'eq_constraints': eq_str,
            'ge_constraints': ge_str,
            'minimize': bool(min_sw),
            'track_iterations': bool(iter_sw),
            'M': M_str
        }

        # ── 2. Parseo de listas numéricas ───────────────
        c = [float(x) for x in c_str.split(',') if x.strip()]
        A = [[float(num) for num in row.split(',') if num.strip()]
             for row in A_str.strip().split('\n') if row.strip()] # Corrected \n to 

        b = [float(x) for x in b_str.split(',') if x.strip()]

        # Validaciones básicas
        if len(A) != len(b):
            raise ValueError("El número de filas en A y en b no coincide")
        if any(len(row) != len(c) for row in A):
            raise ValueError("Cada fila de A debe tener la misma cantidad de columnas que c")

        # ── 3. Construir vector sense ───────────────────
        m = len(b)
        eq_idxs = [int(i) for i in eq_str.split(',') if i.strip().isdigit()]
        ge_idxs = [int(i) for i in ge_str.split(',') if i.strip().isdigit()]

        sense = ['≤'] * m
        for i in eq_idxs:
            if 0 <= i < m: # Check index bounds
                sense[i] = '='
        for i in ge_idxs:
            if 0 <= i < m: # Check index bounds
                sense[i] = '≥'        # ── 4. Llamar al solver ─────────────────────────
        minimize          = bool(min_sw)
        track_iterations  = bool(iter_sw)
        M_val             = float(M_str)

        if track_iterations:
            sol, z, T_hist, piv_hist = granm_solver(
                c, A, b, sense,
                minimize=minimize, track_iterations=True, M=M_val
            )
            # Convertir valores numpy a tipos nativos de Python antes de serializar
            resultado = {
                'solution': [float(x) for x in sol],
                'optimal_value': float(z),
                'tableau_history': [t.tolist() for t in T_hist], # Ensure inner elements are also converted
                'pivot_history': [[int(r), int(c)] for r, c in piv_hist],
                'success': True
            }            # ─ Detectar y generar soluciones múltiples óptimas (Gran M) ─
            final_tableau = T_hist[-1]
            n_vars = len(c)
            
            # Usar el nuevo detector mejorado
            multiple_solutions_result = detect_multiple_solutions(final_tableau, n_vars, c, minimize)
            formatted_result = format_multiple_solutions_result(multiple_solutions_result)
            # Convertir tipos numpy en los resultados de múltiples soluciones
            formatted_result = convert_numpy_types(formatted_result)            # Integrar resultados al resultado principal
            resultado.update(formatted_result)
        else:
            sol, z = granm_solver(
                c, A, b, sense,
                minimize=minimize, track_iterations=False, M=M_val
            )
            # Convertir valores numpy a tipos nativos de Python antes de serializar
            resultado = {
                'solution': [float(x) for x in sol],
                'optimal_value': float(z),
                'success': True
            }
            
            # ─ Detectar soluciones múltiples sin iteraciones ─
            # Ejecutar una vez más con iteraciones solo para obtener el tableau final
            try:
                _, _, T_hist_final, _ = granm_solver(
                    c, A, b, sense,
                    minimize=minimize, track_iterations=True, M=M_val
                )
                final_tableau = T_hist_final[-1]
                n_vars = len(c)
                
                # Usar el nuevo detector mejorado
                multiple_solutions_result = detect_multiple_solutions(final_tableau, n_vars, c, minimize)
                formatted_result = format_multiple_solutions_result(multiple_solutions_result)
                # Convertir tipos numpy en los resultados de múltiples soluciones
                formatted_result = convert_numpy_types(formatted_result)
                # Integrar resultados al resultado principal
                resultado.update(formatted_result)
            except Exception as e:
                # Si hay error en la detección, continuar sin las soluciones múltiples
                logger.warning(f"Error detectando soluciones múltiples en Gran M: {e}")
                resultado.update({
                    'has_multiple_solutions': False,
                    'variables_with_zero_cost': [],
                    'alternative_solutions': [],
                    'detection_method': 'error'
                })

        # Aplicar conversión final de numpy a todos los datos del resultado
        resultado = convert_numpy_types(resultado)

        return render_template('granm.html',
                               resultado=resultado,
                               form_data=form_data)# ── 5. Manejo de errores ────────────────────────────
    except (GranMError, DimensionError, UnboundedError) as e:
        flash(f'Error en el método Gran M: {str(e)}', 'danger')
        return redirect(url_for('main.granm_page'))
    except Exception as e:
        flash(f'Error inesperado: {e}', 'error')
        # Log the error for more details
        current_app.logger.error(f"Error in resolver_granm: {e}", exc_info=True)
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
        from flask import make_response
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
            'c': request.form['c'],
            'A': request.form['A'],
            'b': request.form['b'],
            'eq_constraints': request.form['eq_constraints'],
            'ge_constraints': request.form.get('ge_constraints', ''),
            'minimize': request.form.get('minimize') == 'on',
            'track_iterations': request.form.get('track_iterations') == 'on'
        }
        
        c = list(map(float, form_data['c'].split(',')))
        A_rows = form_data['A'].strip().split('\n')
        A = [list(map(float, row.split(','))) for row in A_rows]
        b = list(map(float, form_data['b'].split(',')))
        
        eq_constraints = None
        if form_data['eq_constraints'].strip():
            eq_constraints = list(map(int, form_data['eq_constraints'].split(',')))
        
        ge_constraints = None
        if form_data['ge_constraints'].strip():
            ge_constraints = list(map(int, form_data['ge_constraints'].split(',')))
        
        minimize = form_data['minimize']
        track_iterations = form_data['track_iterations']
        
        # Resolver
        if track_iterations:
            solution, optimal_value, tableau_history, pivot_history = dosfases_solver(
                c, A, b, eq_constraints=eq_constraints, ge_constraints=ge_constraints, 
                minimize=minimize, track_iterations=True
            )
            # Convertir valores numpy a tipos nativos de Python antes de serializar
            resultado = {
                'solution': convert_numpy_types(solution),
                'optimal_value': convert_numpy_types(optimal_value),
                'tableau_history': convert_numpy_types(tableau_history),
                'pivot_history': convert_numpy_types(pivot_history),
                'success': True
            }            # ─ Detectar y generar soluciones múltiples óptimas (Dos Fases) ─
            final_tableau = tableau_history[-1]
            n_vars = len(c)
              # Usar el nuevo detector mejorado
            multiple_solutions_result = detect_multiple_solutions(final_tableau, n_vars, c, minimize)
            formatted_result = format_multiple_solutions_result(multiple_solutions_result)
            # Convertir tipos numpy en los resultados de múltiples soluciones
            formatted_result = convert_numpy_types(formatted_result)
            # Integrar resultados al resultado principal
            resultado.update(formatted_result)
        else:
            solution, optimal_value = dosfases_solver(
                c, A, b, eq_constraints=eq_constraints, ge_constraints=ge_constraints, 
                minimize=minimize
            )
            # Convertir valores numpy a tipos nativos de Python antes de serializar
            resultado = {
                'solution': convert_numpy_types(solution),
                'optimal_value': convert_numpy_types(optimal_value),
                'success': True
            }
            
            # ─ Detectar soluciones múltiples sin iteraciones ─
            # Ejecutar una vez más con iteraciones solo para obtener el tableau final
            try:
                _, _, tableau_history_final, _ = dosfases_solver(
                    c, A, b, eq_constraints=eq_constraints, ge_constraints=ge_constraints, 
                    minimize=minimize, track_iterations=True
                )
                final_tableau = tableau_history_final[-1]
                n_vars = len(c)
                
                # Usar el nuevo detector mejorado
                multiple_solutions_result = detect_multiple_solutions(final_tableau, n_vars, c, minimize)
                formatted_result = format_multiple_solutions_result(multiple_solutions_result)
                # Convertir tipos numpy en los resultados de múltiples soluciones
                formatted_result = convert_numpy_types(formatted_result)
                # Integrar resultados al resultado principal
                resultado.update(formatted_result)
            except Exception as e:
                # Si hay error en la detección, continuar sin las soluciones múltiples
                logger.warning(f"Error detectando soluciones múltiples en Dos Fases: {e}")
                resultado.update({
                    'has_multiple_solutions': False,
                    'variables_with_zero_cost': [],
                    'alternative_solutions': [],
                    'detection_method': 'error'
                })

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
        from flask import make_response
        response = make_response(json.dumps(data_export, indent=2, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=dosfases_resultado_{int(time.time())}.json'
        
        return response
    
    except Exception as e:
        flash(f'Error al descargar: {str(e)}', 'error')
        return redirect(url_for('main.dosfases_page'))

# ===== RUTAS API EXISTENTES =====

CASOS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'manim_anim', 'casos.json')

# Ensure the casos.json file exists
def ensure_casos_file():
    os.makedirs(os.path.dirname(CASOS_PATH), exist_ok=True)
    if not os.path.exists(CASOS_PATH):
        with open(CASOS_PATH, 'w') as f:
            json.dump([], f)

# Load examples from the casos.json file
def load_casos():
    ensure_casos_file()
    try:
        with open(CASOS_PATH, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If file is corrupted, return empty list
        return []

# Save examples to the casos.json file
def save_casos(casos):
    ensure_casos_file()
    with open(CASOS_PATH, 'w') as f:
        json.dump(casos, f, indent=4)

# Home route is now handled by the first index function

# Favicon route
@main_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# ===== RUTAS PARA ANIMACIONES MANIM =====

@main_bp.route('/generar-animacion/simplex', methods=['POST'])
def generar_animacion_simplex():
    start_time = time.time()
    logger.info("Ruta generar_animacion_simplex iniciada")
    try:
        # Obtener datos del formulario
        c = list(map(float, request.form['c'].split(',')))
        A_rows = request.form['A'].strip().split('\n')
        A = [list(map(float, row.split(','))) for row in A_rows]
        b = list(map(float, request.form['b'].split(',')))
        minimize = request.form.get('minimize') == 'on'
        track_iterations = request.form.get('track_iterations') == 'on'        
        
        logger.info(f"Datos recibidos: c={c}, A={A}, b={b}, minimize={minimize}, track_iterations={track_iterations}")
        
        # Resolver el problema para obtener la solución
        try:
            if track_iterations:
                solution, z_opt, tableau_history, pivot_history = simplex(c, A, b, minimize=minimize, track_iterations=True)
                result = {
                    'solution': solution.tolist() if hasattr(solution, 'tolist') else solution,
                    'z_opt': float(z_opt),
                    'tableau_history': [t.tolist() if hasattr(t, 'tolist') else t for t in tableau_history],
                    'pivot_history': pivot_history
                }
            else:
                solution, z_opt = simplex(c, A, b, minimize=minimize, track_iterations=False)
                result = {
                    'solution': solution.tolist() if hasattr(solution, 'tolist') else solution,
                    'z_opt': float(z_opt),
                    'tableau_history': [],
                    'pivot_history': []
                }
            logger.info(f"Problema resuelto exitosamente: {result}")
        except Exception as e:
            logger.error(f"Error al resolver el problema: {e}")
            flash(f'Error al resolver el problema: {str(e)}', 'danger')
            return redirect(url_for('main.simplex_page'))
        
        # Generar la animación
        tableau_history = result.get('tableau_history', []) if track_iterations else []
        pivot_history = result.get('pivot_history', []) if track_iterations else []
        
        # Prepare animation data
        animation_data = {
            'c': c,
            'A': A, 
            'b': b,
            'solution': result['solution'],            'z_opt': result['z_opt'],
            'minimize': minimize,
            'method': "simplex",
            'tableau_history': tableau_history,
            'pivot_history': pivot_history
        }        
        logger.info("Iniciando generación de animación Manim")
        media_path = generate_manim_animation(**animation_data)
        logger.info(f"Media path generado: {media_path}")
        
        if media_path and os.path.exists(media_path):
            logger.info(f"Archivo encontrado en: {media_path}")
            # Guardar la ruta del archivo de media en la sesión o como archivo temporal
            media_id = str(uuid.uuid4())
            media_dir = os.path.join(current_app.root_path, 'static', 'media')
            os.makedirs(media_dir, exist_ok=True)
            
            # Determinar el tipo de archivo y la extensión
            import shutil
            file_extension = os.path.splitext(media_path)[1].lower()
            is_video = file_extension in ['.mp4', '.avi', '.mov', '.mkv']
            logger.info(f"Tipo de archivo: {file_extension}, es video: {is_video}")
            
            # Copiar el archivo a la carpeta static
            static_media_path = os.path.join(media_dir, f'{media_id}{file_extension}')
            shutil.copy2(media_path, static_media_path)
            logger.info(f"Archivo copiado a: {static_media_path}")
            media_url = f'/static/media/{media_id}{file_extension}'
            logger.info(f"URL de media: {media_url}")
            
            if is_video:
                flash('¡Animación de video generada exitosamente!', 'success')
                logger.info("Renderizando template con video")
                elapsed_time = time.time() - start_time
                logger.info(f"Proceso completado en {elapsed_time:.2f} segundos")
                return render_template('simplex.html', 
                                     solution=result, 
                                     video_url=media_url)
            else:
                flash('¡Visualización generada exitosamente!', 'success')
                logger.info("Renderizando template con imagen")
                elapsed_time = time.time() - start_time
                logger.info(f"Proceso completado en {elapsed_time:.2f} segundos")
                return render_template('simplex.html', 
                                     solution=result, 
                                     image_url=media_url)
        else:
            logger.warning(f"Archivo no encontrado o path vacío: {media_path}")
            flash('Error al generar la animación. Mostrando solo resultados.', 'warning')
            elapsed_time = time.time() - start_time
            logger.info(f"Proceso (con advertencia) completado en {elapsed_time:.2f} segundos")
            return render_template('simplex.html', solution=result)
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error generating Simplex animation after {elapsed_time:.2f} segundos: {e}")
        flash(f'Error al generar la animación: {str(e)}', 'danger')
        return redirect(url_for('main.simplex_page'))

@main_bp.route('/generar-animacion/granm', methods=['POST'])
def generar_animacion_granm():
    try:
        # Obtener datos del formulario
        c = list(map(float, request.form['c'].split(',')))
        A_rows = request.form['A'].strip().split('\n')
        A = [list(map(float, row.split(','))) for row in A_rows]
        b = list(map(float, request.form['b'].split(',')))
        minimize = request.form.get('minimize') == 'on'
        
        eq_constraints_str = request.form.get('eq_constraints', '').strip()
        eq_constraints = []
        if eq_constraints_str:
            eq_constraints = list(map(int, eq_constraints_str.split(',')))
        
        # Resolver el problema
        result = granm_solver(c, A, b, eq_constraints=eq_constraints, minimize=minimize)
        
        if 'error' in result:
            flash(f'Error al resolver el problema: {result["error"]}', 'danger')
            return redirect(url_for('main.granm_page'))
        
        # Generar la animación
        video_path = generate_manim_animation(
            c=c, A=A, b=b,
            solution=result['solution'],
            z_opt=result['z_opt'],
            minimize=minimize,
            method="granm"
        )
        
        if video_path and os.path.exists(video_path):
            video_id = str(uuid.uuid4())
            video_dir = os.path.join(current_app.root_path, 'static', 'videos')
            os.makedirs(video_dir, exist_ok=True)
            
            import shutil
            static_video_path = os.path.join(video_dir, f'{video_id}.mp4')
            shutil.copy2(video_path, static_video_path)
            
            flash('¡Animación generada exitosamente!', 'success')
            return render_template('granm.html', 
                                 solution=result, 
                                 video_url=f'/static/videos/{video_id}.mp4')
        else:
            flash('Error al generar la animación. Mostrando solo resultados.', 'warning')
            return render_template('granm.html', solution=result)
            
    except Exception as e:
        logger.error(f"Error generating Gran M animation: {e}")
        flash(f'Error al generar la animación: {str(e)}', 'danger')
        return redirect(url_for('main.granm_page'))

@main_bp.route('/generar-animacion/dosfases', methods=['POST'])
def generar_animacion_dosfases():
    try:
        # Obtener datos del formulario y mantenerlos
        form_data = {
            'c': request.form['c'],
            'A': request.form['A'],
            'b': request.form['b'],
            'eq_constraints': request.form.get('eq_constraints', ''),
            'minimize': request.form.get('minimize') == 'on',
            'track_iterations': request.form.get('track_iterations') == 'on'
        }
        
        c = list(map(float, form_data['c'].split(',')))
        A_rows = form_data['A'].strip().split('\n')
        A = [list(map(float, row.split(','))) for row in A_rows]
        b = list(map(float, form_data['b'].split(',')))
        minimize = form_data['minimize']
        
        eq_constraints = []
        if form_data['eq_constraints'].strip():
            eq_constraints = list(map(int, form_data['eq_constraints'].split(',')))
          # Resolver el problema
        result = dosfases_solver(c, A, b, eq_constraints=eq_constraints, ge_constraints=[], minimize=minimize)
        
        if 'error' in result:
            flash(f'Error al resolver el problema: {result["error"]}', 'danger')
            return redirect(url_for('main.dosfases_page'))
        
        # Generar la animación
        video_path = generate_manim_animation(
            c=c, A=A, b=b,
            solution=result['solution'],
            z_opt=result['z_opt'],
            minimize=minimize,
            method="dosfases"
        )
        
        if video_path and os.path.exists(video_path):
            video_id = str(uuid.uuid4())
            video_dir = os.path.join(current_app.root_path, 'static', 'videos')
            os.makedirs(video_dir, exist_ok=True)
            
            import shutil
            static_video_path = os.path.join(video_dir, f'{video_id}.mp4')
            shutil.copy2(video_path, static_video_path)
            
            flash('¡Animación generada exitosamente!', 'success')
            return render_template('dosfases.html', 
                                 solution=result, 
                                 video_url=f'/static/videos/{video_id}.mp4',
                                 form_data=form_data)
        else:
            flash('Error al generar la animación. Mostrando solo resultados.', 'warning')
            return render_template('dosfases.html', solution=result, form_data=form_data)
            
    except Exception as e:
        logger.error(f"Error generating Dos Fases animation: {e}")
        flash(f'Error al generar la animación: {str(e)}', 'danger')
        return redirect(url_for('main.dosfases_page'))

# ===== RUTAS API EXISTENTES =====

CASOS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'manim_anim', 'casos.json')

# Get all optimization examples
@api_bp.route('/casos', methods=['GET'])
def get_casos():
    casos = load_casos()
    return jsonify(casos)

# Get a specific example by index
@api_bp.route('/casos/<int:caso_id>', methods=['GET'])
def get_caso(caso_id):
    casos = load_casos()
    if 0 <= caso_id < len(casos):
        return jsonify(casos[caso_id])
    return jsonify({"error": "Caso no encontrado"}), 404

# Add a new example
@api_bp.route('/casos', methods=['POST'])
def add_caso():
    try:
        caso = request.json
        casos = load_casos()
        casos.append(caso)
        save_casos(casos)
        return jsonify({"message": "Caso agregado correctamente", "index": len(casos) - 1})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Delete an example
@api_bp.route('/casos/<int:caso_id>', methods=['DELETE'])
def delete_caso(caso_id):
    casos = load_casos()
    if 0 <= caso_id < len(casos):
        removed = casos.pop(caso_id)
        save_casos(casos)
        return jsonify({"message": "Caso eliminado correctamente", "removed": removed})
    return jsonify({"error": "Caso no encontrado"}), 404

# Solve using Simplex method
@api_bp.route('/resolver/simplex', methods=['POST'])
def resolver_simplex():
    try:
        data = request.json
        c  = data.get('c', [])
        A  = data.get('A', [[]])
        b  = data.get('b', [])
        minimize         = data.get('minimize', False)
        track_iterations = data.get('track_iterations', False)

        # ── Validar entradas ──────────────────────────────
        if not c or not A or not b:
            return jsonify({"error": "Datos incompletos. Se requieren c, A y b."}), 400        # ── Resolver con iteraciones (para mostrar tabla) ─
        if track_iterations:
            solution, z_opt, tableau_hist, pivot_hist = simplex(
                c, A, b, minimize=minimize, track_iterations=True
            )
            result = {
                "solution"       : _to_list(solution),
                "optimal_value"  : float(z_opt),
                "tableau_history": [_to_list(t) for t in tableau_hist],
                "pivot_history"  : pivot_hist
            }

            # Detectar soluciones múltiples
            try:
                final_tableau = tableau_hist[-1]
                multi_info = detect_multiple_solutions(
                    final_tableau,
                    n_orig_vars=len(c),   # 2º arg
                    c=c,                  # 3º arg   ← ¡faltaba!
                    minimize=minimize     # opcional
                    )

                # Convertir tipos numpy en la información de soluciones múltiples
                multi_info = convert_numpy_types(multi_info)

                result["multiple_solutions"]   = format_multiple_solutions_result(multi_info)
                result["has_multiple_solutions"] = multi_info["has_multiple_solutions"]
                result["multiple_solution_vars"] = multi_info.get("variables_with_zero_cost", [])
                if multi_info.get("alternative_solutions"):
                    result["alternative_solutions"] = multi_info["alternative_solutions"]

            except Exception as e:
                logger.warning(f"Error detectando soluciones múltiples: {e}")
                result["multiple_solutions"] = {"has_multiple_solutions": False, "error": str(e)}

        # ── Resolver sin iteraciones ─────────────────────
        else:
            solution, z_opt = simplex(
                c, A, b, minimize=minimize, track_iterations=False
            )
            result = {
                "solution"      : _to_list(solution),
                "optimal_value" : float(z_opt)
            }

        # Aplicar conversión final de numpy a todos los datos del resultado
        result = convert_numpy_types(result)
        return jsonify(result)

    except (SimplexError, DimensionError, UnboundedError) as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        logger.exception("Error in Simplex solver")
        return jsonify({"error": f"Error inesperado: {e}"}), 500


# ────────────────── util ──────────────────
def _to_list(x):
    """Convierte numpy arrays u objetos normales a list."""
    return x.tolist() if hasattr(x, "tolist") else x


# Solve using Gran M method
@api_bp.route('/resolver/granm', methods=['POST'])
def resolver_granm():
    try:
        data = request.json
        c = data.get('c', [])
        A = data.get('A', [[]])
        b = data.get('b', [])
        eq_constraints = data.get('eq_constraints', [])
        minimize = data.get('minimize', False)
        track_iterations = data.get('track_iterations', False)

        # Validate inputs
        if not c or not A or not b:
            return jsonify({"error": "Datos incompletos. Se requieren c, A y b."}), 400

        # Resolver con iteraciones
        if track_iterations:
            solution, z_opt, tableau_history, pivot_history = granm_solver(
                c, A, b, eq_constraints, minimize, track_iterations=True
            )
            result = {
                "solution": solution.tolist() if hasattr(solution, "tolist") else solution,
                "optimal_value": float(z_opt),
                "tableau_history": [t.tolist() for t in tableau_history] if hasattr(tableau_history[0], "tolist") else tableau_history,
                "pivot_history": pivot_history
            }            # ─ Detectar múltiples soluciones usando el detector mejorado ─
            try:
                final_tableau = tableau_history[-1]
                multiple_solutions_result = detect_multiple_solutions(
                    final_tableau, len(c), c, minimize=minimize
                )

                # Formatear resultado y convertir tipos numpy
                formatted_multiple_result = format_multiple_solutions_result(multiple_solutions_result)
                formatted_multiple_result = convert_numpy_types(formatted_multiple_result)
                
                result['multiple_solutions'] = formatted_multiple_result
                result['has_multiple_solutions'] = formatted_multiple_result['has_multiple_solutions']
                result['multiple_solution_vars'] = formatted_multiple_result.get('variables_with_zero_cost', [])

                if formatted_multiple_result.get('alternative_solutions'):                result['alternative_solutions'] = formatted_multiple_result['alternative_solutions']

            except Exception as e:
                logger.warning(f"Error en detección de múltiples soluciones: {e}")
                result['multiple_solutions'] = {'has_multiple_solutions': False, 'error': str(e)}
            
            # Convertir todos los tipos numpy en el resultado final
            result = convert_numpy_types(result)        # Resolver sin iteraciones
        else:
            solution, z_opt = granm_solver(
                c, A, b, eq_constraints, minimize, track_iterations=False
            )
            result = {
                "solution": solution.tolist() if hasattr(solution, "tolist") else solution,
                "optimal_value": float(z_opt)
            }
            # Convertir todos los tipos numpy en el resultado final
            result = convert_numpy_types(result)

        return jsonify(result)

    except (GranMError, DimensionError, UnboundedError) as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        logger.exception("Error in Gran M solver")
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

# Helper function to convert NumPy types to native Python types
def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Handle numpy scalars (including specific types like int64)
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    # Handle Python built-in types with nested numpy
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    # Check if it's any numpy type we missed
    elif hasattr(obj, 'dtype') and 'numpy' in str(type(obj)):
        if obj.ndim == 0:  # scalar
            return obj.item()
        else:
            return obj.tolist()
    # Handle any remaining numpy types by checking the type name
    elif 'numpy' in str(type(obj)) or 'int64' in str(type(obj)):
        try:
            if hasattr(obj, 'item'):
                return obj.item()
            elif hasattr(obj, 'tolist'):
                return obj.tolist()
            else:
                return int(obj) if 'int' in str(type(obj)) else float(obj)
        except (ValueError, TypeError):
            return str(obj)
    return obj

# Solve using Two-Phase method
@api_bp.route('/resolver/dosfases', methods=['POST'])
def resolver_dosfases():
    try:
        data = request.json
        c = data.get('c', [])
        A = data.get('A', [[]])
        b = data.get('b', [])
        eq_constraints = data.get('eq_constraints', [])
        ge_constraints = data.get('ge_constraints', [])
        minimize = data.get('minimize', False)
        track_iterations = data.get('track_iterations', False)
        
        # Validate inputs
        if not c or not A or not b:
            return jsonify({"error": "Datos incompletos. Se requieren c, A y b."}), 400
        
        # Solve with Two-Phase method
        if track_iterations:
            solution, z_opt, tableau_history, pivot_history = dosfases_solver(
                c, A, b, eq_constraints=eq_constraints, ge_constraints=ge_constraints, 
                minimize=minimize, track_iterations=True
            )
            result = {
                "solution": convert_numpy_types(solution),
                "optimal_value": convert_numpy_types(z_opt),
                "tableau_history": convert_numpy_types(tableau_history),
                "pivot_history": convert_numpy_types(pivot_history)            }
            
            # ─ Detectar múltiples soluciones usando el detector mejorado ─
            try:
                final_tableau = tableau_history[-1]
                multiple_solutions_result = detect_multiple_solutions(
                    final_tableau, len(c), c, minimize=minimize
                )

                # Formatear resultado y convertir tipos numpy
                formatted_multiple_result = format_multiple_solutions_result(multiple_solutions_result)
                formatted_multiple_result = convert_numpy_types(formatted_multiple_result)
                
                result['multiple_solutions'] = formatted_multiple_result
                result['has_multiple_solutions'] = formatted_multiple_result['has_multiple_solutions']
                result['multiple_solution_vars'] = formatted_multiple_result.get('variables_with_zero_cost', [])

                if formatted_multiple_result.get('alternative_solutions'):
                    result['alternative_solutions'] = formatted_multiple_result['alternative_solutions']

            except Exception as e:
                logger.warning(f"Error en detección de múltiples soluciones (Dos Fases): {e}")
                result['multiple_solutions'] = {'has_multiple_solutions': False, 'error': str(e)}
              # Convertir todos los tipos numpy en el resultado final
            result = convert_numpy_types(result)
        else:
            solution, z_opt = dosfases_solver(
                c, A, b, eq_constraints=eq_constraints, ge_constraints=ge_constraints, 
                minimize=minimize, track_iterations=False
            )
            result = {
                "solution": convert_numpy_types(solution),
                "optimal_value": convert_numpy_types(z_opt)
            }
            
            # ─ Detectar múltiples soluciones sin iteraciones ─
            # Ejecutar una vez más con iteraciones solo para obtener el tableau final
            try:
                _, _, tableau_history_final, _ = dosfases_solver(
                    c, A, b, eq_constraints=eq_constraints, ge_constraints=ge_constraints, 
                    minimize=minimize, track_iterations=True
                )
                final_tableau = tableau_history_final[-1]
                
                multiple_solutions_result = detect_multiple_solutions(
                    final_tableau, len(c), c, minimize=minimize
                )

                # Formatear resultado y convertir tipos numpy
                formatted_multiple_result = format_multiple_solutions_result(multiple_solutions_result)
                formatted_multiple_result = convert_numpy_types(formatted_multiple_result)
                
                result['multiple_solutions'] = formatted_multiple_result
                result['has_multiple_solutions'] = formatted_multiple_result['has_multiple_solutions']
                result['multiple_solution_vars'] = formatted_multiple_result.get('variables_with_zero_cost', [])

                if formatted_multiple_result.get('alternative_solutions'):
                    result['alternative_solutions'] = formatted_multiple_result['alternative_solutions']

            except Exception as e:
                logger.warning(f"Error detectando soluciones múltiples en Dos Fases (sin iteraciones): {e}")
                result['multiple_solutions'] = {'has_multiple_solutions': False, 'error': str(e)}
            
            # Convertir todos los tipos numpy en el resultado final
            result = convert_numpy_types(result)
        
        return jsonify(result)
    except (DosFasesError, DimensionError, UnboundedError, InfeasibleError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception("Error in Two-Phase solver")
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

# Generate animation
@api_bp.route('/animar', methods=['POST'])
def animar():
    try:
        data = request.json
        c = data.get('c', [])
        A = data.get('A', [[]])
        b = data.get('b', [])
        solution = data.get('solution', [])
        z_opt = data.get('optimal_value')
        minimize = data.get('minimize', False)
        method = data.get('method', 'simplex')  # Default to simplex
        
        # Generate unique ID for this animation
        animation_id = str(uuid.uuid4())
        
        # Generate animation
        video_path = generate_manim_animation(c, A, b, solution, z_opt, minimize, method)
        
        if video_path:
            # Get filename from path
            video_filename = os.path.basename(video_path)
            result = {
                "success": True,
                "animation_id": animation_id,
                "video_path": video_filename,
                "url": f"/api/videos/{video_filename}"
            }
            return jsonify(result)
        else:
            return jsonify({"error": "No se pudo generar la animación"}), 500
    except Exception as e:
        logger.exception("Error generating animation")
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

# Serve video files
@api_bp.route('/videos/<filename>')
def serve_video(filename):
    video_folder = current_app.config['VIDEO_FOLDER']
    return send_from_directory(video_folder, filename)

# Upload a JSON file with examples
@api_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No se seleccionó ningún archivo"}), 400
    
    if file and file.filename.endswith('.json'):
        try:
            # Read JSON content
            file_content = file.read().decode('utf-8')
            json_data = json.loads(file_content)
            
            # Save to casos.json
            save_casos(json_data)
            
            return jsonify({"message": "Archivo cargado y procesado correctamente", "casos": json_data})
        except json.JSONDecodeError:
            return jsonify({"error": "El archivo no contiene JSON válido"}), 400
        except Exception as e:
            return jsonify({"error": f"Error al procesar el archivo: {str(e)}"}), 500
    
    return jsonify({"error": "Tipo de archivo no permitido"}), 400

# For backward compatibility, create a bp variable
bp = main_bp

import numpy as np

def generate_alternative_solutions(final_tableau, n_vars, tol=1e-8):
    """
    Recorre cada variable NO básica con costo reducido 0,
    pivotea (Bland: razón mínima) y devuelve las soluciones alternativas.

    Returns
    -------
    list[dict]  cada dict = {
        'solution'    : list[float],
        'entering_var': int,        # índice de la variable que entra
        'pivot_row'   : int         # fila (0-based, sin contar Z)
    }
    """
    alternatives = []
    z_row  = final_tableau[0, :-1]
    m_rows = final_tableau.shape[0] - 1     # sin la fila Z

    for j in range(n_vars):
        col = final_tableau[1:, j]

        # (a) var NO básica  → columna no unitaria
        is_basic = (np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0, atol=tol))
        # (b) costo reducido ≈ 0
        zero_cost = np.isclose(z_row[j], 0.0, atol=tol)

        if is_basic or not zero_cost:
            continue  # no candidata

        # filas con coeficiente positivo
        positive = np.where(col > tol)[0]
        if positive.size == 0:
            # no se puede pivotar sin violar factibilidad
            continue

        # razón mínima (Bland)
        rhs      = final_tableau[1:, -1][positive]
        ratios   = rhs / col[positive]
        p_row    = positive[np.argmin(ratios)] + 1   # +1 para incluir fila Z

        # --- pivotar en una copia ---
        T = final_tableau.copy()
        T[p_row] /= T[p_row, j]               # normaliza
        for r in range(T.shape[0]):
            if r != p_row:
                T[r] -= T[r, j] * T[p_row]

        # --- extraer solución de la copia ---
        alt_sol = np.zeros(n_vars)
        for k in range(n_vars):
            col_k = T[1:, k]
            if np.count_nonzero(col_k) == 1 and np.isclose(col_k.max(), 1.0, atol=tol):
                basic_row = np.where(np.isclose(col_k, 1.0, atol=tol))[0][0] + 1
                alt_sol[k] = T[basic_row, -1]

        alternatives.append({
            'solution'    : alt_sol.tolist(),
            'entering_var': j,
            'pivot_row'   : p_row - 1   # 0-based sin fila Z
        })

    return alternatives


def detect_multiple_solutions(final_tableau, n_orig_vars, c, minimize=False):
    """
    Detecta soluciones múltiples óptimas con método mejorado.
    
    Métodos de detección:
    1. Variables no básicas con costo reducido cero (método clásico)
    2. Análisis de degeneración y variables básicas con costo cero
    3. Verificación geométrica cuando todas las variables son básicas
    """
    info = {
        'has_multiple_solutions': False,
        'variables_with_zero_cost': [],
        'alternative_solutions': [],
        'detection_method': 'none'
    }

    z_row = final_tableau[0, :-1]
    tol = 1e-8
    
    # Método 1: Variables no básicas con costo reducido 0 (método clásico)
    for j in range(n_orig_vars):
        col = final_tableau[1:, j]
        is_basic = (np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0, atol=tol))
        zero_cost = np.isclose(z_row[j], 0.0, atol=tol)
        
        if not is_basic and zero_cost:
            info['variables_with_zero_cost'].append(j)
    
    if info['variables_with_zero_cost']:
        info['has_multiple_solutions'] = True
        info['detection_method'] = 'nonbasic_zero_cost'
        info['alternative_solutions'] = generate_alternative_solutions(
            final_tableau, n_orig_vars
        )
        return info
      # Método 2: Verificar si todas las variables originales son básicas con costo 0
    # Esto puede indicar que estamos en un vértice donde múltiples aristas son óptimas
    all_basic_zero_cost = True
    basic_vars_count = 0
    
    for j in range(n_orig_vars):
        col = final_tableau[1:, j]
        is_basic = (np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0, atol=tol))
        zero_cost = np.isclose(z_row[j], 0.0, atol=tol)
        
        if is_basic:
            basic_vars_count += 1
            if not zero_cost:
                all_basic_zero_cost = False
        # Note: we don't set all_basic_zero_cost to False for non-basic variables
        # because we only care about whether basic variables have zero cost
    
    # Si todas las variables básicas tienen costo 0, verificar variables de holgura
    if all_basic_zero_cost and basic_vars_count > 0:
        # Buscar variables de holgura no básicas con costo cero
        slack_candidates = []
        for j in range(n_orig_vars, len(z_row)):
            if j < final_tableau.shape[1] - 1:  # No incluir la columna RHS
                col = final_tableau[1:, j]
                is_basic = (np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0, atol=tol))
                zero_cost = np.isclose(z_row[j], 0.0, atol=tol)
                
                if not is_basic and zero_cost:
                    slack_candidates.append(j)
        
        if slack_candidates:
            info['has_multiple_solutions'] = True
            info['detection_method'] = 'slack_zero_cost'
            info['variables_with_zero_cost'] = slack_candidates
            # Para variables de holgura, usamos un generador alternativo
            info['alternative_solutions'] = generate_alternative_solutions_from_slack(
                final_tableau, n_orig_vars, slack_candidates
            )
            return info
    
    # Método 3: Verificación especial para casos donde todas las variables originales son básicas
    # pero los coeficientes de la función objetivo son iguales (indicador fuerte de soluciones múltiples)
    if basic_vars_count >= 2:
        # Verificar si los coeficientes originales son iguales o proporcionales
        c_array = np.array(c)
        if len(set(np.abs(c_array))) == 1 and c_array[0] != 0:  # Todos los coeficientes son iguales            # En este caso, es muy probable que haya soluciones múltiples
            # Intentar generar alternativas intercambiando variables básicas
            info['has_multiple_solutions'] = True
            info['detection_method'] = 'equal_coefficients'
            info['variables_with_zero_cost'] = list(range(n_orig_vars))
            info['alternative_solutions'] = generate_solutions_from_equal_coefficients(
                final_tableau, n_orig_vars, c
            )

    return info


def format_multiple_solutions_result(info):
    """
    Simple pass-through (aquí podrías dar formato distinto si tu UI lo requiere)
    """
    return info

def generate_alternative_solutions_from_slack(final_tableau, n_orig_vars, slack_candidates, tol=1e-8):
    """
    Genera soluciones alternativas cuando variables de holgura no básicas tienen costo reducido cero.
    """
    alternatives = []
    
    for slack_var in slack_candidates:
        # Verificar si podemos hacer básica esta variable de holgura
        col = final_tableau[1:, slack_var]
        rhs = final_tableau[1:, -1]
        
        # Buscar filas donde el coeficiente de la variable de holgura es positivo
        positive_indices = np.where(col > tol)[0]
        
        if len(positive_indices) == 0:
            continue
            
        # Calcular ratios para determinar la fila pivote
        ratios = []
        valid_rows = []
        
        for i in positive_indices:
            if rhs[i] >= 0:  # Solo considerar RHS no negativos
                ratio = rhs[i] / col[i]
                ratios.append(ratio)
                valid_rows.append(i)
        
        if not ratios:
            continue
            
        # Seleccionar la fila con menor ratio
        min_ratio_idx = np.argmin(ratios)
        pivot_row = valid_rows[min_ratio_idx] + 1  # +1 para incluir fila Z
        
        # Crear tableau alternativo pivoteando
        T = final_tableau.copy()
        T[pivot_row] /= T[pivot_row, slack_var]
        
        for r in range(T.shape[0]):
            if r != pivot_row:
                T[r] -= T[r, slack_var] * T[pivot_row]
        
        # Extraer solución alternativa
        alt_sol = np.zeros(n_orig_vars)
        for k in range(n_orig_vars):
            col_k = T[1:, k]
            if np.count_nonzero(col_k) == 1 and np.isclose(col_k.max(), 1.0, atol=tol):
                basic_row = np.where(np.isclose(col_k, 1.0, atol=tol))[0][0] + 1
                alt_sol[k] = T[basic_row, -1]

        # Verificar que es una solución diferente y factible
        current_sol = np.zeros(n_orig_vars)
        for k in range(n_orig_vars):
            col_k = final_tableau[1:, k]
            if np.count_nonzero(col_k) == 1 and np.isclose(col_k.max(), 1.0, atol=tol):
                basic_row = np.where(np.isclose(col_k, 1.0, atol=tol))[0][0] + 1
                current_sol[k] = final_tableau[basic_row, -1]
        
        if not np.allclose(alt_sol, current_sol, atol=tol) and np.all(alt_sol >= -tol):
            alternatives.append({
                'solution': alt_sol.tolist(),
                'entering_var': slack_var,
                'pivot_row': pivot_row - 1,
                'method': 'slack_variable'
            })
    
    return alternatives


def generate_solutions_from_equal_coefficients(final_tableau, n_orig_vars, c, tol=1e-8):
    """
    Genera soluciones alternativas cuando los coeficientes de la función objetivo son iguales,
    lo que geométricamente indica que múltiples vértices son óptimos.
    """
    alternatives = []
    
    # Obtener la solución actual
    current_sol = np.zeros(n_orig_vars)
    basic_vars = []
    
    for k in range(n_orig_vars):
        col_k = final_tableau[1:, k]
        if np.count_nonzero(col_k) == 1 and np.isclose(col_k.max(), 1.0, atol=tol):
            basic_row = np.where(np.isclose(col_k, 1.0, atol=tol))[0][0] + 1
            current_sol[k] = final_tableau[basic_row, -1]
            basic_vars.append(k)
    
    # Cuando los coeficientes son iguales, cualquier combinación convexa de vértices
    # con el mismo valor objetivo es óptima
    if len(basic_vars) >= 2:
        # Generar algunas soluciones convexas alternativas
        for i in range(len(basic_vars)):
            for j in range(i + 1, len(basic_vars)):
                var1, var2 = basic_vars[i], basic_vars[j]
                
                # Crear solución donde intercambiamos valores entre dos variables básicas
                alt_sol = current_sol.copy()
                
                # Intercambio simple: dar todo el valor de var1 a var2
                if current_sol[var1] > tol:
                    transfer = min(current_sol[var1], 1.0)  # Limitar transferencia
                    alt_sol[var1] = max(0, current_sol[var1] - transfer)
                    alt_sol[var2] = current_sol[var2] + transfer                    
                    if np.all(alt_sol >= -tol):  # Verificar factibilidad
                        alternatives.append({
                            'solution': alt_sol.tolist(),
                            'entering_var': var2,  # Variable que se incrementa
                            'pivot_row': -1,  # No hay fila pivote específica en este método
                            'method': 'equal_coefficients',
                            'transfer_from': var1,
                            'transfer_to': var2,
                            'transfer_amount': transfer
                        })
                
                # También intentar el intercambio inverso
                if current_sol[var2] > tol:
                    alt_sol2 = current_sol.copy()
                    transfer = min(current_sol[var2], 1.0)
                    alt_sol2[var2] = max(0, current_sol[var2] - transfer)
                    alt_sol2[var1] = current_sol[var1] + transfer
                    
                    if np.all(alt_sol2 >= -tol):                        alternatives.append({
                            'solution': alt_sol2.tolist(),
                            'entering_var': var1,  # Variable que se incrementa
                            'pivot_row': -1,  # No hay fila pivote específica en este método
                            'method': 'equal_coefficients',
                            'transfer_from': var2,
                            'transfer_to': var1,
                            'transfer_amount': transfer
                        })
    
    # También generar combinaciones convexas más sofisticadas
    if len(basic_vars) >= 2:
        # Generar algunas combinaciones convexas con diferentes pesos
        weights = [0.25, 0.5, 0.75]
        for w in weights:
            alt_sol = current_sol.copy()
            # Redistribuir valores entre variables básicas
            total_value = sum(current_sol[var] for var in basic_vars)
            if total_value > tol:
                # Redistribuir proporcionalmente
                for idx, var in enumerate(basic_vars):
                    new_proportion = w if idx == 0 else (1 - w) / (len(basic_vars) - 1)
                    alt_sol[var] = total_value * new_proportion
                
                if np.all(alt_sol >= -tol) and not np.allclose(alt_sol, current_sol, atol=tol):                    
                    alternatives.append({
                        'solution': alt_sol.tolist(),
                        'entering_var': basic_vars[0],  # Variable principal en la combinación
                        'pivot_row': -1,  # No hay fila pivote específica en este método
                        'method': 'convex_combination',
                        'weight': w
                    })
    
    return alternatives
