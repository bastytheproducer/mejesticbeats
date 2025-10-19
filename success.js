// Obtener parámetros de la URL
const urlParams = new URLSearchParams(window.location.search);
const selectedBeat = urlParams.get('beat');
const transactionId = urlParams.get('txn');

// Datos de los beats
const beatData = {
    'Beat Verano Reggaeton': {
        genre: 'Reggaeton',
        image: 'Caratulas de lo beats/beat verano reggeaton.png'
    },
    'Beat 2025 Verano Trap': {
        genre: 'Trap',
        image: 'Caratulas de lo beats/Beat 2025 verano trap.png'
    },
    'Beat Rellax Reggaeton': {
        genre: 'Reggaeton Relax',
        image: 'Caratulas de lo beats/beat rellax reggeaton.png'
    },
    'Beat Hip Hop Piano Gigant': {
        genre: 'Hip Hop',
        image: 'Caratulas de lo beats/beat hip hop piano gigant.jpg'
    },
    'Beat Sin Frontera': {
        genre: 'Instrumental',
        image: 'Caratulas de lo beats/beat sin frontera.png'
    },
    'Beat Trap Navideño Chilling': {
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
        document.getElementById('beat-image').src = beat.image;
    } else {
        document.getElementById('beat-title').textContent = selectedBeat || 'Beat Seleccionado';
        document.getElementById('beat-genre').textContent = 'Género';
    }

    if (transactionId) {
        document.getElementById('transaction-id').textContent = transactionId;
    }
}

// Descargar beat
function downloadBeat() {
    if (!selectedBeat) {
        alert('No se pudo encontrar el beat para descargar.');
        return;
    }

    // Simulación de descarga
    alert(`¡Descarga iniciada! El archivo "${selectedBeat}.mp3" se descargará automáticamente.`);

    // En una implementación real, esto sería un enlace de descarga real
    // window.location.href = `/downloads/${selectedBeat.replace(/\s+/g, '_').toLowerCase()}.mp3`;
}

// Compartir en redes sociales
function shareOnTwitter() {
    const text = `¡Acabo de adquirir "${selectedBeat}" en Beat Venta! 🎵🔥 #BeatVenta #MusicProduction`;
    const url = window.location.href;
    const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`;
    window.open(twitterUrl, '_blank');
}

function shareOnFacebook() {
    const url = window.location.href;
    const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
    window.open(facebookUrl, '_blank');
}

// Animaciones de entrada
document.addEventListener('DOMContentLoaded', function() {
    loadBeatInfo();

    // Animar elementos con delay
    const elements = document.querySelectorAll('.beat-summary, .next-steps, .actions, .social-share');
    elements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        setTimeout(() => {
            element.style.transition = 'all 0.6s ease-out';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, 200 + (index * 100));
    });

    // Confetti effect (simulado)
    setTimeout(() => {
        createConfetti();
    }, 1000);
});

// Crear efecto de confetti
function createConfetti() {
    const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', '#dda0dd'];

    for (let i = 0; i < 50; i++) {
        setTimeout(() => {
            const confetti = document.createElement('div');
            confetti.style.position = 'fixed';
            confetti.style.width = '10px';
            confetti.style.height = '10px';
            confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.left = Math.random() * 100 + 'vw';
            confetti.style.top = '-10px';
            confetti.style.borderRadius = '50%';
            confetti.style.zIndex = '9999';
            confetti.style.pointerEvents = 'none';
            confetti.style.animation = 'fall 3s linear forwards';

            document.body.appendChild(confetti);

            setTimeout(() => {
                document.body.removeChild(confetti);
            }, 3000);
        }, i * 50);
    }
}

// Agregar estilos para la animación de confetti
const style = document.createElement('style');
style.textContent = `
    @keyframes fall {
        to {
            transform: translateY(100vh) rotate(360deg);
        }
    }
`;
document.head.appendChild(style);
