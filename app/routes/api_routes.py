"""
Rutas de la API REST.
"""

import json
import os
import logging
import uuid
from flask import Blueprint, request, jsonify, send_from_directory, current_app

from ..solvers import simplex, granm_solver, dosfases_solver
from ..solvers import SimplexError, GranMError, DosFasesError, UnboundedError, DimensionError, InfeasibleError
from ..utils import (
    convert_numpy_types, 
    load_casos, 
    save_casos,
    detect_multiple_solutions,
    format_multiple_solutions_result,
    _to_list
)

logger = logging.getLogger(__name__)

# API blueprint with /api prefix
api_bp = Blueprint('api', __name__, url_prefix='/api')


# ===== GESTIÓN DE CASOS =====

@api_bp.route('/casos', methods=['GET'])
def get_casos():
    """Get all optimization examples"""
    casos = load_casos()
    return jsonify(casos)


@api_bp.route('/casos/<int:caso_id>', methods=['GET'])
def get_caso(caso_id):
    """Get a specific example by index"""
    casos = load_casos()
    if 0 <= caso_id < len(casos):
        return jsonify(casos[caso_id])
    return jsonify({'error': 'Caso no encontrado'}), 404


@api_bp.route('/casos', methods=['POST'])
def add_caso():
    """Add a new example"""
    try:
        new_caso = request.get_json()
        if not new_caso:
            return jsonify({'error': 'No se recibieron datos'}), 400
            
        casos = load_casos()
        casos.append(new_caso)
        save_casos(casos)
        
        return jsonify({'message': 'Caso agregado exitosamente', 'id': len(casos) - 1}), 201
        
    except Exception as e:
        logger.error(f"Error al agregar caso: {e}")
        return jsonify({'error': f'Error al agregar caso: {str(e)}'}), 500


@api_bp.route('/casos/<int:caso_id>', methods=['DELETE'])
def delete_caso(caso_id):
    """Delete an example"""
    casos = load_casos()
    if 0 <= caso_id < len(casos):
        deleted_caso = casos.pop(caso_id)
        save_casos(casos)
        return jsonify({'message': 'Caso eliminado exitosamente', 'deleted': deleted_caso})
    return jsonify({'error': 'Caso no encontrado'}), 404


# ===== RESOLUCIÓN DE MÉTODOS =====

@api_bp.route('/resolver/simplex', methods=['POST'])
def resolver_simplex_api():
    """Solve using Simplex method"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se recibieron datos JSON'}), 400

        # Extraer datos
        c = data.get('c', [])
        A = data.get('A', [])
        b = data.get('b', [])
        minimize = data.get('minimize', False)
        track_iterations = data.get('track_iterations', False)

        if not all([c, A, b]):
            return jsonify({'error': 'Faltan datos requeridos (c, A, b)'}), 400        # Resolver
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

        # Convertir tipos numpy
        resultado = convert_numpy_types(resultado)
        return jsonify(resultado)

    except (SimplexError, DimensionError, UnboundedError) as e:
        logger.error(f"Error en método Simplex: {str(e)}")
        return jsonify({'error': f'Error en método Simplex: {str(e)}'}), 400

    except Exception as e:
        logger.error(f"Error inesperado en Simplex API: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error inesperado: {str(e)}'}), 500


@api_bp.route('/resolver/granm', methods=['POST'])
def resolver_granm_api():
    """Solve using Gran M method"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se recibieron datos JSON'}), 400

        # Extraer datos
        c = data.get('c', [])
        A = data.get('A', [])
        b = data.get('b', [])
        sense = data.get('sense', ['≤'] * len(b))
        minimize = data.get('minimize', False)
        track_iterations = data.get('track_iterations', False)
        M = data.get('M', 1e6)

        if not all([c, A, b]):
            return jsonify({'error': 'Faltan datos requeridos (c, A, b)'}), 400

        # Resolver
        if track_iterations:
            sol, z, T_hist, piv_hist = granm_solver(
                c, A, b, sense,
                minimize=minimize, track_iterations=True, M=M
            )
        else:
            resultado = granm_solver.solve(c, A, b, sense, minimize=minimize, M=M)

        # Detectar soluciones múltiples si hay tableau final
        if 'tableau_final' in resultado:
            multiple_info = detect_multiple_solutions(
                resultado['tableau_final'], 
                len(c), 
                c, 
                minimize
            )
            resultado['multiple_solutions'] = format_multiple_solutions_result(multiple_info)

        # Convertir tipos numpy
        resultado = convert_numpy_types(resultado)
        return jsonify(resultado)

    except (GranMError, DimensionError, UnboundedError) as e:
        logger.error(f"Error en método Gran M: {str(e)}")
        return jsonify({'error': f'Error en método Gran M: {str(e)}'}), 400

    except Exception as e:
        logger.error(f"Error inesperado en Gran M API: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error inesperado: {str(e)}'}), 500


@api_bp.route('/resolver/dosfases', methods=['POST'])
def resolver_dosfases_api():
    """Solve using Two-Phase method"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se recibieron datos JSON'}), 400

        # Extraer datos
        c = data.get('c', [])
        A = data.get('A', [])
        b = data.get('b', [])
        eq_constraints = data.get('eq_constraints')
        ge_constraints = data.get('ge_constraints')
        minimize = data.get('minimize', False)
        track_iterations = data.get('track_iterations', False)

        if not all([c, A, b]):
            return jsonify({'error': 'Faltan datos requeridos (c, A, b)'}), 400        # Resolver
        if track_iterations:
            solution, optimal_value, tableau_history, pivot_history = dosfases_solver(
                c, A, b, eq_constraints=eq_constraints, ge_constraints=ge_constraints,
                minimize=minimize, track_iterations=True
            )
        else:
            resultado = dosfases_solver.solve(
                c, A, b, eq_constraints, ge_constraints, minimize=minimize
            )

        # Detectar soluciones múltiples si hay tableau final
        if 'tableau_final' in resultado:
            multiple_info = detect_multiple_solutions(
                resultado['tableau_final'], 
                len(c), 
                c, 
                minimize
            )
            resultado['multiple_solutions'] = format_multiple_solutions_result(multiple_info)

        # Convertir tipos numpy
        resultado = convert_numpy_types(resultado)
        return jsonify(resultado)

    except (DosFasesError, DimensionError, UnboundedError, InfeasibleError) as e:
        logger.error(f"Error en método Dos Fases: {str(e)}")
        return jsonify({'error': f'Error en método Dos Fases: {str(e)}'}), 400

    except Exception as e:
        logger.error(f"Error inesperado en Dos Fases API: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error inesperado: {str(e)}'}), 500


# ===== ARCHIVOS ESTÁTICOS =====

@api_bp.route('/upload', methods=['POST'])
def upload_file():
    """Upload a JSON file with examples"""
    if 'file' not in request.files:
        return jsonify({'error': 'No se seleccionó archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó archivo'}), 400
    
    if file and file.filename.endswith('.json'):
        try:
            data = json.load(file)
            save_casos(data)
            return jsonify({'message': 'Archivo cargado exitosamente', 'casos_count': len(data)})
        except json.JSONDecodeError:
            return jsonify({'error': 'Archivo JSON inválido'}), 400
        except Exception as e:
            logger.error(f"Error al cargar archivo: {e}")
            return jsonify({'error': f'Error al procesar archivo: {str(e)}'}), 500
    
    return jsonify({'error': 'Solo se permiten archivos JSON'}), 400


# Favicon route (moved from main routes)
@api_bp.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory(os.path.join(current_app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
