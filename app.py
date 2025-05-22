import streamlit as st
import numpy as np
import pandas as pd
import json
from simplex import simplex, SimplexError, DimensionError, NegativeBError, UnboundedError
import io
import base64
import subprocess
import os
import sys
import time
from pathlib import Path

# Inicializar el estado de la sesión si no existe
if 'solved' not in st.session_state:
    st.session_state.solved = False
if 'solution_data' not in st.session_state:
    st.session_state.solution_data = {}
if 'generating_animation' not in st.session_state:
    st.session_state.generating_animation = False
if 'animation_generated' not in st.session_state:
    st.session_state.animation_generated = False
if 'video_path' not in st.session_state:
    st.session_state.video_path = None

# Función para manejar el botón de generar animación
def handle_generate_animation():
    st.session_state.generating_animation = True

# Función para manejar cuando se completa la animación
def handle_animation_complete(video_path):
    st.session_state.animation_generated = True
    st.session_state.video_path = video_path
    st.session_state.generating_animation = False

# Función para reiniciar el estado de la animación
def reset_animation_state():
    st.session_state.solved = False
    st.session_state.solution_data = {}
    st.session_state.generating_animation = False
    st.session_state.animation_generated = False
    st.session_state.video_path = None

st.set_page_config(page_title="Método Simplex", layout="centered")
st.title("🔺 Solucionador Simplex")

st.markdown("Ingresa los coeficientes para resolver problemas de programación lineal usando el método Simplex.")

# Pestañas para elegir entre entrada manual o cargar desde JSON
tab1, tab2 = st.tabs(["Entrada manual", "Cargar desde JSON"])

with tab1:
    # Sección para tipo de optimización y tamaño del problema
    col1, col2 = st.columns(2)
    with col1:
        optimization_type = st.radio("Tipo de optimización", ["Maximización", "Minimización"])
    with col2:
        show_iterations = st.checkbox("Mostrar iteraciones", value=True)

    # Dimensiones del problema
    num_vars = st.number_input("Número de variables (n)", min_value=1, max_value=10, value=2)
    num_constraints = st.number_input("Número de restricciones (m)", min_value=1, max_value=10, value=3)

    st.subheader("Función objetivo (c)")
    c_input = []
    cols = st.columns(num_vars)
    for i in range(num_vars):
        c_input.append(cols[i].number_input(f"c[{i+1}]", value=0.0))

    st.subheader("Matriz de restricciones (A)")
    A_input = []
    for i in range(num_constraints):
        row = []
        cols = st.columns(num_vars)
        for j in range(num_vars):
            row.append(cols[j].number_input(f"A[{i+1},{j+1}]", value=0.0, key=f"A{i}{j}"))
        A_input.append(row)

    st.subheader("Vector lado derecho (b)")
    b_input = []
    cols = st.columns(num_constraints)
    for i in range(num_constraints):
        b_input.append(cols[i].number_input(f"b[{i+1}]", value=0.0, key=f"b{i}"))

with tab2:
    st.subheader("Cargar casos de prueba desde JSON")
    
    # Opción 1: Cargar archivo JSON
    uploaded_file = st.file_uploader("Selecciona un archivo JSON", type=["json"])
    
    # Opción 2: Pegar contenido JSON
    json_text = st.text_area("O pega el contenido JSON aquí:", height=200)
    
    # Opción 3: Usar un caso predefinido de ejemplo
    st.markdown("### O selecciona un caso de ejemplo:")
    
    # Verificar si hay casos disponibles en el sistema
    try:
        with open("casos_simplex/casos.json", "r") as f:
            casos_disponibles = json.load(f)
        caso_names = [caso["nombre"] for caso in casos_disponibles]
        selected_caso = st.selectbox("Casos disponibles:", ["Selecciona un caso..."] + caso_names)
    except (FileNotFoundError, json.JSONDecodeError):
        st.warning("No se encontró el archivo casos_simplex/casos.json o tiene un formato incorrecto.")
        casos_disponibles = []
        selected_caso = None
    
    # Mostrar vista previa del caso seleccionado
    if uploaded_file is not None:
        try:
            datos_json = json.load(uploaded_file)
            st.success("✅ Archivo JSON cargado correctamente")
            st.write("Vista previa del primer caso:")
            if isinstance(datos_json, list) and len(datos_json) > 0:
                st.write(datos_json[0])
            else:
                st.write(datos_json)
        except json.JSONDecodeError:
            st.error("❌ Error al parsear el archivo JSON. Verifica el formato.")
            datos_json = None
    elif json_text:
        try:
            datos_json = json.loads(json_text)
            st.success("✅ JSON ingresado correctamente")
            st.write("Vista previa del primer caso:")
            if isinstance(datos_json, list) and len(datos_json) > 0:
                st.write(datos_json[0])
            else:
                st.write(datos_json)
        except json.JSONDecodeError:
            st.error("❌ Error al parsear el JSON ingresado. Verifica el formato.")
            datos_json = None
    elif selected_caso and selected_caso != "Selecciona un caso...":
        # Cargar caso seleccionado
        for caso in casos_disponibles:
            if caso["nombre"] == selected_caso:
                datos_json = [caso]  # Convertir a lista para compatibilidad
                st.write("Vista previa del caso seleccionado:")
                st.write(caso)
                break
    else:
        datos_json = None
    
    if datos_json:
        # Verificar formato del JSON
        if not isinstance(datos_json, list):
            datos_json = [datos_json]  # Convertir a lista si es un solo objeto
        
        # Si hay múltiples casos, permitir seleccionar uno
        if len(datos_json) > 1:
            if isinstance(datos_json[0], dict) and "nombre" in datos_json[0]:
                caso_names = [caso.get("nombre", f"Caso {i+1}") for i, caso in enumerate(datos_json)]
                selected_index = st.selectbox("Selecciona un caso específico:", 
                                             range(len(caso_names)), 
                                             format_func=lambda i: caso_names[i])
                selected_data = datos_json[selected_index]
            else:
                selected_index = st.number_input("Selecciona un índice de caso:", 
                                               min_value=0, 
                                               max_value=len(datos_json)-1, 
                                               value=0)
                selected_data = datos_json[selected_index]
        else:
            selected_data = datos_json[0]
        
        # Opción para guardar el conjunto de casos en el sistema
        if uploaded_file is not None or json_text:
            if st.button("Guardar casos en el sistema"):
                try:
                    with open("casos_simplex/casos.json", "w") as f:
                        json.dump(datos_json, f, indent=4)
                    st.success("✅ Casos guardados correctamente en casos_simplex/casos.json")
                except Exception as e:
                    st.error(f"❌ Error al guardar: {e}")
        
        # Opción para usar este caso
        st.subheader("Usar este caso para resolver:")
        col1, col2 = st.columns(2)
        with col1:
            json_optimization_type = st.radio("Tipo de optimización (JSON)", 
                                             ["Maximización", "Minimización"], key="json_opt")
        with col2:
            json_show_iterations = st.checkbox("Mostrar iteraciones (JSON)", 
                                             value=True, key="json_iter")

# Función para generar un enlace de descarga
def get_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 {text}</a>'
    return href

# Función para generar archivo Excel
def get_excel_download_link(df_dict, filename, text):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet_name, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    binary_data = output.getvalue()
    b64 = base64.b64encode(binary_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">📥 {text}</a>'
    return href

# Función para generar animación Manim
def generate_manim_animation(c, A, b, solution, z_opt, minimize=False):
    """
    Genera una animación Manim del problema Simplex y su solución
    """
    try:
        # Crear carpetas necesarias si no existen
        for path in ["output", "output/videos", "output/videos/720p30", "output/videos/simplex_anim"]:
            os.makedirs(path, exist_ok=True)
            st.write(f"✓ Carpeta creada/verificada: {path}")
        
        # Asegurar que manim_anim existe
        os.makedirs("manim_anim", exist_ok=True)
        st.write(f"✓ Carpeta creada/verificada: manim_anim")
        
        # Verificar que Manim esté instalado
        try:
            import importlib
            manim_spec = importlib.util.find_spec("manim")
            if manim_spec is None:
                st.error("❌ Manim no está instalado. Ejecuta: pip install manim")
                return None
            st.success("✅ Manim está instalado correctamente.")
        except Exception as e:
            st.error(f"❌ Error al verificar instalación de Manim: {str(e)}")
            st.info("Intenta ejecutar: pip install manim")
            return None
        
        # Crear archivo temporal con los datos del problema
        problem_data = {
            "c": c,
            "A": A,
            "b": b,
            "solution": solution if isinstance(solution, list) else solution.tolist() if hasattr(solution, 'tolist') else list(solution),
            "z_opt": float(z_opt) if isinstance(z_opt, (int, float, np.number)) else z_opt,
            "minimize": minimize
        }
        
        # Convertir valores no serializables a tipos básicos
        for key in problem_data:
            if isinstance(problem_data[key], np.ndarray):
                problem_data[key] = problem_data[key].tolist()
            elif isinstance(problem_data[key], np.number):
                problem_data[key] = float(problem_data[key])
            elif isinstance(problem_data[key], list):
                for i, item in enumerate(problem_data[key]):
                    if isinstance(item, np.ndarray):
                        problem_data[key][i] = item.tolist()
                    elif isinstance(item, np.number):
                        problem_data[key][i] = float(item)
            
        # Mostrar los datos que se están pasando a la animación
        st.write("Datos para la animación:")
        st.code(json.dumps(problem_data, indent=2))
        
        # Guardar datos en un archivo temporal
        try:
            with open("manim_anim/problem_data.json", "w", encoding="utf-8", errors="replace") as f:
                json.dump(problem_data, f, ensure_ascii=True, indent=2)
            st.success("✅ Archivo problem_data.json creado correctamente")
            
            # Verificar que se creó correctamente
            if os.path.exists("manim_anim/problem_data.json"):
                file_size = os.path.getsize("manim_anim/problem_data.json")
                st.write(f"Archivo de datos creado. Tamaño: {file_size} bytes")
                
                # Leer primeras líneas para verificar contenido
                with open("manim_anim/problem_data.json", "r", encoding="utf-8", errors="replace") as f:
                    content = f.read(500)  # Leer primeros 500 bytes
                st.code(f"Primeras líneas del archivo:\n{content}...", language="json")
            else:
                st.error("❌ El archivo problem_data.json no se creó correctamente")
        except Exception as e:
            st.error(f"❌ Error al escribir problem_data.json: {str(e)}")
            import traceback
            st.code(traceback.format_exc(), language="python")
            return None
        
        # Verificar que los scripts de animación existen
        scripts_to_use = []
        for script, class_name in [
            ("basic_simplex_anim.py", "SimplexBasicAnim"),  # Versión básica más robusta
            ("simple_anim.py", "SimplexAnim"),              # Versión simplificada
            ("simplex_anim.py", "SimplexAnim")              # Versión completa
        ]:
            script_path = os.path.join("manim_anim", script)
            if os.path.exists(script_path) and os.path.getsize(script_path) > 0:
                st.success(f"✅ Script encontrado: {script}")
                scripts_to_use.append((script, class_name))
            else:
                st.warning(f"⚠️ Script no encontrado o vacío: {script}")
        
        if not scripts_to_use:
            st.error("❌ No se encontraron scripts de animación válidos.")
            return None
        
        # Mostrar mensaje de generación
        with st.spinner("🎬 Generando animación del método Simplex..."):
            try:
                # Intentar cada script en orden
                for script, class_name in scripts_to_use:
                    try:
                        # Mostrar qué script se está probando
                        st.write(f"Intentando con el script: {script}")
                        
                        # Ejecutar Manim con más opciones de diagnóstico de forma cross-platform
                        python_exe = sys.executable
                        
                        # Construir comando como lista y usar cwd en Popen para evitar problemas de shell o rutas
                        cmd = [
                            python_exe,
                            "-m", "manim",
                            script,
                            class_name,
                            "-ql",
                            "--media_dir=../output"
                        ]
                        st.write(f"Comando Popen: {cmd}, cwd='manim_anim'")
                        
                        # Verificar el entorno Python antes de ejecutar
                        st.write("Verificando entorno Python:")
                        env_cmd = f'"{python_exe}" -c "import sys; print(sys.version); import os; print(os.getcwd()); print(\\"PATH = \\" + os.environ[\\"PATH\\"])"'
                        env_process = subprocess.Popen(
                            env_cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            encoding="utf-8",
                            errors="replace"
                        )
                        env_stdout, env_stderr = env_process.communicate(timeout=10)
                        st.code(f"Python info:\n{env_stdout}\nErrors: {env_stderr}", language="bash")
                        
                        # Ejecutar el comando como subproceso con más tiempo
                        process = subprocess.Popen(
                            cmd,
                            cwd="manim_anim",
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            encoding="utf-8",
                            errors="replace"
                        )
                        
                        # Capturar salida con un timeout más largo
                        stdout, stderr = process.communicate(timeout=180)  # 3 minutos
                        
                        # Mostrar tanto stdout como stderr para mejor diagnóstico
                        st.write(f"Salida estándar de Manim ({script}):")
                        st.code(stdout[:1500] + "..." if len(stdout) > 1500 else stdout, language="bash")
                        
                        st.write(f"Errores de Manim ({script}):")
                        st.code(stderr[:1500] + "..." if len(stderr) > 1500 else stderr, language="bash")
                        
                        # Verificar si el proceso se completó correctamente
                        st.write(f"Código de salida: {process.returncode}")
                        
                        if process.returncode == 0:
                            # Buscar videos en múltiples directorios posibles
                            for video_dir in [
                                "output/videos/720p30",
                                "output/videos", 
                                "output/videos/simplex_anim",
                                "output"
                            ]:
                                if os.path.exists(video_dir):
                                    st.write(f"Buscando videos en: {video_dir}")
                                    video_files = [
                                        os.path.join(video_dir, f) 
                                        for f in os.listdir(video_dir) 
                                        if f.endswith('.mp4')
                                    ]
                                    
                                    if video_files:
                                        # Ordenar por fecha de modificación (más reciente primero)
                                        video_files.sort(key=os.path.getmtime, reverse=True)
                                        st.write(f"Videos encontrados: {len(video_files)}")
                                        
                                        for video in video_files[:3]:  # Mostrar los 3 más recientes
                                            st.write(f"- {video} (Modificado: {os.path.getmtime(video)})")
                                        
                                        latest_video = video_files[0]
                                        st.success(f"✅ Video seleccionado: {latest_video}")
                                        return latest_video
                                    else:
                                        st.write(f"No se encontraron videos en {video_dir}")
                            
                            st.warning(f"⚠️ El script {script} no generó un archivo de video visible")
                            continue
                        else:
                            st.warning(f"⚠️ El script {script} falló con código {process.returncode}")
                            continue
                    except subprocess.TimeoutExpired:
                        st.warning(f"⚠️ Timeout para el script {script} (180 segundos)")
                        continue
                    except Exception as e:
                        st.warning(f"⚠️ Error con el script {script}: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc(), language="python")
                        continue
                
                # Si llegamos aquí, todos los scripts fallaron
                st.error("❌ Todos los scripts de animación fallaron")
                
                # Verificar si hay algún video generado anteriormente como fallback
                for video_dir in ["output/videos/720p30", "output/videos", "output"]:
                    if os.path.exists(video_dir):
                        video_files = [
                            os.path.join(video_dir, f) 
                            for f in os.listdir(video_dir) 
                            if f.endswith('.mp4')
                        ]
                        if video_files:
                            video_files.sort(key=os.path.getmtime, reverse=True)
                            latest_video = video_files[0]
                            st.warning(f"⚠️ Usando video existente como fallback: {latest_video}")
                            return latest_video
                
                return None
                
            except subprocess.TimeoutExpired:
                st.error("❌ La generación de la animación excedió el tiempo límite general")
                process.kill() if 'process' in locals() else None
                return None
            except Exception as e:
                st.error(f"❌ Error inesperado al generar la animación: {str(e)}")
                import traceback
                st.code(traceback.format_exc(), language="python")
                return None
    except Exception as e:
        st.error(f"❌ Error general al generar la animación: {str(e)}")
        import traceback
        st.code(traceback.format_exc(), language="python")
        return None

# Botones para resolver
if st.button("Resolver Simplex (Entrada Manual)", key="solve_manual", on_click=reset_animation_state):
    try:
        # Determinar si es minimización o maximización
        minimize = optimization_type == "Minimización"
        
        # Resolver el problema
        if show_iterations:
            solution, z_opt, tableau_history, pivot_history = simplex(
                c_input, A_input, b_input, minimize=minimize, track_iterations=True
            )
        else:
            solution, z_opt = simplex(
                c_input, A_input, b_input, minimize=minimize, track_iterations=False
            )
        
        # Mostrar la solución
        st.success("✅ Solución encontrada")
        
        operation = "minimización" if minimize else "maximización"
        st.write(f"**Resultado de {operation}:**")
        st.write("**Solución óptima:**", solution)
        st.write(f"**Valor óptimo {'mínimo' if minimize else 'máximo'} Z:**", z_opt)
        
        # Crear un DataFrame para la solución
        solution_df = pd.DataFrame({
            'Variable': [f'x{i+1}' for i in range(len(solution))],
            'Valor': solution
        })
        solution_df = solution_df.round(4)
        
        # Mostrar la tabla de solución
        st.subheader("Tabla de solución")        
        st.dataframe(solution_df)
        # Generar el enlace de descarga para la solución
        st.markdown(get_download_link(solution_df, "simplex_solucion.csv", "Descargar solución (CSV)"), unsafe_allow_html=True)
          # Generar animación Manim
        with st.expander("🎬 Animación del Método Simplex", expanded=True):
            st.warning("**Nota:** La generación de animaciones puede tardar varios minutos y requiere que Manim esté correctamente instalado.")
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                # Guardamos los datos de la solución en session_state
                if not st.session_state.solved:
                    st.session_state.solved = True
                    st.session_state.solution_data = {
                        'c': c_input,
                        'A': A_input,
                        'b': b_input,
                        'solution': solution,
                        'z_opt': z_opt,
                        'minimize': minimize
                    }
                
                # Usar un botón en lugar de checkbox para evitar recarga
                generate_animation_btn = st.button("Generar animación", 
                                                 key="gen_anim_btn", 
                                                 on_click=handle_generate_animation,
                                                 disabled=st.session_state.generating_animation or st.session_state.animation_generated)
                
                if st.session_state.animation_generated and st.session_state.video_path:
                    st.success("✅ Animación ya generada")
            with col2:
                st.markdown("")
                st.markdown("")
                check_manim = st.button("✓ Verificar Manim", disabled=st.session_state.generating_animation)
            with col3:
                st.markdown("")
                st.markdown("")
                test_manim = st.button("🧪 Probar Manim", disabled=st.session_state.generating_animation)
            
            if check_manim:
                with st.spinner("Verificando instalación de Manim..."):
                    try:
                        # Ejecutar manim --version para comprobar instalación
                        cmd = [sys.executable, "-m", "manim", "--version"]
                        st.write(f"DEBUG: Ejecutando comando: {cmd}")
                        proc = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            encoding="utf-8",
                            errors="replace"
                        )
                        out, err = proc.communicate(timeout=15)
                        st.write(f"DEBUG: Código de salida: {proc.returncode}")
                        st.write(f"DEBUG: stdout: {out}")
                        st.write(f"DEBUG: stderr: {err}")
                        if proc.returncode == 0:
                            st.success(f"✅ Manim instalado. Versión: {out.strip()}")
                        else:
                            st.error("❌ Manim no parece estar instalado o falla al ejecutarse.")
                            st.info("Instala con: pip install manim")
                    except Exception as e:
                        import traceback
                        st.error(f"❌ Excepción al verificar Manim: {e}")
                        st.code(traceback.format_exc(), language="python")
            
            # Si el botón fue presionado o la animación ya está siendo generada
            if st.session_state.generating_animation and not st.session_state.animation_generated:
                try:
                    st.info("Generando animación... Este proceso puede tardar varios minutos. **No cambies la página ni interactúes con la app durante la generación.**")
                    
                    # Crear tiempo de inicio para medir duración
                    start_time = time.time()
                    
                    # Usar los datos guardados en session_state
                    data = st.session_state.solution_data
                    video_path = generate_manim_animation(
                        data['c'], data['A'], data['b'], 
                        data['solution'], data['z_opt'], 
                        data['minimize']
                    )
                    
                    # Calcular duración
                    duration = time.time() - start_time
                    
                    if video_path and os.path.exists(video_path):
                        # Actualizar el estado
                        handle_animation_complete(video_path)
                        
                        st.success(f"✅ Animación generada correctamente en {duration:.1f} segundos")
                        
                        # Mostrar video
                        st.video(video_path)
                        
                        # Proporcionar enlace de descarga
                        with open(video_path, "rb") as file:
                            video_bytes = file.read()
                            st.download_button(
                                label="📥 Descargar animación (MP4)",
                                data=video_bytes,
                                file_name="simplex_animation.mp4",
                                mime="video/mp4"
                            )
                    else:
                        st.error("❌ No se pudo generar la animación.")
                        st.session_state.generating_animation = False
                        st.info("Puedes intentar las siguientes soluciones:")
                        st.markdown("""
                        1. Verifica que Manim esté instalado correctamente (botón "Verificar Manim")
                        2. Reinicia la aplicación
                        3. Comprueba que tienes suficiente espacio en disco
                        4. Revisa si hay errores específicos en la sección de salida anterior
                        """)
                except Exception as e:
                    st.error(f"❌ Error en la generación de la animación: {str(e)}")
                    st.session_state.generating_animation = False
                    import traceback
                    st.code(traceback.format_exc(), language="python")
            
            # Mostrar video si ya fue generado
            elif st.session_state.animation_generated and st.session_state.video_path:
                if os.path.exists(st.session_state.video_path):
                    st.video(st.session_state.video_path)
                    
                    # Proporcionar enlace de descarga
                    with open(st.session_state.video_path, "rb") as file:
                        video_bytes = file.read()
                        st.download_button(
                            label="📥 Descargar animación (MP4)",
                            data=video_bytes,
                            file_name="simplex_animation.mp4",
                            mime="video/mp4"
                        )
        
        # Mostrar las iteraciones si se solicitó
        if show_iterations and tableau_history:
            st.subheader("Iteraciones del método Simplex")
            
            # Crear DataFrames para cada tableau
            tableau_dfs = {}
            
            for i, (tableau, pivot) in enumerate(zip(tableau_history, pivot_history)):
                # Crear etiquetas para columnas
                col_labels = [f'x{j+1}' for j in range(len(c_input))]
                col_labels += [f's{j+1}' for j in range(num_constraints)]
                col_labels += ['b']
                
                # Crear etiquetas para filas
                row_labels = [f'Restricción {j+1}' for j in range(num_constraints)]
                row_labels += ['Función objetivo']
                
                # Convertir el tableau a un DataFrame
                df = pd.DataFrame(tableau, columns=col_labels, index=row_labels)
                df = df.round(4)  # Redondear a 4 decimales
                
                # Resaltar la celda pivote si no es la iteración inicial
                if i > 0:
                    row_p, col_p = pivot
                    
                    # Mostrar información del pivote
                    st.write(f"**Iteración {i}** - Elemento pivote: "
                             f"Fila {row_p+1} ('{row_labels[row_p]}'), "
                             f"Columna '{col_labels[col_p]}'")
                else:
                    st.write("**Tableau inicial**")
                
                # Mostrar el tableau
                st.dataframe(df)
                
                # Guardar para exportación
                tableau_dfs[f'Iteración {i}'] = df.reset_index().rename(columns={'index': 'Fila/Columna'})
            
            # Generar enlaces de descarga para todas las iteraciones
            st.markdown(get_excel_download_link(tableau_dfs, "simplex_iteraciones.xlsx", 
                                             "Descargar todas las iteraciones (Excel)"), 
                      unsafe_allow_html=True)

    except DimensionError as e:
        st.error(f"❌ Error de dimensiones: {e}")
    except NegativeBError as e:
        st.error(f"❌ Error: El vector b tiene valores negativos. {e}")
    except UnboundedError as e:
        st.error(f"❌ Problema no acotado: {e}")
    except SimplexError as e:
        st.error(f"❌ Error general del método Simplex: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")

# Botón para resolver desde JSON
if 'datos_json' in locals() and datos_json and st.button("Resolver Simplex (Desde JSON)", key="solve_json", on_click=reset_animation_state):
    try:
        # Extraer datos del caso seleccionado
        if isinstance(selected_data, dict) and all(k in selected_data for k in ["c", "A", "b"]):
            c_json = selected_data["c"]
            A_json = selected_data["A"]
            b_json = selected_data["b"]
            caso_nombre = selected_data.get("nombre", "Caso sin nombre")
            
            st.write(f"### Resolviendo: {caso_nombre}")
            
            # Determinar si es minimización o maximización
            minimize = json_optimization_type == "Minimización"
            
            # Resolver el problema
            if json_show_iterations:
                solution, z_opt, tableau_history, pivot_history = simplex(
                    c_json, A_json, b_json, minimize=minimize, track_iterations=True
                )
            else:
                solution, z_opt = simplex(
                    c_json, A_json, b_json, minimize=minimize, track_iterations=False
                )
            
            # Mostrar la solución
            st.success("✅ Solución encontrada")
            
            # Mostrar el problema
            st.subheader("Datos del problema")
            st.write("**Vector de coeficientes (c):**", c_json)
            st.write("**Matriz de restricciones (A):**")
            st.dataframe(pd.DataFrame(A_json))
            st.write("**Vector lado derecho (b):**", b_json)
            
            operation = "minimización" if minimize else "maximización"
            st.write(f"**Resultado de {operation}:**")
            st.write("**Solución óptima:**", solution)
            st.write(f"**Valor óptimo {'mínimo' if minimize else 'máximo'} Z:**", z_opt)
            
            # Crear un DataFrame para la solución
            solution_df = pd.DataFrame({
                'Variable': [f'x{i+1}' for i in range(len(solution))],
                'Valor': solution
            })
            solution_df = solution_df.round(4)
            
            # Mostrar la tabla de solución
            st.subheader("Tabla de solución")
            st.dataframe(solution_df)
              # Generar el enlace de descarga para la solución
            st.markdown(get_download_link(solution_df, f"simplex_solucion_{caso_nombre}.csv", 
                                       "Descargar solución (CSV)"), unsafe_allow_html=True)              
            
            # Generar animación Manim
            with st.expander("🎬 Animación del Método Simplex", expanded=True):
                st.warning("**Nota:** La generación de animaciones puede tardar varios minutos y requiere que Manim esté correctamente instalado.")
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    # Guardamos los datos de la solución en session_state
                    if not st.session_state.solved:
                        st.session_state.solved = True
                        st.session_state.solution_data = {
                            'c': c_json,
                            'A': A_json,
                            'b': b_json,
                            'solution': solution,
                            'z_opt': z_opt,
                            'minimize': minimize
                        }
                    
                    # Usar un botón en lugar de checkbox para evitar recarga
                    generate_animation_btn = st.button("Generar animación", 
                                                     key="gen_anim_btn_json", 
                                                     on_click=handle_generate_animation,
                                                     disabled=st.session_state.generating_animation or st.session_state.animation_generated)
                    
                    if st.session_state.animation_generated and st.session_state.video_path:
                        st.success("✅ Animación ya generada")
                with col2:
                    st.markdown("")
                    st.markdown("")
                    check_manim = st.button("✓ Verificar Manim", key="check_manim_json", disabled=st.session_state.generating_animation)
                
                if check_manim:
                    with st.spinner("Verificando instalación de Manim..."):
                        try:
                            cmd = f'"{sys.executable}" -c "import manim; print(f\'Manim version: {{manim.__version__}}\')"'
                            process = subprocess.Popen(
                                cmd, 
                                shell=True, 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE,
                                text=True,
                                encoding="utf-8",
                                errors="replace"
                            )
                            stdout, stderr = process.communicate(timeout=10)
                            
                            if process.returncode == 0:
                                st.success(f"✅ Manim está instalado correctamente. {stdout.strip()}")
                            else:
                                st.error(f"❌ Manim no está instalado correctamente: {stderr}")
                                st.info("Puedes instalar Manim ejecutando: pip install manim")
                        except Exception as e:
                            st.error(f"❌ Error al verificar Manim: {str(e)}")
                
                # Si el botón fue presionado o la animación ya está siendo generada
                if st.session_state.generating_animation and not st.session_state.animation_generated:
                    try:
                        st.info("Generando animación... Este proceso puede tardar varios minutos. **No cambies la página ni interactúes con la app durante la generación.**")
                        
                        # Crear tiempo de inicio para medir duración
                        start_time = time.time()
                        
                        # Usar los datos guardados en session_state
                        data = st.session_state.solution_data
                        video_path = generate_manim_animation(
                            data['c'], data['A'], data['b'], 
                            data['solution'], data['z_opt'], 
                            data['minimize']
                        )
                        
                        # Calcular duración
                        duration = time.time() - start_time
                        
                        if video_path and os.path.exists(video_path):
                            # Actualizar el estado
                            handle_animation_complete(video_path)
                            
                            st.success(f"✅ Animación generada correctamente en {duration:.1f} segundos")
                            
                            # Mostrar video
                            st.video(video_path)
                            
                            # Proporcionar enlace de descarga
                            with open(video_path, "rb") as file:
                                video_bytes = file.read()
                                st.download_button(
                                    label="📥 Descargar animación (MP4)",
                                    data=video_bytes,
                                    file_name=f"simplex_animation_{caso_nombre}.mp4",
                                    mime="video/mp4",
                                    key="download_video_json"
                                )
                        else:
                            st.error("❌ No se pudo generar la animación.")
                            st.session_state.generating_animation = False
                            st.info("Puedes intentar las siguientes soluciones:")
                            st.markdown("""
                            1. Verifica que Manim esté instalado correctamente (botón "Verificar Manim")
                            2. Reinicia la aplicación
                            3. Comprueba que tienes suficiente espacio en disco
                            4. Revisa si hay errores específicos en la sección de salida anterior
                            """)
                    except Exception as e:
                        st.error(f"❌ Error en la generación de la animación: {str(e)}")
                        st.session_state.generating_animation = False
                        import traceback
                        st.code(traceback.format_exc(), language="python")
                
                # Mostrar video si ya fue generado
                elif st.session_state.animation_generated and st.session_state.video_path:
                    if os.path.exists(st.session_state.video_path):
                        st.video(st.session_state.video_path)
                        
                        # Proporcionar enlace de descarga
                        with open(st.session_state.video_path, "rb") as file:
                            video_bytes = file.read()
                            st.download_button(
                                label="📥 Descargar animación (MP4)",
                                data=video_bytes,
                                file_name=f"simplex_animation_{caso_nombre}.mp4",
                                mime="video/mp4",
                                key="download_video_json2"
                            )
            
            # Mostrar las iteraciones si se solicitó
            if json_show_iterations and tableau_history:
                st.subheader("Iteraciones del método Simplex")
                
                # Crear DataFrames para cada tableau
                tableau_dfs = {}
                
                for i, (tableau, pivot) in enumerate(zip(tableau_history, pivot_history)):
                    # Crear etiquetas para columnas
                    col_labels = [f'x{j+1}' for j in range(len(c_json))]
                    col_labels += [f's{j+1}' for j in range(len(b_json))]
                    col_labels += ['b']
                    
                    # Crear etiquetas para filas
                    row_labels = [f'Restricción {j+1}' for j in range(len(b_json))]
                    row_labels += ['Función objetivo']
                    
                    # Convertir el tableau a un DataFrame
                    df = pd.DataFrame(tableau, columns=col_labels, index=row_labels)
                    df = df.round(4)  # Redondear a 4 decimales
                    
                    # Resaltar la celda pivote si no es la iteración inicial
                    if i > 0:
                        row_p, col_p = pivot
                        
                        # Mostrar información del pivote
                        st.write(f"**Iteración {i}** - Elemento pivote: "
                                f"Fila {row_p+1} ('{row_labels[row_p]}'), "
                                f"Columna '{col_labels[col_p]}'")
                    else:
                        st.write("**Tableau inicial**")
                    
                    # Mostrar el tableau
                    st.dataframe(df)
                    
                    # Guardar para exportación
                    tableau_dfs[f'Iteración {i}'] = df.reset_index().rename(columns={'index': 'Fila/Columna'})
                
                # Generar enlaces de descarga para todas las iteraciones
                st.markdown(get_excel_download_link(tableau_dfs, f"simplex_iteraciones_{caso_nombre}.xlsx", 
                                                "Descargar todas las iteraciones (Excel)"), 
                          unsafe_allow_html=True)
        else:
            st.error("❌ Formato JSON incorrecto. Debe contener las claves 'c', 'A' y 'b'.")
            
    except DimensionError as e:
        st.error(f"❌ Error de dimensiones: {e}")
    except NegativeBError as e:
        st.error(f"❌ Error: El vector b tiene valores negativos. {e}")
    except UnboundedError as e:
        st.error(f"❌ Problema no acotado: {e}")
    except SimplexError as e:
        st.error(f"❌ Error general del método Simplex: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")

# Agregar información sobre el formato del problema
with st.expander("ℹ️ Formato del problema"):
    st.markdown("""
    ### Formato del problema de programación lineal
    
    #### Maximización
    Maximizar: Z = c₁x₁ + c₂x₂ + ... + cₙxₙ
    
    Sujeto a:
    - a₁₁x₁ + a₁₂x₂ + ... + a₁ₙxₙ ≤ b₁
    - a₂₁x₁ + a₂₂x₂ + ... + a₂ₙxₙ ≤ b₂
    - ...
    - aₘ₁x₁ + aₘ₂x₂ + ... + aₘₙxₙ ≤ bₘ
    - x₁, x₂, ..., xₙ ≥ 0
    
    #### Minimización
    Minimizar: Z = c₁x₁ + c₂x₂ + ... + cₙxₙ
    
    Sujeto a las mismas restricciones.
    
    ### Ejemplo
    
    Para resolver el problema:
    
    Maximizar: Z = 3x₁ + 2x₂
    
    Sujeto a:
    - 2x₁ + x₂ ≤ 10
    - x₁ + 2x₂ ≤ 8
    - x₁, x₂ ≥ 0
    
    Configure:
    - c = [3, 2]
    - A = [[2, 1], [1, 2]]
    - b = [10, 8]
    """)

with st.expander("📋 Formato del archivo JSON"):
    st.markdown("""
    ### Formato del archivo JSON para cargar casos
    
    El archivo JSON debe contener un arreglo de objetos, donde cada objeto representa un caso de prueba con el siguiente formato:
    
    ```json
    [
        {
            "nombre": "Nombre del caso de prueba",
            "c": [coeficientes de la función objetivo],
            "A": [
                [coeficientes de la primera restricción],
                [coeficientes de la segunda restricción],
                ...
            ],
            "b": [valores del lado derecho de las restricciones]
        },
        {
            "nombre": "Otro caso de prueba",
            ...
        }
    ]
    ```
    
    ### Ejemplo
    
    ```json
    [
        {
            "nombre": "Caso 1 - Solución única",
            "c": [3, 2],
            "A": [
                [1, 1],
                [1, 0],
                [0, 1]
            ],
            "b": [4, 2, 3]
        }
    ]
    ```
    """)
