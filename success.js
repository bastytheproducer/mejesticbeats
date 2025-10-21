// Obtener parámetros de la URL
const urlParams = new URLSearchParams(window.location.search);
const beatName = urlParams.get('beat');
const transactionId = urlParams.get('txn');
const paymentId = urlParams.get('payment_id'); // Parámetro de Mercado Pago
const status = urlParams.get('status'); // Estado del pago

// Verificar autenticación
function checkAuthentication() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        // Redirigir a login si no hay token
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// Cargar información de la compra
function loadPurchaseInfo() {
    if (!checkAuthentication()) return;

    if (beatName) {
        document.getElementById('beat-name').textContent = decodeURIComponent(beatName);
    }

    if (transactionId) {
        document.getElementById('transaction-id').textContent = transactionId;
    } else if (paymentId) {
        document.getElementById('transaction-id').textContent = paymentId;
    }

    // Mostrar fecha actual
    const now = new Date();
    const dateString = now.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    document.getElementById('purchase-date').textContent = dateString;

    // Verificar estado del pago de Mercado Pago
    if (status === 'approved') {
        // Pago aprobado, mostrar descarga inmediatamente
        showDownloadSection();
    } else if (status === 'pending') {
        // Pago pendiente
        showPendingMessage();
    } else if (status === 'failure') {
        // Pago fallido
        showFailureMessage();
    } else {
        // Para desarrollo, mostrar descarga después de un tiempo
        setTimeout(() => {
            showDownloadSection();
        }, 2000);
    }
}

// Mostrar sección de descarga
function showDownloadSection() {
    const downloadSection = document.getElementById('downloadSection');
    const downloadLink = document.getElementById('downloadLink');

    // Construir URL de descarga con el beat seleccionado
    const downloadUrl = transactionId
        ? `/api/download/${transactionId}?beat=${encodeURIComponent(beatName)}`
        : `/api/download/${paymentId}?beat=${encodeURIComponent(beatName)}`;

    downloadLink.href = downloadUrl;
    downloadLink.textContent = `Descargar ${beatName}`;

    downloadSection.style.display = 'block';
}

// Mostrar mensaje de pago pendiente
function showPendingMessage() {
    const nextSteps = document.querySelector('.next-steps ul');
    const pendingItem = document.createElement('li');
    pendingItem.textContent = 'Tu pago está siendo procesado. Recibirás un email cuando esté aprobado.';
    pendingItem.style.color = '#ffa500';
    nextSteps.appendChild(pendingItem);
}

// Mostrar mensaje de pago fallido
function showFailureMessage() {
    const nextSteps = document.querySelector('.next-steps ul');
    const failureItem = document.createElement('li');
    failureItem.textContent = 'Tu pago no pudo ser procesado. Intenta nuevamente.';
    failureItem.style.color = '#ff0000';
    nextSteps.appendChild(failureItem);

    // Ocultar sección de descarga
    document.getElementById('downloadSection').style.display = 'none';
}

// Inicializar página
document.addEventListener('DOMContentLoaded', function() {
    loadPurchaseInfo();
});
