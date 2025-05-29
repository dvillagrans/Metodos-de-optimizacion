# Métodos de Optimización

Aplicación Flask para resolver problemas de programación lineal usando distintos métodos de optimización y visualizar los resultados mediante animaciones generadas con Manim.

## Características

- Implementación de diferentes métodos de optimización:
  - Método Simplex
  - Método de la Gran M
  - Método de las Dos Fases
- Interfaz web API para resolver problemas
- Generación de animaciones visuales de los problemas y sus soluciones
- Carga y descarga de ejemplos en formato JSON

## Estructura del Proyecto

```
metodos-optimizacion/
│
├── app/
│   ├── __init__.py
│   ├── routes.py                   # Endpoints: resolver, animar, servir archivos
│   ├── solvers/
│   │   ├── __init__.py
│   │   ├── simplex_solver.py       # Método Simplex
│   │   ├── granm_solver.py         # Método Gran M
│   │   └── dosfases_solver.py      # Método de Dos Fases
│   ├── manim_renderer.py           # Genera animación usando cualquier método
│
├── manim_anim/                     # Scripts Manim y problem_data.json
│   ├── basic_simplex_anim.py
│   └── ...
│
├── output/                         # Donde se guardan los .mp4
│   └── videos/
│
├── run.py
├── requirements.txt
└── README.md
```

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/tuusuario/metodos-optimizacion.git
cd metodos-optimizacion
```

2. Crea y activa un entorno virtual:
```bash
# Para Windows
python -m venv venv
venv\Scripts\activate

# Para Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

4. Para generar animaciones, asegúrate de tener las dependencias de Manim:
   - FFmpeg
   - LaTeX (opcional, para fórmulas avanzadas)
   - Cairo

## Ejecución

Para ejecutar la aplicación:

```bash
python run.py
```

La aplicación estará disponible en `http://localhost:5000`

## API Endpoints

- `GET /api/casos` - Obtener todos los ejemplos guardados
- `GET /api/casos/{id}` - Obtener un ejemplo específico
- `POST /api/casos` - Agregar un nuevo ejemplo
- `DELETE /api/casos/{id}` - Eliminar un ejemplo

- `POST /api/resolver/simplex` - Resolver un problema usando el método Simplex
- `POST /api/resolver/granm` - Resolver un problema usando el método Gran M
- `POST /api/resolver/dosfases` - Resolver un problema usando el método de Dos Fases

- `POST /api/animar` - Generar una animación para un problema
- `GET /api/videos/{filename}` - Obtener un video generado

## Formato de Entrada

Para resolver un problema, envía un JSON con la siguiente estructura:

```json
{
  "c": [5, 7],               // Coeficientes de la función objetivo
  "A": [[2, 3], [1, 1], [1, 0]], // Matriz de restricciones
  "b": [12, 5, 3],           // Valores de lado derecho de restricciones
  "minimize": false,         // true para minimizar, false para maximizar
  "eq_constraints": [0],     // Índices de restricciones de igualdad (opcional)
  "track_iterations": true   // Devolver historial de iteraciones (opcional)
}
```

## Ejemplos

En la carpeta `manim_anim` encontrarás un archivo `casos.json` con ejemplos predefinidos que puedes utilizar para probar la aplicación.

## Licencia

Este proyecto está bajo la Licencia MIT.
