from flask import Blueprint, request, jsonify, send_from_directory, current_app, render_template, flash, redirect, url_for
import json
import os
import numpy as np
from .solvers import simplex, granm_solver, dosfases_solver
from .solvers import SimplexError, GranMError, DosFasesError, UnboundedError, DimensionError, InfeasibleError
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
        # Obtener datos del formulario
        c = list(map(float, request.form['c'].split(',')))
        A_rows = request.form['A'].strip().split('\n')
        A = [list(map(float, row.split(','))) for row in A_rows]
        b = list(map(float, request.form['b'].split(',')))
        minimize = request.form.get('minimize') == 'on'
        track_iterations = request.form.get('track_iterations') == 'on'
        
        # Resolver
        if track_iterations:
            solution, optimal_value, tableau_history, pivot_history = simplex(
                c, A, b, minimize=minimize, track_iterations=True
            )
            resultado = {
                'solution': solution.tolist() if hasattr(solution, 'tolist') else solution,
                'optimal_value': float(optimal_value),
                'tableau_history': [t.tolist() if hasattr(t, 'tolist') else t for t in tableau_history],
                'pivot_history': pivot_history,
                'success': True
            }
        else:
            solution, optimal_value = simplex(c, A, b, minimize=minimize)
            resultado = {
                'solution': solution.tolist() if hasattr(solution, 'tolist') else solution,
                'optimal_value': float(optimal_value),
                'success': True
            }
        
        return render_template('simplex.html', resultado=resultado)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('main.simplex_page'))

@main_bp.route('/resolver/granm', methods=['POST'])
def resolver_granm():
    try:
        # Obtener datos del formulario
        c = list(map(float, request.form['c'].split(',')))
        A_rows = request.form['A'].strip().split('\n')
        A = [list(map(float, row.split(','))) for row in A_rows]
        b = list(map(float, request.form['b'].split(',')))
        
        eq_constraints = None
        if request.form['eq_constraints'].strip():
            eq_constraints = list(map(int, request.form['eq_constraints'].split(',')))
        
        minimize = request.form.get('minimize') == 'on'
        track_iterations = request.form.get('track_iterations') == 'on'
        M = float(request.form.get('M', 1000))
        
        # Resolver
        if track_iterations:
            solution, optimal_value, tableau_history, pivot_history = granm_solver(
                c, A, b, eq_constraints=eq_constraints, minimize=minimize, 
                track_iterations=True, M=M
            )
            resultado = {
                'solution': solution.tolist() if hasattr(solution, 'tolist') else solution,
                'optimal_value': float(optimal_value),
                'tableau_history': [t.tolist() if hasattr(t, 'tolist') else t for t in tableau_history],
                'pivot_history': pivot_history,
                'success': True
            }
        else:
            solution, optimal_value = granm_solver(
                c, A, b, eq_constraints=eq_constraints, minimize=minimize, M=M
            )
            resultado = {
                'solution': solution.tolist() if hasattr(solution, 'tolist') else solution,
                'optimal_value': float(optimal_value),
                'success': True
            }
        
        return render_template('granm.html', resultado=resultado)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('main.granm_page'))

@main_bp.route('/resolver/dosfases', methods=['POST'])
def resolver_dosfases():
    try:
        # Obtener datos del formulario
        c = list(map(float, request.form['c'].split(',')))
        A_rows = request.form['A'].strip().split('\n')
        A = [list(map(float, row.split(','))) for row in A_rows]
        b = list(map(float, request.form['b'].split(',')))
        
        eq_constraints = None
        if request.form['eq_constraints'].strip():
            eq_constraints = list(map(int, request.form['eq_constraints'].split(',')))
        
        minimize = request.form.get('minimize') == 'on'
        track_iterations = request.form.get('track_iterations') == 'on'
        
        # Resolver
        if track_iterations:
            solution, optimal_value, tableau_history, pivot_history = dosfases_solver(
                c, A, b, eq_constraints=eq_constraints, minimize=minimize, 
                track_iterations=True
            )
            resultado = {
                'solution': solution.tolist() if hasattr(solution, 'tolist') else solution,
                'optimal_value': float(optimal_value),
                'tableau_history': [t.tolist() if hasattr(t, 'tolist') else t for t in tableau_history],
                'pivot_history': pivot_history,
                'success': True
            }
        else:
            solution, optimal_value = dosfases_solver(
                c, A, b, eq_constraints=eq_constraints, minimize=minimize
            )
            resultado = {
                'solution': solution.tolist() if hasattr(solution, 'tolist') else solution,
                'optimal_value': float(optimal_value),
                'success': True
            }
        
        return render_template('dosfases.html', resultado=resultado)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
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
                return render_template('simplex.html', 
                                     solution=result, 
                                     video_url=media_url)
            else:
                flash('¡Visualización generada exitosamente!', 'success')
                logger.info("Renderizando template con imagen")
                return render_template('simplex.html', 
                                     solution=result, 
                                     image_url=media_url)
        else:
            logger.warning(f"Archivo no encontrado o path vacío: {media_path}")
            flash('Error al generar la animación. Mostrando solo resultados.', 'warning')
            return render_template('simplex.html', solution=result)
            
    except Exception as e:
        logger.error(f"Error generating Simplex animation: {e}")
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
        result = dosfases_solver(c, A, b, eq_constraints=eq_constraints, minimize=minimize)
        
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
                                 video_url=f'/static/videos/{video_id}.mp4')
        else:
            flash('Error al generar la animación. Mostrando solo resultados.', 'warning')
            return render_template('dosfases.html', solution=result)
            
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
        
        # Solve with Gran M
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

# Solve using Two-Phase method
@api_bp.route('/resolver/dosfases', methods=['POST'])
def resolver_dosfases():
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
        
        # Solve with Two-Phase method
        if track_iterations:
            solution, z_opt, tableau_history, pivot_history = dosfases_solver(
                c, A, b, eq_constraints, minimize, track_iterations=True
            )
            result = {
                "solution": solution.tolist() if hasattr(solution, "tolist") else solution,
                "optimal_value": float(z_opt),
                "tableau_history": [t.tolist() for t in tableau_history] if hasattr(tableau_history[0], "tolist") else tableau_history,
                "pivot_history": pivot_history
            }
        else:
            solution, z_opt = dosfases_solver(
                c, A, b, eq_constraints, minimize, track_iterations=False
            )
            result = {
                "solution": solution.tolist() if hasattr(solution, "tolist") else solution,
                "optimal_value": float(z_opt)
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
