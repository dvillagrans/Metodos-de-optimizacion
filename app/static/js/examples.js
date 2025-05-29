// Datos de ejemplo para los diferentes métodos de optimización
const examples = {
    simplex: [
        {
            name: "Ejemplo 1 - Producción",
            c: "5,7",
            A: "2,3\n1,1\n1,0",
            b: "12,5,3",
            minimize: false,
            description: "Maximizar: 5x₁ + 7x₂"
        },
        {
            name: "Ejemplo 2 - Transporte",
            c: "3,4,6",
            A: "1,1,1\n2,1,0\n0,1,2",
            b: "10,8,7",
            minimize: false,
            description: "Maximizar: 3x₁ + 4x₂ + 6x₃"
        },
        {
            name: "Ejemplo 3 - Inversión",
            c: "0.2,0.3,0.1",
            A: "1,1,1\n0.5,0.2,0.3\n0.1,0.4,0.2",
            b: "1000,400,300",
            minimize: false,
            description: "Maximizar: 0.2x₁ + 0.3x₂ + 0.1x₃"
        }
    ],
    granm: [
        {
            name: "Ejemplo 1 - Gran M",
            c: "2,3",
            A: "1,1\n2,1\n1,2",
            b: "4,6,5",
            eq_constraints: "0",
            minimize: false,
            description: "Maximizar: 2x₁ + 3x₂ con restricción de igualdad"
        },
        {
            name: "Ejemplo 2 - Sistema Mixto",
            c: "3,2,1",
            A: "1,1,1\n2,1,0\n1,0,1",
            b: "6,8,4",
            eq_constraints: "1,2",
            minimize: false,
            description: "Maximizar: 3x₁ + 2x₂ + x₃ con múltiples igualdades"
        },
        {
            name: "Ejemplo 3 - Minimización",
            c: "4,5",
            A: "2,1\n1,3\n1,1",
            b: "10,12,6",
            eq_constraints: "2",
            minimize: true,
            description: "Minimizar: 4x₁ + 5x₂ con restricción de igualdad"
        }
    ],
    dosfases: [
        {
            name: "Ejemplo 1 - Dos Fases",
            c: "3,2",
            A: "1,1\n1,-1\n2,1",
            b: "4,1,6",
            eq_constraints: "0,1",
            minimize: false,
            description: "Maximizar: 3x₁ + 2x₂ con restricciones de igualdad"
        },
        {
            name: "Ejemplo 2 - Sistema Complejo",
            c: "2,3,1",
            A: "1,1,1\n2,1,-1\n1,2,1",
            b: "6,4,8",
            eq_constraints: "1,2",
            minimize: false,
            description: "Maximizar: 2x₁ + 3x₂ + x₃ con sistema complejo"
        },
        {
            name: "Ejemplo 3 - Producción Mixta",
            c: "5,4,3",
            A: "1,0,1\n0,1,1\n1,1,0",
            b: "5,4,6",
            eq_constraints: "0",
            minimize: true,
            description: "Minimizar: 5x₁ + 4x₂ + 3x₃ con producción mixta"
        }
    ]
};

// Función para cargar ejemplo en el formulario
function loadExample(method, exampleIndex) {
    const example = examples[method][exampleIndex];

    if (!example) {
        console.error('Ejemplo no encontrado');
        return;
    }

    // Llenar campos comunes
    document.getElementById('c').value = example.c;
    document.getElementById('A').value = example.A;
    document.getElementById('b').value = example.b;

    // Manejar checkbox de minimizar
    const minimizeCheckbox = document.getElementById('minimize');
    if (minimizeCheckbox) {
        minimizeCheckbox.checked = example.minimize || false;
    }

    // Manejar campo de restricciones de igualdad (para Gran M y Dos Fases)
    const eqConstraintsField = document.getElementById('eq_constraints');
    if (eqConstraintsField && example.eq_constraints !== undefined) {
        eqConstraintsField.value = example.eq_constraints;
    }

    // Manejar campo M específico para Gran M
    const mField = document.getElementById('M');
    if (mField && method === 'granm') {
        mField.value = example.M || 1000;
    }

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
    document.getElementById('c').value = '';
    document.getElementById('A').value = '';
    document.getElementById('b').value = '';

    const minimizeCheckbox = document.getElementById('minimize');
    if (minimizeCheckbox) {
        minimizeCheckbox.checked = false;
    }

    const eqConstraintsField = document.getElementById('eq_constraints');
    if (eqConstraintsField) {
        eqConstraintsField.value = '';
    }

    const mField = document.getElementById('M');
    if (mField) {
        mField.value = '1000';
    }

    const trackIterationsCheckbox = document.getElementById('track_iterations');
    if (trackIterationsCheckbox) {
        trackIterationsCheckbox.checked = false;
    }

    showNotification('Formulario limpiado', 'info');
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

    // Agregar botones de ejemplo si estamos en una página de método
    if (currentMethod && examples[currentMethod]) {
        const form = document.querySelector('form');
        if (form) {
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
});
