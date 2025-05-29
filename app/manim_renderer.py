import json
import os
import subprocess
import sys
import time
import logging
import shutil
import numpy as np
from manim import *

# Configure logger
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_ffmpeg():
    """Check if FFmpeg is available and properly configured."""
    # First check if ffmpeg is in PATH
    if shutil.which("ffmpeg") is not None:
        logger.info("FFmpeg found in PATH")
        return True
    
    # Check common installation paths on Windows
    common_paths = [
        "C:\\ffmpeg\\bin\\ffmpeg.exe",
        "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
        "C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe"
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            logger.info(f"FFmpeg found at: {path}")
            return True
    
    logger.warning("FFmpeg not found in common locations")
    return False

def get_ffmpeg_warning():
    """Get FFmpeg warning message if not available."""
    if not check_ffmpeg():
        return ("FFmpeg not found. Please install FFmpeg to generate video animations. "
                "You can download it from https://ffmpeg.org/download.html")
    return None

def get_ffmpeg_path():
    """Get the path to FFmpeg executable."""
    # First check if ffmpeg is in PATH
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is not None:
        return ffmpeg_path
    
    # Check common installation paths on Windows
    common_paths = [
        "C:\\ffmpeg\\bin\\ffmpeg.exe",
        "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
        "C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe"
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None

def setup_ffmpeg_environment():
    """Setup environment variables to include FFmpeg in PATH."""
    env = os.environ.copy()
    
    # Always add FFmpeg paths to ensure availability
    ffmpeg_paths = [
        "C:\\ffmpeg\\bin",
        "C:\\Program Files\\ffmpeg\\bin",
        "C:\\Program Files (x86)\\ffmpeg\\bin"
    ]
    
    current_path = env.get('PATH', '')
    ffmpeg_added = False
    
    for path in ffmpeg_paths:
        if os.path.exists(path) and path not in current_path:
            env['PATH'] = path + os.pathsep + current_path
            current_path = env['PATH']
            logger.info(f"Added FFmpeg path to environment: {path}")
            ffmpeg_added = True
            break
    
    if not ffmpeg_added:
        # Check if FFmpeg is already in PATH
        if shutil.which("ffmpeg", path=env.get('PATH')) is not None:
            logger.info("FFmpeg already available in PATH")
        else:
            logger.warning("FFmpeg not found - video generation may fail")
    
    return env

# Try to import static visualization as fallback
try:
    from static_visualization import create_static_optimization_visualization
    STATIC_FALLBACK_AVAILABLE = True
except ImportError:
    STATIC_FALLBACK_AVAILABLE = False
    logger.warning("Static visualization fallback not available")

# Import our advanced animation classes
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'manim_anim'))
try:
    from advanced_simplex_anim import AdvancedSimplexAnim, TableauVisualization
except ImportError as e:
    logger.warning(f"Could not import advanced animation classes: {e}")
    AdvancedSimplexAnim = None
    TableauVisualization = None

def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj

def generate_manim_animation(c, A, b, solution, z_opt, minimize=False, method="simplex", 
                           tableau_history=None, pivot_history=None, iterations=None):
    """
    Generates a Manim animation for the optimization problem.
    
    Args:
        c (list): Coefficients of the objective function.
        A (list of lists): Matrix of constraint coefficients.
        b (list): Right-hand side values of constraints.
        solution (list): The optimal solution.
        z_opt (float): The optimal value.
        minimize (bool): If True, problem is minimization; otherwise, maximization.
        method (str): The solver method used ("simplex", "granm", or "dosfases").
        tableau_history (list): List of tableau states for visualization.
        pivot_history (list): List of pivot positions for visualization.
        iterations (list): List of iteration data for backwards compatibility.
    
    Returns:
        str: Path to the generated video file, or None if generation failed.
    """
    try:
        # Check FFmpeg availability
        ffmpeg_warning = get_ffmpeg_warning()
        if ffmpeg_warning:
            logger.warning(ffmpeg_warning)
            # Continue anyway, but warn the user
        
        # Create necessary directories if they don't exist
        animation_dir = os.path.join(os.path.dirname(__file__), '..', 'manim_anim')
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'videos')
        
        os.makedirs(animation_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare data for animation
        data = {
            'c': c,
            'A': A,
            'b': b,
            'solution': solution,
            'z_opt': z_opt,
            'minimize': minimize,
            'method': method,
            'tableau_history': tableau_history or iterations or [],
            'pivot_history': pivot_history or []
        }
        
        # Clean data for JSON serialization
        clean_data = convert_numpy_types(data)
        
        # Determine animation type based on problem characteristics
        num_variables = len(c) if c else 0
        
        # For Gran M and Dos Fases methods, always use tableau visualization
        if method in ["granm", "dosfases"]:
            return generate_granm_dosfases_animation(clean_data, animation_dir, output_dir)
        
        # For 2D problems, use geometric visualization
        elif num_variables == 2 and method == "simplex":
            return generate_simplex_2d_animation(clean_data, animation_dir, output_dir)
        
        # For 3D problems, use 3D geometric visualization
        elif num_variables == 3 and method == "simplex":
            return generate_simplex_3d_animation(clean_data, animation_dir, output_dir)
        
        # For higher dimensions or if tableau data is available, use advanced visualization
        elif method == "simplex" and (tableau_history or iterations) and AdvancedSimplexAnim:
            return generate_advanced_simplex_animation(clean_data, animation_dir, output_dir)
        
        else:
            # Fallback to basic animation
            result = generate_basic_animation(clean_data, animation_dir, output_dir)
            
            # If Manim fails and static fallback is available, use it
            if result is None and STATIC_FALLBACK_AVAILABLE:
                logger.info("Manim failed, falling back to static visualization")
                return create_static_optimization_visualization(
                    c=c, A=A, b=b, solution=solution, z_opt=z_opt,
                    minimize=minimize, method=method, output_dir=output_dir
                )
            
            return result
            
    except Exception as e:
        logger.error(f"Error generating animation: {e}")
        return None

def generate_advanced_simplex_animation(data, animation_dir, output_dir):
    """Generate advanced Simplex animation with tableau visualization."""
    try:
        # Convert numpy arrays to lists if necessary
        def convert_to_native_types(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, list):
                return [convert_to_native_types(item) for item in obj]
            elif isinstance(obj, np.number):
                return float(obj)
            return obj

        # Convert data to native Python types
        converted_data = {
            "c": convert_to_native_types(data['c']),
            "A": convert_to_native_types(data['A']),
            "b": convert_to_native_types(data['b']),
            "solution": convert_to_native_types(data['solution']),
            "z_opt": float(data['z_opt']) if not isinstance(data['z_opt'], (str, bool)) else data['z_opt'],
            "minimize": data['minimize'],
            "method": data['method'],
            "iterations": convert_to_native_types(data.get('iterations', [])),
            "tableau_history": convert_to_native_types(data.get('tableau_history', [])),
            "pivot_history": convert_to_native_types(data.get('pivot_history', []))
        }
        
        # Save data for the animation
        data_file = os.path.join(animation_dir, 'problem_data.json')
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(converted_data, f, ensure_ascii=True, indent=2)
          # Python executable path
        python_exe = sys.executable
        
        # Command to run advanced animation  
        cmd = [
            python_exe,
            "-m", "manim",
            "advanced_simplex_anim.py",
            "AdvancedSimplexAnim",
            "-qm",  # Medium quality
            "--format", "mp4",
            f"--media_dir={output_dir}",
            "--disable_caching"
        ]
        
        logger.info(f"Running advanced Manim command: {cmd}")
        
        # Execute Manim with better error handling
        try:
            # Setup environment with FFmpeg
            env = setup_ffmpeg_environment()
            
            process = subprocess.Popen(
                cmd,
                cwd=animation_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env  # Use modified environment with FFmpeg path
            )
            
            stdout, stderr = process.communicate(timeout=180)  # 3 minutes timeout
            
            logger.info(f"Advanced Manim stdout: {stdout[:500]}...")
            if stderr and "RuntimeWarning" not in stderr:
                logger.warning(f"Advanced Manim stderr: {stderr[:500]}...")
                
        except subprocess.TimeoutExpired:
            logger.error("Manim process timed out")
            process.kill()
            return generate_basic_animation(data, animation_dir, output_dir)
        except Exception as e:
            logger.error(f"Error running Manim process: {e}")
            return generate_basic_animation(data, animation_dir, output_dir)
            return generate_basic_animation(data, animation_dir, output_dir)
        
        if process.returncode == 0:
            # Look for the generated video with improved search
            import glob
            import time
            
            # Wait a moment for file system to update
            time.sleep(1)
            
            # Try multiple patterns to find generated files
            search_patterns = [
                os.path.join(output_dir, "**", "*.mp4"),
                os.path.join(output_dir, "videos", "**", "*.mp4"),
                os.path.join(animation_dir, "media", "**", "*.mp4"),
                os.path.join(animation_dir, "**", "*.mp4")
            ]
            
            video_files = []
            for pattern in search_patterns:
                found_files = glob.glob(pattern, recursive=True)
                video_files.extend(found_files)
            
            # Remove duplicates and sort by modification time
            video_files = list(set(video_files))
            
            if video_files:
                video_files.sort(key=os.path.getmtime, reverse=True)
                latest_video = video_files[0]
                logger.info(f"Generated advanced video: {latest_video}")
                return latest_video
        
        logger.warning("Advanced animation failed, falling back to basic animation")
        return generate_basic_animation(data, animation_dir, output_dir)
        
    except Exception as e:
        logger.error(f"Error in advanced animation: {e}")
        return generate_basic_animation(data, animation_dir, output_dir)

def generate_basic_animation(data, animation_dir, output_dir):
    """Generate basic animation for any optimization method."""
    try:
        # Convert numpy arrays to lists if necessary
        def convert_to_native_types(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, list):
                return [convert_to_native_types(item) for item in obj]
            elif isinstance(obj, np.number):
                return float(obj)
            return obj

        # Create problem data dict
        problem_data = {
            "c": convert_to_native_types(data['c']),
            "A": convert_to_native_types(data['A']),
            "b": convert_to_native_types(data['b']),
            "solution": convert_to_native_types(data['solution']),
            "z_opt": float(data['z_opt']) if not isinstance(data['z_opt'], (str, bool)) else data['z_opt'],
            "minimize": data['minimize'],
            "method": data['method']
        }

        # Save data to a file
        data_file = os.path.join(animation_dir, "problem_data.json")
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(problem_data, f, ensure_ascii=True, indent=2)

        # Determine which script to use based on the method
        script_mapping = {
            "simplex": "basic_simplex_anim.py",
            "granm": "basic_simplex_anim.py",  # Use same script for now
            "dosfases": "basic_simplex_anim.py",  # Use same script for now
            "default": "basic_simplex_anim.py"
        }

        script_to_use = script_mapping.get(data['method'], script_mapping["default"])

        # Check if script exists, if not create it
        script_path = os.path.join(animation_dir, script_to_use)
        if not os.path.exists(script_path):
            create_default_manim_script(script_path)
            logger.info(f"Created default Manim script at {script_path}")        # Get class name from script
        class_name = "BasicSimplexAnim"
        
        # Python executable path
        python_exe = sys.executable
        
        # Command to run Manim
        cmd = [
            python_exe,
            "-m", "manim",
            script_to_use,
            class_name,
            "-qm",  # Medium quality
            "--format", "mp4",
            f"--media_dir={output_dir}",
            "--disable_caching"
        ]
        
        logger.info(f"Running basic Manim command: {cmd}")        
        
        # Execute Manim as a subprocess with better error handling
        try:
            # Check FFmpeg availability before proceeding
            ffmpeg_available = check_ffmpeg()
            if not ffmpeg_available:
                logger.warning("FFmpeg not available - attempting to install or configure")
            
            # Setup environment with FFmpeg
            env = setup_ffmpeg_environment()
            
            process = subprocess.Popen(
                cmd,
                cwd=animation_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env  # Use modified environment with FFmpeg path
            )

            # Capture output
            stdout, stderr = process.communicate(timeout=180)  # 3 minutes timeout

            # Log output for debugging (filter out common warnings)
            logger.info(f"Basic Manim stdout: {stdout[:500]}...")
            if stderr and "RuntimeWarning" not in stderr and "ffmpeg" not in stderr.lower():
                logger.warning(f"Basic Manim stderr: {stderr[:500]}...")

        except subprocess.TimeoutExpired:
            logger.error("Basic Manim process timed out")
            process.kill()
            return None
        except Exception as e:
            logger.error(f"Error running basic Manim process: {e}")
            return None            # Check if process was successful OR if it completed with warnings (exit code 1)
        # but still generated files successfully
        if process.returncode == 0 or (process.returncode == 1 and "File ready at" in stdout):
            # Look for video or image files with improved search
            import glob
            import time
            
            # Wait a moment for file system to update
            time.sleep(1)
            
            # Try multiple patterns to find generated files
            search_patterns = [
                os.path.join(output_dir, "**", "*.mp4"),
                os.path.join(output_dir, "videos", "**", "*.mp4"),
                os.path.join(animation_dir, "media", "**", "*.mp4"),
                os.path.join(animation_dir, "**", "*.mp4")
            ]
            
            video_files = []
            for pattern in search_patterns:
                found_files = glob.glob(pattern, recursive=True)
                video_files.extend(found_files)
            
            # Remove duplicates and sort by modification time
            video_files = list(set(video_files))
            
            if video_files:
                video_files.sort(key=os.path.getmtime, reverse=True)
                latest_video = video_files[0]
                logger.info(f"Generated basic video: {latest_video}")
                return latest_video
            else:
                # Look for PNG files if no video was found
                search_patterns_png = [
                    os.path.join(output_dir, "**", "*.png"),
                    os.path.join(output_dir, "images", "**", "*.png"),
                    os.path.join(animation_dir, "media", "**", "*.png"),
                    os.path.join(animation_dir, "**", "*.png")                ]
                
                png_files = []
                for pattern in search_patterns_png:
                    found_files = glob.glob(pattern, recursive=True)
                    png_files.extend(found_files)
                
                png_files = list(set(png_files))
                
                if png_files:
                    png_files.sort(key=os.path.getmtime, reverse=True)
                    latest_png = png_files[0]
                    logger.info(f"Generated basic image: {latest_png}")
                    return latest_png

            logger.warning("Manim ran successfully but no output file was found")
            return None
        else:
            if process.returncode == 1 and "File ready at" in stdout:
                logger.warning(f"Manim completed with warnings (exit code {process.returncode}) but file generation might have succeeded")
            else:
                logger.error(f"Manim exited with error code {process.returncode}")
            return None

    except Exception as e:
        logger.error(f"Error in basic animation generation: {e}")
        return None

def create_default_manim_script(filepath):
    """Create a simple default Manim script if none exists."""
    
    script_content = '''
from manim import *
import json
import os
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
        
        # Set up the scene
        method_names = {
            "simplex": "Método Simplex",
            "granm": "Método Gran M",
            "dosfases": "Método Dos Fases"
        }
        
        title = Text(method_names.get(method, "Método Simplex"), font_size=48)
        title.to_edge(UP)
        self.play(Write(title))
        
        # Problem description
        problem_type = "Minimización" if minimize else "Maximización"
        prob_desc = Text(f"Problema de {problem_type}", font_size=32)
        prob_desc.next_to(title, DOWN)
        self.play(Write(prob_desc))
          # Objective function
        obj_text = ""
        if len(c) > 0:
            obj_text = f"Z = {float(c[0]):.2f}x₁"
            for i in range(1, len(c)):
                c_val = float(c[i])  # Convert to Python scalar
                if c_val >= 0:
                    obj_text += f" + {c_val:.2f}x₍{i+1}₎"
                else:
                    obj_text += f" - {abs(c_val):.2f}x₍{i+1}₎"
        
        obj_func = Text(obj_text, font_size=28)
        obj_func.next_to(prob_desc, DOWN, buff=0.5)
        self.play(Write(obj_func))
        self.wait(1)
        
        # Constraints
        constraints_title = Text("Sujeto a:", font_size=28)
        constraints_title.next_to(obj_func, DOWN, buff=0.5)
        constraints_title.align_to(obj_func, LEFT)
        self.play(Write(constraints_title))
          # Display each constraint
        constraints_group = VGroup()
        for i in range(min(len(b), 5)):  # Limit to 5 constraints for display
            constraint_text = ""
            if len(A[i]) > 0:
                constraint_text = f"{float(A[i][0]):.2f}x₁"
                for j in range(1, min(len(A[i]), 4)):  # Limit variables for display
                    a_val = float(A[i][j])  # Convert to Python scalar
                    if a_val >= 0:
                        constraint_text += f" + {a_val:.2f}x₍{j+1}₎"
                    else:
                        constraint_text += f" - {abs(a_val):.2f}x₍{j+1}₎"
                constraint_text += f" ≤ {float(b[i]):.2f}"
            
            constraint = Text(constraint_text, font_size=22)
            if i == 0:
                constraint.next_to(constraints_title, DOWN, buff=0.3)
                constraint.align_to(constraints_title, LEFT).shift(RIGHT*0.5)
            else:
                constraint.next_to(constraints_group[-1], DOWN, buff=0.2)
                constraint.align_to(constraints_group[-1], LEFT)
            
            constraints_group.add(constraint)
            self.play(Write(constraint))
        
        self.wait(1)
        
        # Solution
        solution_title = Text("Solución Óptima:", font_size=32, color=GREEN)
        solution_title.next_to(constraints_group, DOWN, buff=1)
        self.play(Write(solution_title))
        
        # Display solution values
        sol_values_group = VGroup()
        max_vars_to_show = min(len(solution), 4)  # Show max 4 variables
        for i in range(max_vars_to_show):
            sol_text = f"x₍{i+1}₎ = {solution[i]:.4f}"
            sol_value = Text(sol_text, font_size=26)
            
            if i == 0:
                sol_value.next_to(solution_title, DOWN, buff=0.5)
            else:
                sol_value.next_to(sol_values_group[-1], DOWN, buff=0.3)
            
            sol_values_group.add(sol_value)
            self.play(Write(sol_value))
        
        # Optimal value
        opt_text = f"Valor óptimo: Z = {z_opt:.4f}"
        opt_value = Text(opt_text, font_size=30, color=YELLOW)
        opt_value.next_to(sol_values_group, DOWN, buff=0.8)
        self.play(Write(opt_value))
        
        # Celebration effect
        confetti = VGroup()
        for _ in range(20):
            dot = Dot(
                point=np.array([
                    np.random.uniform(-7, 7),
                    np.random.uniform(3, 4),
                    0
                ]),
                color=random.choice([RED, BLUE, GREEN, YELLOW, PURPLE])
            )
            confetti.add(dot)
        
        self.play(FadeIn(confetti))
        self.play(
            confetti.animate.shift(DOWN * 8),
            rate_func=rate_functions.ease_in_quad,
            run_time=2
        )
        
        # Final wait
        self.wait(2)
'''
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(script_content)

def run_manim_command(command):
    """Execute Manim command and capture both stdout and stderr"""
    try:
        logger.info(f"Running Manim command: {command}")
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60  # Add timeout to prevent hanging
        )
        
        # Log stdout
        if result.stdout:
            logger.info(f"Manim stdout: {result.stdout}")
        
        # Log stderr
        if result.stderr:
            logger.error(f"Manim stderr: {result.stderr}")
        
        # Check return code
        if result.returncode != 0:
            logger.error(f"Manim exited with error code {result.returncode}")
            return False, result.stderr or "Unknown error occurred"
        
        return True, result.stdout
        
    except subprocess.TimeoutExpired:
        logger.error("Manim command timed out")
        return False, "Command timed out after 60 seconds"
    except Exception as e:
        logger.error(f"Error running Manim command: {e}")
        return False, str(e)

def generate_simplex_2d_animation(data, animation_dir, output_dir):
    """Generate 2D Simplex animation with geometric visualization."""
    try:
        # Convert and save data
        converted_data = convert_numpy_types(data)
        data_file = os.path.join(animation_dir, 'problem_data.json')
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(converted_data, f, ensure_ascii=True, indent=2)
        
        # Python executable path
        python_exe = sys.executable        # Command to run 2D animation
        cmd = [
            python_exe,
            "-m", "manim",
            "simplex_2d_anim.py",
            "Simplex2DAnim",
            "-qm",  # Medium quality
            "--format", "mp4",
            f"--media_dir={output_dir}",
            "--disable_caching"
        ]
        
        logger.info(f"Running 2D Simplex animation: {cmd}")
        
        # Execute Manim
        env = setup_ffmpeg_environment()
        process = subprocess.Popen(
            cmd,
            cwd=animation_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env
        )
        
        stdout, stderr = process.communicate(timeout=180)
        
        if process.returncode == 0:
            # Look for generated video
            video_path = find_generated_video(output_dir, "Simplex2DAnim")
            if video_path:
                logger.info(f"2D animation generated successfully: {video_path}")
                return video_path
        
        logger.warning("2D animation failed, falling back to basic animation")
        return generate_basic_animation(data, animation_dir, output_dir)
        
    except Exception as e:
        logger.error(f"Error in 2D animation: {e}")
        return generate_basic_animation(data, animation_dir, output_dir)

def generate_simplex_3d_animation(data, animation_dir, output_dir):
    """Generate 3D Simplex animation with geometric visualization."""
    try:
        # Convert and save data
        converted_data = convert_numpy_types(data)
        data_file = os.path.join(animation_dir, 'problem_data.json')
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(converted_data, f, ensure_ascii=True, indent=2)
        
        # Python executable path
        python_exe = sys.executable        # Command to run 3D animation
        cmd = [
            python_exe,
            "-m", "manim",
            "simplex_3d_anim.py",
            "Simplex3DAnim",
            "-qm",  # Medium quality
            "--format", "mp4",
            f"--media_dir={output_dir}",
            "--disable_caching"
        ]
        
        logger.info(f"Running 3D Simplex animation: {cmd}")
        
        # Execute Manim
        env = setup_ffmpeg_environment()
        process = subprocess.Popen(
            cmd,
            cwd=animation_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env
        )
        
        stdout, stderr = process.communicate(timeout=180)
        
        if process.returncode == 0:
            # Look for generated video
            video_path = find_generated_video(output_dir, "Simplex3DAnim")
            if video_path:
                logger.info(f"3D animation generated successfully: {video_path}")
                return video_path
        
        logger.warning("3D animation failed, falling back to basic animation")
        return generate_basic_animation(data, animation_dir, output_dir)
        
    except Exception as e:
        logger.error(f"Error in 3D animation: {e}")
        return generate_basic_animation(data, animation_dir, output_dir)

def generate_granm_dosfases_animation(data, animation_dir, output_dir):
    """Generate Gran M or Dos Fases animation with tableau visualization."""
    try:
        # Convert and save data
        converted_data = convert_numpy_types(data)
        data_file = os.path.join(animation_dir, 'problem_data.json')
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(converted_data, f, ensure_ascii=True, indent=2)
        
        # Python executable path
        python_exe = sys.executable        # Command to run Gran M/Dos Fases animation
        cmd = [
            python_exe,
            "-m", "manim",
            "granm_dosfases_anim.py",
            "GranMDosFasesAnim",
            "-qm",  # Medium quality
            "--format", "mp4",
            f"--media_dir={output_dir}",
            "--disable_caching"
        ]
        
        logger.info(f"Running Gran M/Dos Fases animation: {cmd}")
        
        # Execute Manim
        env = setup_ffmpeg_environment()
        process = subprocess.Popen(
            cmd,
            cwd=animation_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env
        )
        
        stdout, stderr = process.communicate(timeout=180)
        
        if process.returncode == 0:
            # Look for generated video
            video_path = find_generated_video(output_dir, "GranMDosFasesAnim")
            if video_path:
                logger.info(f"Gran M/Dos Fases animation generated successfully: {video_path}")
                return video_path
        
        logger.warning("Gran M/Dos Fases animation failed, falling back to basic animation")
        return generate_basic_animation(data, animation_dir, output_dir)
        
    except Exception as e:
        logger.error(f"Error in Gran M/Dos Fases animation: {e}")
        return generate_basic_animation(data, animation_dir, output_dir)

def find_generated_video(output_dir, scene_name):
    """Helper function to find generated video files."""
    import glob
    import time
    
    # Wait for file system to update
    time.sleep(2)
    
    # Try multiple patterns to find generated files
    search_patterns = [
        f"{output_dir}/**/{scene_name}*.mp4",
        f"{output_dir}/**/videos/**/{scene_name}*.mp4",
        f"{output_dir}/videos/**/{scene_name}*.mp4",
        f"{output_dir}/**/*{scene_name}*.mp4",
        f"{output_dir}/**/720p30/{scene_name}*.mp4",  # Common manim output folder
        f"{output_dir}/**/1080p60/{scene_name}*.mp4",  # High quality output
        f"{output_dir}/**/480p15/{scene_name}*.mp4",   # Low quality output
        f"{output_dir}/videos/**/720p30/{scene_name}*.mp4",
        f"{output_dir}/videos/**/1080p60/{scene_name}*.mp4",
        f"{output_dir}/videos/**/480p15/{scene_name}*.mp4"
    ]
    
    all_found_files = []
    for pattern in search_patterns:
        files = glob.glob(pattern, recursive=True)
        all_found_files.extend(files)
    
    if all_found_files:
        # Remove duplicates and return the most recent file
        unique_files = list(set(all_found_files))
        latest_file = max(unique_files, key=os.path.getctime)
        logger.info(f"Found video file: {latest_file}")
        return latest_file
    
    # Also look for GIF files as fallback
    gif_patterns = [
        f"{output_dir}/**/{scene_name}*.gif",
        f"{output_dir}/**/images/**/{scene_name}*.gif"
    ]
    
    for pattern in gif_patterns:
        files = glob.glob(pattern, recursive=True)
        if files:
            latest_file = max(files, key=os.path.getctime)
            logger.info(f"Found GIF file: {latest_file}")
            return latest_file
    
    logger.warning(f"No video files found for scene {scene_name} in {output_dir}")
    return None