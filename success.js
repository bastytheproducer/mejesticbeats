// Página de confirmación: muestra el resultado del pago y entrega el MP3 completo.
// La descarga la autoriza el servidor, que verifica el pago en Mercado Pago;
// lo que diga la dirección de esta página no basta para descargar.

const urlParams = new URLSearchParams(window.location.search);
const beatName = urlParams.get('beat');
const paymentId = urlParams.get('payment_id') || urlParams.get('collection_id') || urlParams.get('txn');
const status = urlParams.get('status') || urlParams.get('collection_status');

function addStep(text, color) {
    const item = document.createElement('li');
    item.textContent = text;
    item.style.color = color;
    document.querySelector('.next-steps ul').appendChild(item);
}

function setHeading(icon, title, subtitle) {
    document.querySelector('.success-icon').textContent = icon;
    document.querySelector('.success-page h1').textContent = title;
    document.querySelector('.success-page > p').textContent = subtitle;
}

function loadPurchaseInfo() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        window.location.href = 'login.html' + (beatName ? '?beat=' + encodeURIComponent(beatName) : '');
        return;
    }

    document.getElementById('beat-name').textContent = beatName || '—';
    document.getElementById('transaction-id').textContent = paymentId || '—';
    document.getElementById('purchase-date').textContent = new Date().toLocaleDateString('es-CL', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    if (status === 'approved' && beatName && paymentId) {
        showDownloadSection(token);
    } else if (status === 'pending' || status === 'in_process') {
        setHeading('⏳', 'Pago en proceso', 'Mercado Pago todavía está confirmando tu pago.');
        addStep('Cuando el pago se apruebe, vuelve a esta página para descargar tu beat.', '#ff9a3d');
    } else {
        setHeading('⚠️', 'No pudimos confirmar el pago', 'No se hizo ningún cobro por esta compra, o el pago fue rechazado.');
        addStep('Vuelve al catálogo e intenta de nuevo. Si te cobraron, escríbenos con el ID de transacción.', '#ff6b7d');
    }
}

function showDownloadSection(token) {
    const downloadSection = document.getElementById('downloadSection');
    const downloadLink = document.getElementById('downloadLink');
    const label = `Descargar ${beatName}`;

    downloadLink.textContent = label;
    downloadSection.style.display = 'block';

    downloadLink.addEventListener('click', async (event) => {
        event.preventDefault();
        if (downloadLink.dataset.busy) return;
        downloadLink.dataset.busy = '1';
        downloadLink.textContent = 'Preparando descarga…';

        try {
            const response = await fetch(
                `/api/download/${encodeURIComponent(paymentId)}?beat=${encodeURIComponent(beatName)}`,
                { headers: { Authorization: `Bearer ${token}` } }
            );
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.error || 'No se pudo descargar el beat');
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const tempLink = document.createElement('a');
            tempLink.href = url;
            tempLink.download = `${beatName}.mp3`;
            document.body.appendChild(tempLink);
            tempLink.click();
            tempLink.remove();
            URL.revokeObjectURL(url);
        } catch (error) {
            addStep(`${error.message}. Escríbenos con el ID de transacción y te lo enviamos.`, '#ff6b7d');
        } finally {
            delete downloadLink.dataset.busy;
            downloadLink.textContent = label;
        }
    });
}

document.addEventListener('DOMContentLoaded', loadPurchaseInfo);
