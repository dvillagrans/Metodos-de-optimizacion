const examples = {
    simplex: [
        {
            name: "Ejercicio 3 - Simplex",
            c: "3,5",
            A: "2,3\n4,1",
            b: "8,7",
            minimize: false,
            description: "Maximizar: 3x₁ + 5x₂ con restricciones ≤",
            expected_solution: {
                Z: 13.33,
                variables: [1, "8/3"]
            }
        },
        {
            name: "Ejercicio 6 (modificado) - Simplex",
            c: "2,2,4",
            A: "2,1,1\n-3,-4,-2",
            b: "2,-8",
            minimize: false,
            description: "Versión modificada con restricciones ≤",
            expected_solution: {
                Z: 4,
                variables: [0, 2, 0]
            }
        },
        {
            name: "Ejercicio 9 - Simplex",
            c: "3,9",
            A: "1,4\n1,2",
            b: "8,4",
            minimize: false,
            description: "Maximizar con solución degenerada",
            expected_solution: {
                Z: 18,
                variables: [0, 2]
            }
        },
        {
            name: "Ejercicio 10 - Simplex",
            c: "3,2",
            A: "4,-1\n4,3\n4,1",
            b: "8,12,8",
            minimize: false,
            description: "Maximizar con 3 restricciones ≤",
            expected_solution: {
                Z: 8.5,
                variables: [1.5, 2]
            }
        },
        {
            name: "Ejercicio 11 - Simplex",
            c: "2,4",
            A: "1,2\n1,1",
            b: "5,4",
            minimize: false,
            description: "Maximizar: 2x₁ + 4x₂",
            expected_solution: {
                Z: 10,
                variables: [0, 2.5]
            }
        }
    ],
    granm: [
        {
            name: "Ejercicio 1 - Gran M",
            c: "1,2,3",
            A: "1,1,0\n1,1,1\n1,0,1\n1,0,1",
            b: "2,3,4,5",
            ge_constraints: "0,2",
            minimize: true,
            description: "Minimizar con mezcla de ≥ y ≤",
            expected_solution: {
                Z: 6,
                variables: [3, 0, 1]
            }
        },
        {
            name: "Ejercicio 2 - Gran M",
            c: "4,1",
            A: "3,1\n4,3\n1,2",
            b: "3,6,4",
            eq_constraints: "0",
            ge_constraints: "1",
            minimize: true,
            description: "Minimizar con =, ≥, ≤",
            expected_solution: {
                Z: "3.4 - 3.6",
                variables: ["0.4 - 0.6", "1.8 - 1.2"]
            }
        },
        {
            name: "Ejercicio 4 - Gran M",
            c: "3,2,3,0",
            A: "1,4,1,0\n2,1,0,1",
            b: "7,10",
            ge_constraints: "0,1",
            minimize: true,
            description: "Minimizar con solo ≥",
            expected_solution: {
                Z: 35.5,
                variables: [0, 11.75, 6, 8.25]
            }
        },
        {
            name: "Ejercicio 5 - Gran M",
            c: "1,5,3",
            A: "1,2,1\n2,-1,0",
            b: "3,4",
            eq_constraints: "0,1",
            minimize: false,
            description: "Maximizar con igualdades",
            expected_solution: {
                Z: 5,
                variables: [2, 0, 1]
            }
        },
        {
            name: "Ejercicio 7 - Gran M",
            c: "2,5",
            A: "3,2\n2,1",
            b: "6,2",
            ge_constraints: "0",
            minimize: false,
            description: "No factible",
            expected_solution: null
        },
        {
            name: "Ejercicio 12 - Gran M",
            c: "2,1",
            A: "1,-1\n2,0",
            b: "10,40",
            ge_constraints: "1",
            minimize: false,
            description: "No acotado",
            expected_solution: null
        },
        {
            name: "Ejercicio 13 - Gran M",
            c: "3,2",
            A: "2,1\n3,4",
            b: "2,12",
            ge_constraints: "1",
            minimize: false,
            description: "No factible",
            expected_solution: null
        },
        {
            name: "Ejercicio 14 - Gran M",
            c: "5,12,4",
            A: "1,2,1\n2,-1,3",
            b: "10,8",
            eq_constraints: "1",
            minimize: false,
            description: "Maximizar con igualdad",
            expected_solution: {
                Z: 54.8,
                variables: [5.20, 2.40, 0]
            }
        },
        {
            name: "Ejercicio 15 - Gran M",
            c: "5,6,3",
            A: "5,5,3\n1,1,-1\n7,6,-3\n5,5,5\n2,4,-15\n12,10,0\n0,1,-10",
            b: "50,20,30,36,10,90,20",
            ge_constraints: "0,1,2,3,4,5,6",
            minimize: true,
            description: "Minimizar con muchas ≥",
            expected_solution: {
                Z: 120,
                variables: [0, 0, 0]
            }
        }
    ],
    dosfases: [
        // Puedes clonar los ejercicios de granm si se usa Dos Fases como alternativa
    ]
};

// Función genérica para mostrar la solución esperada
function showExpectedSolutionGeneric(example) {
    const container = document.getElementById('expected-solution-container');
    const content = document.getElementById('expected-solution-content');

    // Solo proceder si existen los contenedores en el DOM
    if (!container || !content) {
        return;
    }

    if (example.expected_solution) {
        const solution = example.expected_solution;
        let solutionHtml = '<div class="row">';

        // Mostrar valor óptimo
        solutionHtml += `
            <div class="col-md-6">
                <strong>Valor Óptimo (Z*):</strong> 
                <span class="badge bg-success">${solution.Z}</span>
            </div>
        `;

        // Mostrar variables
        if (solution.variables && solution.variables.length > 0) {
            solutionHtml += `
                <div class="col-md-6">
                    <strong>Variables:</strong><br>
            `;

            solution.variables.forEach((value, index) => {
                const variableName = `x${index + 1}`;
                solutionHtml += `
                    <span class="badge bg-primary me-1">
                        ${variableName} = ${value}
                    </span>
                `;
            });

            solutionHtml += '</div>';
        }

        solutionHtml += '</div>';

        content.innerHTML = solutionHtml;
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
    }
}

// Función para cargar ejemplo en el formulario
function loadExample(method, exampleIndex) {
    // Para simplex, usar la función específica del formulario dinámico si existe
    if (method === 'simplex' && typeof window.loadSimplexExample === 'function') {
        window.loadSimplexExample(method, exampleIndex);
        return;
    }

    const example = examples[method][exampleIndex];

    if (!example) {
        console.error('Ejemplo no encontrado');
        return;
    }

    // Llenar campos comunes
    document.getElementById('c').value = example.c || '';
    document.getElementById('A').value = example.A || '';
    document.getElementById('b').value = example.b || '';

    // Manejar checkbox de minimizar
    const minimizeCheckbox = document.getElementById('minimize');
    if (minimizeCheckbox) {
        minimizeCheckbox.checked = example.minimize || false;
    }

    // Manejar campo de restricciones de igualdad (para Gran M y Dos Fases)
    const eqConstraintsField = document.getElementById('eq_constraints');
    if (eqConstraintsField) {
        eqConstraintsField.value = example.eq_constraints || '';
    }

    // Manejar campo de restricciones >= (para Gran M y Dos Fases)
    const geConstraintsField = document.getElementById('ge_constraints');
    if (geConstraintsField) {
        geConstraintsField.value = example.ge_constraints || '';
    }

    // Manejar campo M específico para Gran M
    const mField = document.getElementById('M');
    if (mField && method === 'granm') {
        mField.value = example.M || 1000;
    }    // Limpiar campos de seguimiento de iteraciones si existe
    const trackIterationsCheckbox = document.getElementById('track_iterations');
    if (trackIterationsCheckbox) {
        trackIterationsCheckbox.checked = example.track_iterations || false;
    }

    // Mostrar solución esperada si existe y hay un contenedor para ello
    showExpectedSolutionGeneric(example);

    // Mostrar notificación
    showNotification(`Ejemplo cargado: ${example.name}`, 'success');
}

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Agregar al DOM
    document.body.appendChild(notification);

    // Auto-remover después de 3 segundos
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

// Función para crear botones de ejemplo
function createExampleButtons(method) {
    const methodExamples = examples[method];
    if (!methodExamples) return '';

    let buttonsHtml = '<div class="d-flex flex-wrap gap-2 mb-3">';

    methodExamples.forEach((example, index) => {
        buttonsHtml += `
            <button type="button" 
                    class="btn btn-outline-secondary btn-sm" 
                    onclick="loadExample('${method}', ${index})"
                    title="${example.description}">
                <i class="fas fa-lightbulb me-1"></i>${example.name}
            </button>
        `;
    });

    buttonsHtml += '</div>';
    return buttonsHtml;
}

// Función para limpiar formulario
function clearForm() {
    const form = document.querySelector('form[method="POST"]');
    if (!form) {
        console.error('No se encontró el formulario');
        return;
    }

    // Limpiar campos de texto y textarea
    const textInputs = form.querySelectorAll('input[type="text"], input[type="number"], textarea');
    textInputs.forEach(input => {
        input.value = '';
    });

    // Limpiar checkboxes
    const checkboxes = form.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });

    // Restablecer valores por defecto específicos
    const mField = document.getElementById('M');
    if (mField) {
        mField.value = '1000';
    }

    showNotification('Formulario limpiado', 'info');
}

// Funciones para persistencia de datos en localStorage
function saveFormData(method) {
    const formData = {};
    const form = document.querySelector('form[method="POST"]');

    if (form) {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            if (input.type === 'checkbox') {
                formData[input.name] = input.checked;
            } else {
                formData[input.name] = input.value;
            }
        });

        localStorage.setItem(`${method}_form_data`, JSON.stringify(formData));
    }
}

function loadFormData(method) {
    const savedData = localStorage.getItem(`${method}_form_data`);
    if (savedData) {
        try {
            const formData = JSON.parse(savedData);
            const form = document.querySelector('form[method="POST"]');

            if (form) {
                Object.keys(formData).forEach(key => {
                    const input = form.querySelector(`[name="${key}"]`);
                    if (input) {
                        if (input.type === 'checkbox') {
                            input.checked = formData[key];
                        } else {
                            input.value = formData[key];
                        }
                    }
                });
            }
        } catch (e) {
            console.error('Error al cargar datos guardados:', e);
        }
    }
}

function clearFormData(method) {
    localStorage.removeItem(`${method}_form_data`);
    // También limpiar el formulario actual
    const form = document.querySelector('form[method="POST"]');
    if (form) {
        form.reset();
    }
}

// Auto-guardar datos del formulario mientras el usuario escribe
function setupAutoSave(method) {
    const form = document.querySelector('form[method="POST"]');
    if (form) {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                setTimeout(() => saveFormData(method), 500); // Debounce de 500ms
            });
            input.addEventListener('change', () => {
                saveFormData(method);
            });
        });
    }
}

// Funciones específicas para cada método
function setupMethodFeatures(method) {
    // Auto-guardar
    setupAutoSave(method);

    // Agregar botón para limpiar datos
    const form = document.querySelector('form[method="POST"]');
    if (form) {
        const clearButton = document.createElement('button');
        clearButton.type = 'button';
        clearButton.className = 'btn btn-outline-secondary btn-sm ms-2';
        clearButton.innerHTML = '<i class="fas fa-trash me-1"></i>Limpiar';
        clearButton.onclick = () => {
            if (confirm('¿Estás seguro de que quieres limpiar todos los datos?')) {
                clearFormData(method);
            }
        };

        // Insertar el botón después del último botón del formulario
        const lastButtonContainer = form.querySelector('.row:last-child .col-md-6:last-child');
        if (lastButtonContainer) {
            const buttonWrapper = document.createElement('div');
            buttonWrapper.className = 'mt-2';
            buttonWrapper.appendChild(clearButton);
            lastButtonContainer.appendChild(buttonWrapper);
        }
    }

    // Mejorar feedback del botón de descarga JSON
    const downloadButton = document.querySelector('.btn-download-json');
    if (downloadButton) {
        downloadButton.addEventListener('click', function () {
            const originalContent = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Descargando...';
            this.classList.add('downloading');
            this.disabled = true;

            // Re-habilitar después de un momento (en caso de error)
            setTimeout(() => {
                this.innerHTML = originalContent;
                this.classList.remove('downloading');
                this.disabled = false;
            }, 3000);
        });
    }

    // Verificar si hay datos en los campos y agregar indicador visual
    if (form) {
        const inputs = form.querySelectorAll('input[type="text"], input[type="checkbox"], textarea');
        inputs.forEach(input => {
            if (input.type === 'checkbox' ? input.checked : input.value.trim() !== '') {
                input.classList.add('has-saved-data');
            }
        });

        // Mostrar mensaje si hay datos guardados
        const hasData = Array.from(inputs).some(input =>
            input.type === 'checkbox' ? input.checked : input.value.trim() !== ''
        );
        if (hasData) {
            showDataPreservedMessage();
        }
    }
}

// Funciones específicas para el método dos fases (mantener compatibilidad)
function setupDosFasesFeatures() {
    setupMethodFeatures('dosfases');
}

// Función para mostrar mensaje de datos preservados
function showDataPreservedMessage() {
    const form = document.querySelector('form[method="POST"]');
    if (form) {
        const message = document.createElement('div');
        message.className = 'alert alert-info alert-dismissible fade show mt-2';
        message.innerHTML = `
            <i class="fas fa-info-circle me-2"></i>
            Los datos de tu formulario anterior se han mantenido.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insertar el mensaje antes del formulario
        form.parentNode.insertBefore(message, form);

        // Auto-ocultar después de 5 segundos
        setTimeout(() => {
            if (message.parentNode) {
                message.remove();
            }
        }, 5000);
    }
}

// Inicialización cuando se carga la página
document.addEventListener('DOMContentLoaded', function () {
    // Detectar método actual basado en la URL o clase del body
    let currentMethod = '';
    if (window.location.pathname.includes('simplex')) {
        currentMethod = 'simplex';
    } else if (window.location.pathname.includes('granm')) {
        currentMethod = 'granm';
    } else if (window.location.pathname.includes('dosfases')) {
        currentMethod = 'dosfases';
    }

    // Agregar botones de ejemplo si estamos en una página de método Y no existen ya
    if (currentMethod && examples[currentMethod]) {
        const form = document.querySelector('form');
        // Verificar si ya existen botones de ejemplo en el HTML
        const existingExamples = document.querySelector('.form-label:contains("Ejemplos Rápidos"), .form-label[innerHTML*="Ejemplos Rápidos"], label[class*="form-label"]:has([class*="fa-star"])');
        const existingExamplesByText = Array.from(document.querySelectorAll('.form-label')).find(label =>
            label.textContent.includes('Ejemplos Rápidos')
        );

        if (form && !existingExamplesByText) {
            const exampleButtonsContainer = document.createElement('div');
            exampleButtonsContainer.className = 'mb-3';
            exampleButtonsContainer.innerHTML = `
                <label class="form-label fw-bold">
                    <i class="fas fa-star text-warning me-1"></i>Ejemplos Rápidos:
                </label>
                ${createExampleButtons(currentMethod)}
                <button type="button" class="btn btn-outline-danger btn-sm" onclick="clearForm()">
                    <i class="fas fa-eraser me-1"></i>Limpiar
                </button>
            `;

            // Insertar antes del primer campo del formulario
            const firstFormGroup = form.querySelector('.mb-3');
            if (firstFormGroup) {
                form.insertBefore(exampleButtonsContainer, firstFormGroup);
            }
        }
    }

    // Cargar datos guardados y configurar características del método
    if (currentMethod) {
        loadFormData(currentMethod);
        setupMethodFeatures(currentMethod);
    }
});
