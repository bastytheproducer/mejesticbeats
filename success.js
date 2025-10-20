// Obtener parámetros de la URL
const urlParams = new URLSearchParams(window.location.search);
const beatName = urlParams.get('beat');
const transactionId = urlParams.get('txn');

// Cargar información de la compra
function loadPurchaseInfo() {
    if (beatName) {
        document.getElementById('beat-name').textContent = decodeURIComponent(beatName);
    }

    if (transactionId) {
        document.getElementById('transaction-id').textContent = transactionId;
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

    // Simular verificación de pago (en producción esto vendría del backend)
    setTimeout(() => {
        showDownloadSection();
    }, 2000);
}

// Mostrar sección de descarga
function showDownloadSection() {
    const downloadSection = document.getElementById('downloadSection');
    const downloadLink = document.getElementById('downloadLink');

    // Construir URL de descarga con el beat seleccionado
    downloadLink.href = `/api/download/${transactionId}?beat=${encodeURIComponent(beatName)}`;
    downloadLink.textContent = `Descargar ${beatName}`;

    downloadSection.style.display = 'block';
}

// Inicializar página
document.addEventListener('DOMContentLoaded', function() {
    loadPurchaseInfo();
});
