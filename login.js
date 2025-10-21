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
    document.querySelector('.forgot-password-form').style.display = 'none';
    document.querySelector('.login-form').style.display = 'block';
}

function showForgotPassword() {
    window.location.href = 'reset_password.html';
}

function initializeGoogleSignIn() {
    // Inicializar Google Sign-In para login
    google.accounts.id.initialize({
        client_id: '834692381201-sa5mpbj4mjrucgkslgf0oacdn40p6794.apps.googleusercontent.com',
        callback: handleCredentialResponse
    });

    // Configurar el origen autorizado para desarrollo local
    gapi.load('auth2', function() {
        gapi.auth2.init({
            client_id: '834692381201-sa5mpbj4mjrucgkslgf0oacdn40p6794.apps.googleusercontent.com',
            scope: 'profile email'
        });
    });

    // Renderizar el botón de Google para login
    google.accounts.id.renderButton(
        document.getElementById('google-login-button'),
        {
            theme: 'outline',
            size: 'large',
            text: 'signin_with',
            shape: 'rectangular',
            logo_alignment: 'left'
        }
    );

    // Renderizar el botón de Google para registro
    google.accounts.id.renderButton(
        document.getElementById('google-register-button'),
        {
            theme: 'outline',
            size: 'large',
            text: 'signup_with',
            shape: 'rectangular',
            logo_alignment: 'left'
        }
    );
}



// Llamar a la inicialización cuando el script de Google esté cargado
window.onload = function() {
    if (typeof google !== 'undefined') {
        initializeGoogleSignIn();
    } else {
        // Si el script no está cargado, esperar un poco
        setTimeout(initializeGoogleSignIn, 1000);
    }
};

function handleCredentialResponse(response) {
    // Decodificar el JWT token
    const responsePayload = decodeJwtResponse(response.credential);

    console.log('Usuario autenticado:', responsePayload);

    // Enviar el token al servidor para validación
    fetch('/api/auth/google', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            credential: response.credential
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Autenticación exitosa en el servidor');
            // Guardar token JWT en localStorage
            if (data.token) {
                localStorage.setItem('auth_token', data.token);
            }
            // Redirigir a la página de checkout
            const selectedBeat = new URLSearchParams(window.location.search).get('beat');
            window.location.href = 'checkout.html?beat=' + encodeURIComponent(selectedBeat || 'tu beat');
        } else {
            console.error('Error en la autenticación:', data.message);
            alert('Error en la autenticación: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error al enviar el token al servidor:', error);
        alert('Error de conexión. Inténtalo de nuevo.');
    });
}

function decodeJwtResponse(token) {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));

    return JSON.parse(jsonPayload);
}



// Manejar el formulario de login
document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    // Validación básica
    if (!email || !password) {
        alert('Por favor, completa todos los campos.');
        return;
    }

    if (!/\S+@\S+\.\S+/.test(email)) {
        alert('Por favor, ingresa un email válido.');
        return;
    }

    // Enviar datos al servidor
    fetch('/api/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email: email,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Login exitoso! Redirigiendo al checkout...');
            // Guardar token JWT en localStorage
            if (data.token) {
                localStorage.setItem('auth_token', data.token);
            }
            window.location.href = 'checkout.html?beat=' + encodeURIComponent(selectedBeat || 'tu beat');
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error al enviar datos de login:', error);
        alert('Error de conexión. Inténtalo de nuevo.');
    });
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

    if (!name || !email || !password) {
        alert('Por favor, completa todos los campos.');
        return;
    }

    if (!/\S+@\S+\.\S+/.test(email)) {
        alert('Por favor, ingresa un email válido.');
        return;
    }

    if (password.length < 6) {
        alert('La contraseña debe tener al menos 6 caracteres.');
        return;
    }

    // Enviar datos al servidor
    fetch('/api/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            name: name,
            email: email,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Registro exitoso! Ahora puedes iniciar sesión.');
            // Guardar token JWT en localStorage
            if (data.token) {
                localStorage.setItem('auth_token', data.token);
            }
            showLogin(); // Cambiar a formulario de login
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error al enviar datos de registro:', error);
        alert('Error de conexión. Inténtalo de nuevo.');
    });
});

// Función para alternar la visibilidad de la contraseña
function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    const button = input.nextElementSibling;
    const icon = button.querySelector('.eye-icon');

    if (input.type === 'password') {
        input.type = 'text';
        icon.innerHTML = '<path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92 1.11-1.11c.55-.55.55-1.44 0-1.99-1.73-1.73-4.39-2.5-7-2.5-1.02 0-2.01.16-2.91.46l1.15 1.15C10.97 7.13 11.47 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42 1.11 1.11 1.41-1.41L3.51 2.86 2.1 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>';
    } else {
        input.type = 'password';
        icon.innerHTML = '<path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>';
    }
}

// Manejar el formulario de recuperación de contraseña
document.getElementById('forgotPasswordFormElement').addEventListener('submit', function(e) {
    e.preventDefault();

    const email = document.getElementById('forgotEmail').value;

    if (!email) {
        alert('Por favor, ingresa tu email.');
        return;
    }

    if (!/\S+@\S+\.\S+/.test(email)) {
        alert('Por favor, ingresa un email válido.');
        return;
    }

    // Enviar solicitud al servidor
    fetch('/api/forgot_password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email: email
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Si el email existe, recibirás instrucciones para recuperar tu contraseña.');
            showLogin(); // Volver al login
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error al enviar solicitud de recuperación:', error);
        alert('Error de conexión. Inténtalo de nuevo.');
    });
});

// Animación de entrada
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('.login-form, .register-form, .forgot-password-form');
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
