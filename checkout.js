// Obtener el parámetro del beat desde la URL
const urlParams = new URLSearchParams(window.location.search);
const selectedBeat = urlParams.get('beat');

// Verificar autenticación al cargar la página
function checkAuthentication() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        // Redirigir a login si no hay token
        window.location.href = 'login.html?beat=' + encodeURIComponent(selectedBeat || '');
        return false;
    }
    return true;
}

// Datos de los beats para mostrar información
const beatData = {
    'Beat Verano Reggaeton': {
        price: '$20',
        genre: 'Reggaeton',
        image: 'Caratulas de lo beats/beat verano reggeaton.png'
    },
    'Beat 2025 Verano Trap': {
        price: '$25',
        genre: 'Trap',
        image: 'Caratulas de lo beats/Beat 2025 verano trap.png'
    },
    'Beat Rellax Reggaeton': {
        price: '$22',
        genre: 'Reggaeton Relax',
        image: 'Caratulas de lo beats/beat rellax reggeaton.png'
    },
    'Beat Hip Hop Piano Gigant': {
        price: '$28',
        genre: 'Hip Hop',
        image: 'Caratulas de lo beats/beat hip hop piano gigant.jpg'
    },
    'Beat Sin Frontera': {
        price: '$30',
        genre: 'Instrumental',
        image: 'Caratulas de lo beats/beat sin frontera.png'
    },
    'Beat Trap Navideño Chilling': {
        price: '$26',
        genre: 'Trap Navideño',
        image: 'Caratulas de lo beats/beat trap navideño chilling.png'
    }
};

// Cargar información del beat
function loadBeatInfo() {
    if (selectedBeat && beatData[selectedBeat]) {
        const beat = beatData[selectedBeat];
        document.getElementById('beat-title').textContent = selectedBeat;
        document.getElementById('beat-genre').textContent = beat.genre;
        document.getElementById('beat-price').textContent = beat.price;
        document.getElementById('beat-image').src = beat.image;
    } else {
        document.getElementById('beat-title').textContent = selectedBeat || 'Beat Seleccionado';
        document.getElementById('beat-genre').textContent = 'Género';
        document.getElementById('beat-price').textContent = '$0';
    }
}

// Mostrar términos y condiciones
function showTerms() {
    alert('Términos y Condiciones:\n\n1. Los beats son para uso personal y comercial.\n2. No se permiten reventas sin autorización.\n3. Descargas ilimitadas después de la compra.\n4. Soporte técnico incluido por 30 días.');
}

// Procesar pago con Mercado Pago
async function processPayment(beatName, beatPrice) {
    const token = localStorage.getItem('auth_token');
    try {
        const response = await fetch('/api/create_preference', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                beat_name: beatName,
                beat_price: beatPrice
            })
        });

        const data = await response.json();

        if (data.success) {
            // Inicializar checkout embebido
            const mp = new MercadoPago('APP_USR-692d1872-0d2c-40f2-89c2-e876e3ed5814', {
                locale: 'es-AR'
            });

            mp.checkout({
                preference: {
                    id: data.preference_id
                },
                render: {
                    container: '#wallet_container',
                    label: 'Pagar con Mercado Pago'
                }
            });
        } else {
            throw new Error(data.message || 'Error creando preferencia de pago');
        }
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
}

// Manejar envío del formulario
document.getElementById('paymentForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const submitBtn = document.querySelector('.btn-primary');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Procesando...';
    submitBtn.disabled = true;

    try {
        // Validar términos y condiciones
        if (!document.getElementById('terms').checked) {
            throw new Error('Debes aceptar los términos y condiciones');
        }

        // Obtener precio del beat
        const beatPrice = document.getElementById('beat-price').textContent;

        // Procesar pago con Mercado Pago
        await processPayment(selectedBeat, beatPrice);

    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
});

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    if (checkAuthentication()) {
        loadBeatInfo();
    }
});
