from flask import Blueprint, request, jsonify, send_from_directory, current_app, render_template, flash, redirect, url_for
import json
import os
import time
import numpy as np
from .solvers import simplex, granm_solver, dosfases_solver
from .solvers import SimplexError, GranMError, DosFasesError, UnboundedError, DimensionError, InfeasibleError
from .solvers.multiple_solutions_detector import detect_multiple_solutions, format_multiple_solutions_result
from .manim_renderer import generate_manim_animation
import uuid
import logging

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
            }            # ─ Detectar soluciones múltiples óptimas con nuevo detector ─
            final_tableau = tableau_history[-1]
            n_vars = len(c)
            
            # Usar el nuevo detector mejorado
            multiple_solutions_result = detect_multiple_solutions(final_tableau, n_vars)
            formatted_result = format_multiple_solutions_result(multiple_solutions_result)
            
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
            multiple_solutions_result = detect_multiple_solutions(final_tableau, n_vars)
            formatted_result = format_multiple_solutions_result(multiple_solutions_result)            
            # Integrar resultados al resultado principal
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
            multiple_solutions_result = detect_multiple_solutions(final_tableau, n_vars)
            formatted_result = format_multiple_solutions_result(multiple_solutions_result)            
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
        c = data.get('c', [])
        A = data.get('A', [[]])
        b = data.get('b', [])
        minimize = data.get('minimize', False)
        track_iterations = data.get('track_iterations', False)
        
        # Validate inputs
        if not c or not A or not b:
            return jsonify({"error": "Datos incompletos. Se requieren c, A y b."}), 400
          # Solve with Simplex
        if track_iterations:
            solution, z_opt, tableau_history, pivot_history = simplex(
                c, A, b, minimize=minimize, track_iterations=True
            )
            result = {
                "solution": solution.tolist() if hasattr(solution, "tolist") else solution,
                "optimal_value": float(z_opt),
                "tableau_history": [t.tolist() for t in tableau_history] if hasattr(tableau_history[0], "tolist") else tableau_history,
                "pivot_history": pivot_history
            }
            
            # ─ Detectar múltiples soluciones usando el detector mejorado ─
            try:
                final_tableau = tableau_history[-1]
                multiple_solutions_result = detect_multiple_solutions(
                    final_tableau, len(c), c, minimize=minimize
                )
                
                # Formatear resultado para compatibilidad con API
                result['multiple_solutions'] = format_multiple_solutions_result(multiple_solutions_result)
                
                # Mantener compatibilidad con API anterior
                result['has_multiple_solutions'] = multiple_solutions_result['has_multiple_solutions']
                result['multiple_solution_vars'] = multiple_solutions_result.get('variables_with_zero_cost', [])
                if multiple_solutions_result.get('alternative_solutions'):
                    result['alternative_solutions'] = multiple_solutions_result['alternative_solutions']
                
            except Exception as e:
                logger.warning(f"Error en detección de múltiples soluciones: {e}")
                result['multiple_solutions'] = {'has_multiple_solutions': False, 'error': str(e)}
        else:
            solution, z_opt = simplex(
                c, A, b, minimize=minimize, track_iterations=False
            )
            result = {
                "solution": solution.tolist() if hasattr(solution, "tolist") else solution,
                "optimal_value": float(z_opt)
            }
        
        return jsonify(result)
    except (SimplexError, DimensionError, UnboundedError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception("Error in Simplex solver")
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

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
            }

            # ─ Detectar múltiples soluciones usando el detector mejorado ─
            try:
                final_tableau = tableau_history[-1]
                multiple_solutions_result = detect_multiple_solutions(
                    final_tableau, len(c), c, minimize=minimize
                )

                # Formatear resultado
                result['multiple_solutions'] = format_multiple_solutions_result(multiple_solutions_result)
                result['has_multiple_solutions'] = multiple_solutions_result['has_multiple_solutions']
                result['multiple_solution_vars'] = multiple_solutions_result.get('variables_with_zero_cost', [])

                if multiple_solutions_result.get('alternative_solutions'):
                    result['alternative_solutions'] = multiple_solutions_result['alternative_solutions']

            except Exception as e:
                logger.warning(f"Error en detección de múltiples soluciones: {e}")
                result['multiple_solutions'] = {'has_multiple_solutions': False, 'error': str(e)}

        # Resolver sin iteraciones
        else:
            solution, z_opt = granm_solver(
                c, A, b, eq_constraints, minimize, track_iterations=False
            )
            result = {
                "solution": solution.tolist() if hasattr(solution, "tolist") else solution,
                "optimal_value": float(z_opt)
            }

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
    
    # Handle numpy scalars
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
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
                "pivot_history": convert_numpy_types(pivot_history)
            }
            
            # ─ Detectar y generar soluciones múltiples óptimas (Dos Fases - API) ─
            final_tableau = tableau_history[-1]
            z_row = final_tableau[0, :-1]
            n_vars = len(c)

            non_basic_zero_cost = []
            for j in range(n_vars):  # Solo variables originales
                col = final_tableau[1:, j]
                if np.count_nonzero(col) != 1 or not np.isclose(col.max(), 1.0):
                    # Está fuera de la base
                    if abs(z_row[j]) < 1e-8:  # costo reducido ≈ 0
                        non_basic_zero_cost.append(j)

            result['has_multiple_solutions'] = bool(non_basic_zero_cost)
            result['multiple_solution_vars'] = convert_numpy_types(non_basic_zero_cost)

            # Generar soluciones alternativas si existen
            alternative_solutions = []
            if non_basic_zero_cost:
                for var_to_enter in non_basic_zero_cost:
                    try:
                        # Crear una copia del tableau final para pivotear
                        tableau_copy = final_tableau.copy()
                        
                        # Encontrar la fila pivote (ratio test)
                        entering_col = tableau_copy[1:, var_to_enter]
                        rhs_col = tableau_copy[1:, -1]
                        
                        # Solo considerar ratios positivos
                        valid_ratios = []
                        for i, (col_val, rhs_val) in enumerate(zip(entering_col, rhs_col)):
                            if col_val > 1e-8:  # Evitar división por cero/negativo
                                valid_ratios.append((rhs_val / col_val, i + 1))  # i+1 porque saltamos la fila z
                        
                        if valid_ratios:
                            # Encontrar el mínimo ratio (regla del pivote)
                            min_ratio, pivot_row = min(valid_ratios)
                            
                            # Realizar el pivoteo
                            pivot_element = tableau_copy[pivot_row, var_to_enter]
                            
                            # Normalizar la fila pivote
                            tableau_copy[pivot_row, :] /= pivot_element
                            
                            # Eliminar la columna pivote en otras filas
                            for i in range(tableau_copy.shape[0]):
                                if i != pivot_row:
                                    factor = tableau_copy[i, var_to_enter]
                                    tableau_copy[i, :] -= factor * tableau_copy[pivot_row, :]
                            
                            # Extraer la nueva solución
                            new_solution = np.zeros(n_vars)
                            
                            # Identificar variables básicas en el nuevo tableau
                            for j in range(n_vars):
                                col = tableau_copy[1:, j]
                                # Si es una columna unitaria (variable básica)
                                if np.count_nonzero(col) == 1 and np.isclose(col.max(), 1.0):
                                    basic_row = np.where(np.isclose(col, 1.0))[0][0] + 1
                                    new_solution[j] = tableau_copy[basic_row, -1]
                              # Verificar que la solución es válida (no negativa)
                            if np.all(new_solution >= -1e-8):  # Tolerancia para errores numéricos
                                new_solution = np.maximum(new_solution, 0)  # Limpiar valores muy pequeños negativos
                                alternative_solutions.append({
                                    'solution': convert_numpy_types(new_solution),
                                    'entering_var': convert_numpy_types(var_to_enter),
                                    'pivot_row': convert_numpy_types(pivot_row - 1)  # Ajustar índice
                                })
                        
                    except Exception as e:
                        # Si hay error al generar esta solución alternativa, continuar con la siguiente
                        logger.warning(f"Error generando solución alternativa para variable {var_to_enter}: {e}")
                        continue            
            result['alternative_solutions'] = alternative_solutions
        else:
            solution, z_opt = dosfases_solver(
                c, A, b, eq_constraints=eq_constraints, ge_constraints=ge_constraints, 
                minimize=minimize, track_iterations=False
            )
            result = {
                "solution": convert_numpy_types(solution),
                "optimal_value": convert_numpy_types(z_opt)
            }
        
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
