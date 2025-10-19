// Obtener el parámetro del beat desde la URL
const urlParams = new URLSearchParams(window.location.search);
const selectedBeat = urlParams.get('beat');

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

// Manejar cambio de método de pago
function handlePaymentMethodChange() {
    const paymentMethod = document.querySelector('input[name="paymentMethod"]:checked').value;
    const cardFields = document.getElementById('cardFields');

    if (paymentMethod === 'card') {
        cardFields.style.display = 'block';
    } else {
        cardFields.style.display = 'none';
    }
}

// Formatear número de tarjeta
function formatCardNumber(value) {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    const matches = v.match(/\d{4,16}/g);
    const match = matches && matches[0] || '';
    const parts = [];
    for (let i = 0, len = match.length; i < len; i += 4) {
        parts.push(match.substring(i, i + 4));
    }
    if (parts.length) {
        return parts.join(' ');
    } else {
        return v;
    }
}

// Formatear fecha de expiración
function formatExpiry(value) {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    if (v.length >= 2) {
        return v.substring(0, 2) + '/' + v.substring(2, 4);
    }
    return v;
}

// Mostrar términos y condiciones
function showTerms() {
    alert('Términos y Condiciones:\n\n1. Los beats son para uso personal y comercial.\n2. No se permiten reventas sin autorización.\n3. Descargas ilimitadas después de la compra.\n4. Soporte técnico incluido por 30 días.');
}

// Procesar pago
function processPayment(paymentMethod, formData) {
    // Simulación de procesamiento de pago
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            // Simular éxito del 90% de las veces
            if (Math.random() > 0.1) {
                resolve({ success: true, transactionId: 'TXN' + Date.now() });
            } else {
                reject({ success: false, message: 'Error en el procesamiento del pago' });
            }
        }, 2000);
    });
}

// Manejar envío del formulario
document.getElementById('paymentForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const submitBtn = document.querySelector('.btn-primary');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Procesando...';
    submitBtn.disabled = true;

    try {
        const paymentMethod = document.querySelector('input[name="paymentMethod"]:checked').value;
        const formData = new FormData(e.target);

        // Validar campos requeridos
        if (!document.getElementById('terms').checked) {
            throw new Error('Debes aceptar los términos y condiciones');
        }

        if (paymentMethod === 'card') {
            const cardNumber = document.getElementById('cardNumber').value.replace(/\s/g, '');
            const expiryDate = document.getElementById('expiryDate').value;
            const cvv = document.getElementById('cvv').value;
            const cardName = document.getElementById('cardName').value;

            if (!cardNumber || cardNumber.length < 13) {
                throw new Error('Número de tarjeta inválido');
            }
            if (!expiryDate || !/^\d{2}\/\d{2}$/.test(expiryDate)) {
                throw new Error('Fecha de expiración inválida');
            }
            if (!cvv || cvv.length < 3) {
                throw new Error('CVV inválido');
            }
            if (!cardName.trim()) {
                throw new Error('Nombre en la tarjeta requerido');
            }
        }

        // Procesar pago
        const result = await processPayment(paymentMethod, formData);

        if (result.success) {
            // Redirigir a página de éxito
            window.location.href = 'success.html?beat=' + encodeURIComponent(selectedBeat) + '&txn=' + result.transactionId;
        } else {
            throw new Error(result.message);
        }

    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
});

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    loadBeatInfo();

    // Manejar cambio de método de pago
    document.querySelectorAll('input[name="paymentMethod"]').forEach(radio => {
        radio.addEventListener('change', handlePaymentMethodChange);
    });

    // Formatear inputs de tarjeta
    document.getElementById('cardNumber').addEventListener('input', function(e) {
        e.target.value = formatCardNumber(e.target.value);
    });

    document.getElementById('expiryDate').addEventListener('input', function(e) {
        e.target.value = formatExpiry(e.target.value);
    });

    document.getElementById('cvv').addEventListener('input', function(e) {
        e.target.value = e.target.value.replace(/[^0-9]/g, '');
    });
});
