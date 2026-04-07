/**
 * Sistema de Gestion Academica - JavaScript Principal
 */

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });

    // Close offcanvas sidebar when clicking a link (mobile)
    const sidebarLinks = document.querySelectorAll('#sidebar .nav-link');
    const offcanvas = document.getElementById('sidebar');
    
    if (offcanvas) {
        const bsOffcanvas = bootstrap.Offcanvas.getOrCreateInstance(offcanvas);
        sidebarLinks.forEach(function(link) {
            link.addEventListener('click', function() {
                bsOffcanvas.hide();
            });
        });
    }

    // Enable tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(function(tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || 'Esta seguro de realizar esta accion?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Format currency inputs
    const currencyInputs = document.querySelectorAll('.currency-input');
    currencyInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            const value = parseFloat(this.value);
            if (!isNaN(value)) {
                this.value = value.toFixed(2);
            }
        });
    });

    // Search form auto-submit on enter
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(function(input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                this.closest('form').submit();
            }
        });
    });
});

/**
 * Guardar asistencia via AJAX
 */
function guardarAsistencia(sesionId) {
    const asistencias = [];
    const rows = document.querySelectorAll('.asistencia-row');
    
    rows.forEach(function(row) {
        const estudianteId = row.dataset.estudianteId;
        const estado = row.querySelector('select[name="estado"]').value;
        const observaciones = row.querySelector('textarea[name="observaciones"]')?.value || '';
        
        asistencias.push({
            estudiante_id: parseInt(estudianteId),
            estado: estado,
            observaciones: observaciones
        });
    });

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/api/asistencia/guardar/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            sesion_id: sesionId,
            asistencias: asistencias
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('success', data.message);
        } else {
            showToast('danger', data.error || 'Error al guardar');
        }
    })
    .catch(error => {
        showToast('danger', 'Error de conexion');
        console.error('Error:', error);
    });
}

/**
 * Mostrar toast notification
 */
function showToast(type, message) {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    document.getElementById('toast-container').insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

/**
 * Formatear numero como moneda
 */
function formatCurrency(number) {
    return new Intl.NumberFormat('es-PY', {
        style: 'currency',
        currency: 'PYG',
        minimumFractionDigits: 0
    }).format(number);
}

/**
 * Calcular saldo pendiente dinamicamente
 */
function calcularSaldo(montoAcordado, montoPagado) {
    return montoAcordado - montoPagado;
}
