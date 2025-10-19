// Obtener el parámetro del beat desde la URL
const urlParams = new URLSearchParams(window.location.search);
const selectedBeat = urlParams.get('beat');

if (selectedBeat) {
    document.querySelector('h2').textContent = `Comprar ${selectedBeat}`;
    document.querySelector('p').textContent = `Inicia sesión para completar la compra de ${selectedBeat}`;
}

// Funciones de login y registro
function showRegister() {
    document.querySelector('.login-form').style.display = 'none';
    document.querySelector('.register-form').style.display = 'block';
}

function showLogin() {
    document.querySelector('.register-form').style.display = 'none';
    document.querySelector('.login-form').style.display = 'block';
}

function loginWithGoogle() {
    // Simulación de login con Google
    alert('Redirigiendo a Google para iniciar sesión...');
    // En una implementación real, usarías Google Sign-In API
    // window.location.href = 'https://accounts.google.com/signin';
}

function registerWithGoogle() {
    // Simulación de registro con Google
    alert('Redirigiendo a Google para registrarse...');
    // En una implementación real, usarías Google Sign-In API
    // window.location.href = 'https://accounts.google.com/signup';
}

function forgotPassword() {
    alert('Funcionalidad de recuperación de contraseña próximamente.');
}

// Manejar el formulario de login
document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    // Simulación de login
    if (email && password) {
        // Redirigir a la página de checkout
        window.location.href = 'checkout.html?beat=' + encodeURIComponent(selectedBeat || 'tu beat');
    } else {
        alert('Por favor, completa todos los campos.');
    }
});

// Manejar el formulario de registro
document.getElementById('registerFormElement').addEventListener('submit', function(e) {
    e.preventDefault();

    const name = document.getElementById('regName').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;

    if (password !== confirmPassword) {
        alert('Las contraseñas no coinciden.');
        return;
    }

    if (name && email && password) {
        // Redirigir a la página de checkout
        window.location.href = 'checkout.html?beat=' + encodeURIComponent(selectedBeat || 'tu beat');
    } else {
        alert('Por favor, completa todos los campos.');
    }
});

// Animación de entrada
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('.login-form, .register-form');
    forms.forEach(form => {
        form.style.opacity = '0';
        form.style.transform = 'translateY(20px)';
        setTimeout(() => {
            form.style.transition = 'all 0.5s ease-out';
            form.style.opacity = '1';
            form.style.transform = 'translateY(0)';
        }, 100);
    });
});
