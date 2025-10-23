// @ts-nocheck
const audioPlayer = document.getElementById('audio-player');
const playPauseBtn = document.getElementById('play-pause-btn');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const progressBar = document.getElementById('progress-bar');
const volumeBar = document.getElementById('volume-bar');
const muteBtn = document.getElementById('mute-btn');
const currentTimeEl = document.getElementById('current-time');
const durationEl = document.getElementById('duration');
const currentTitle = document.getElementById('current-title');
const currentGenre = document.getElementById('current-genre');
const currentArt = document.getElementById('current-art');
const waveformCanvas = document.getElementById('waveform-canvas');
const waveformContainer = document.getElementById('waveform-container');

let isMuted = false;
let previousVolume = 1;

let canvasContext = waveformCanvas.getContext('2d');
let audioBuffer = null;
let waveformData = [];

let currentTrackIndex = 0;
const tracks = [
    {
        title: 'Beat Verano Reggaeton',
        genre: 'Reggaeton',
        src: 'BEATS/BEAT%20VERANO%20REGGEATON.mp3',
        art: 'Caratulas%20de%20lo%20beats/beat%20verano%20reggeaton.png'
    },
    {
        title: 'Beat 2025 Verano Trap',
        genre: 'Trap',
        src: 'BEATS/BEAT%202025%20VERANO%20TRAP%20HOUSE.mp3',
        art: 'Caratulas%20de%20lo%20beats/Beat%202025%20verano%20trap.png'
    },
    {
        title: 'Beat Rellax Reggaeton',
        genre: 'Reggaeton Relax',
        src: 'BEATS/BEAT%20RELLAX%20REGGEATON.mp3',
        art: 'Caratulas%20de%20lo%20beats/beat%20rellax%20reggeaton.png'
    },
    {
        title: 'Beat Hip Hop Piano Gigant',
        genre: 'Hip Hop',
        src: 'BEATS/BEAT%20HIP%20HOP%20PIANO%20GIGANT.mp3',
        art: 'Caratulas%20de%20lo%20beats/beat%20hip%20hop%20piano%20gigant.jpg'
    },
    {
        title: 'Beat Sin Frontera',
        genre: 'Instrumental',
        src: 'BEATS/BEAT%20SIN%20FRONTERA.mp3',
        art: 'Caratulas%20de%20lo%20beats/beat%20sin%20frontera.png'
    },
    {
        title: 'Beat Trap Navideño Chilling',
        genre: 'Trap Navideño',
        src: 'BEATS/BEAT%20TRAP%20NAVIDEÑO%20CHILLING.mp3',
        art: 'Caratulas%20de%20lo%20beats/beat%20trap%20navideño%20chilling.png'
    }
];

function loadTrack(index) {
    const track = tracks[index];
    audioPlayer.src = track.src;
    currentTitle.textContent = track.title;
    currentGenre.textContent = track.genre;
    currentArt.src = track.art;
    audioPlayer.load();

    // Load waveform for the track
    loadAudioBuffer(track.src);
}

function playTrack() {
    audioPlayer.play();
    playPauseBtn.textContent = '⏸';
}

function pauseTrack() {
    audioPlayer.pause();
    playPauseBtn.textContent = '▶';
}

function updateProgress() {
    const { currentTime, duration } = audioPlayer;
    const progressPercent = (currentTime / duration) * 100;
    progressBar.value = progressPercent;
    currentTimeEl.textContent = formatTime(currentTime);
    durationEl.textContent = formatTime(duration);

    // Update custom progress bar
    const progressFill = document.querySelector('.progress-fill');
    const progressThumb = document.querySelector('.progress-thumb');
    if (progressFill && progressThumb) {
        progressFill.style.width = progressPercent + '%';
        progressThumb.style.left = progressPercent + '%';
    }

    // Update waveform with progress
    if (duration > 0) {
        drawWaveform(progressPercent);
    }
}

function formatTime(time) {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

function setProgress(e) {
    const width = this.clientWidth;
    const clickX = e.offsetX;
    const duration = audioPlayer.duration;
    audioPlayer.currentTime = (clickX / width) * duration;
}

function setWaveformProgress(e) {
    const rect = waveformContainer.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const width = rect.width;
    const duration = audioPlayer.duration;
    audioPlayer.currentTime = (clickX / width) * duration;
}

function generateWaveform(audioBuffer) {
    const rawData = audioBuffer.getChannelData(0);
    const samples = 200; // Number of bars in the waveform
    const blockSize = Math.floor(rawData.length / samples);
    waveformData = [];

    for (let i = 0; i < samples; i++) {
        let blockStart = blockSize * i;
        let sum = 0;
        for (let j = 0; j < blockSize; j++) {
            sum += Math.abs(rawData[blockStart + j]);
        }
        waveformData[i] = sum / blockSize;
    }

    drawWaveform();
}

function drawWaveform(progressPercent = 0) {
    const canvas = waveformCanvas;
    const ctx = canvasContext;
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    const barWidth = width / waveformData.length;
    const maxAmplitude = Math.max(...waveformData);
    const progressIndex = Math.floor((progressPercent / 100) * waveformData.length);

    waveformData.forEach((amplitude, index) => {
        const barHeight = (amplitude / maxAmplitude) * height * 0.8;
        const x = index * barWidth;
        const y = (height - barHeight) / 2;

        // Color based on progress: green for played, white for unplayed
        ctx.fillStyle = index < progressIndex ? '#4ecdc4' : 'rgba(255, 255, 255, 0.3)';

        ctx.fillRect(x, y, barWidth - 1, barHeight);
    });
}

async function loadAudioBuffer(url) {
    try {
        const response = await fetch(url);
        const arrayBuffer = await response.arrayBuffer();
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        generateWaveform(audioBuffer);
    } catch (error) {
        console.error('Error loading audio buffer:', error);
        // Fallback: draw a simple placeholder waveform
        drawPlaceholderWaveform();
    }
}

function drawPlaceholderWaveform() {
    const canvas = waveformCanvas;
    const ctx = canvasContext;
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';

    for (let i = 0; i < 100; i++) {
        const barHeight = Math.random() * height * 0.6 + height * 0.2;
        const x = (width / 100) * i;
        const y = (height - barHeight) / 2;
        ctx.fillRect(x, y, width / 100 - 1, barHeight);
    }
}

playPauseBtn.addEventListener('click', () => {
    if (audioPlayer.paused) {
        playTrack();
    } else {
        pauseTrack();
    }
});

prevBtn.addEventListener('click', () => {
    currentTrackIndex = (currentTrackIndex - 1 + tracks.length) % tracks.length;
    loadTrack(currentTrackIndex);
    playTrack();
});

nextBtn.addEventListener('click', () => {
    currentTrackIndex = (currentTrackIndex + 1) % tracks.length;
    loadTrack(currentTrackIndex);
    playTrack();
});

audioPlayer.addEventListener('timeupdate', updateProgress);
audioPlayer.addEventListener('loadedmetadata', () => {
    durationEl.textContent = formatTime(audioPlayer.duration);
});

progressBar.addEventListener('input', (e) => {
    const duration = audioPlayer.duration;
    audioPlayer.currentTime = (e.target.value / 100) * duration;
});

// Custom progress bar click handler
const customProgressBar = document.querySelector('.progress-bar');
if (customProgressBar) {
    customProgressBar.addEventListener('click', (e) => {
        const rect = customProgressBar.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const width = rect.width;
        const duration = audioPlayer.duration;
        audioPlayer.currentTime = (clickX / width) * duration;
    });
}

volumeBar.addEventListener('input', (e) => {
    audioPlayer.volume = e.target.value;
    updateVolumeBar();
    if (audioPlayer.volume > 0 && isMuted) {
        isMuted = false;
        muteBtn.textContent = '🔊';
    }
});

function updateVolumeBar() {
    const volumePercent = (audioPlayer.volume * 100) + '%';
    volumeBar.style.setProperty('--value', volumePercent);
}

muteBtn.addEventListener('click', () => {
    if (isMuted) {
        // Unmute
        audioPlayer.volume = previousVolume;
        volumeBar.value = previousVolume;
        updateVolumeBar();
        muteBtn.textContent = '🔊';
        isMuted = false;
    } else {
        // Mute
        previousVolume = audioPlayer.volume;
        audioPlayer.volume = 0;
        volumeBar.value = 0;
        updateVolumeBar();
        muteBtn.textContent = '🔇';
        isMuted = true;
    }
});

document.querySelectorAll('.play-btn').forEach((btn, index) => {
    btn.addEventListener('click', () => {
        currentTrackIndex = index;
        loadTrack(currentTrackIndex);
        playTrack();
    });
});

async function loadAvailableBeats() {
    try {
        const response = await fetch('/api/beats');
        const data = await response.json();

        const trackList = document.getElementById('track-list');
        trackList.innerHTML = '';

        if (data.beats.length === 0) {
            trackList.innerHTML = '<p>No hay beats disponibles en este momento.</p>';
            return;
        }

        // Mapear nombres de beats a archivos de audio
        const audioFiles = {
            'Beat Verano Reggaeton': 'BEATS/BEAT VERANO REGGEATON.mp3',
            'Beat 2025 Verano Trap': 'BEATS/BEAT 2025 VERANO TRAP HOUSE.mp3',
            'Beat Rellax Reggaeton': 'BEATS/BEAT RELLAX REGGEATON.mp3',
            'Beat Hip Hop Piano Gigant': 'BEATS/BEAT HIP HOP PIANO GIGANT.mp3',
            'Beat Sin Frontera': 'BEATS/BEAT SIN FRONTERA.mp3',
            'Beat Trap Navideño Chilling': 'BEATS/BEAT TRAP NAVIDEÑO CHILLING.mp3'
        };

        data.beats.forEach(beat => {
            const trackDiv = document.createElement('div');
            trackDiv.className = 'track';
            trackDiv.setAttribute('data-src', audioFiles[beat.name] || '');

            trackDiv.innerHTML = `
                <div class="track-info">
                    <img src="${beat.image}" alt="${beat.name}" class="album-art">
                    <div class="details">
                        <h3>${beat.name}</h3>
                        <p>Género: ${beat.genre}</p>
                        <p>Precio: ${beat.price}</p>
                    </div>
                </div>
                <div class="controls">
                    <button class="play-btn">▶</button>
                    <button class="buy-btn" onclick="buyBeat('${beat.name}')">Comprar Ahora</button>
                </div>
            `;

            trackList.appendChild(trackDiv);
        });

        // Re-inicializar event listeners para los nuevos botones
        document.querySelectorAll('.play-btn').forEach((btn, index) => {
            btn.addEventListener('click', () => {
                const tracks = document.querySelectorAll('.track');
                currentTrackIndex = Array.from(tracks).indexOf(btn.closest('.track'));
                loadTrack(currentTrackIndex);
                playTrack();
            });
        });

    } catch (error) {
        console.error('Error cargando beats:', error);
        document.getElementById('track-list').innerHTML = '<p>Error al cargar los beats. Inténtalo de nuevo más tarde.</p>';
    }
}

async function buyBeat(beatName) {
    try {
        // Verificar stock antes de proceder
        const stockResponse = await fetch(`/api/check_stock/${encodeURIComponent(beatName)}`);
        const stockData = await stockResponse.json();

        if (!stockData.available) {
            alert('Este beat ya no está disponible.');
            // Recargar la página para actualizar la lista
            loadAvailableBeats();
            return;
        }

        // Mapa de beats a sus respectivos links de WebPay
        const webpayLinks = {
            'Beat Verano Reggaeton': 'https://www.webpay.cl/form-pay/329024',
            'Beat 2025 Verano Trap': 'https://www.webpay.cl/form-pay/329189',
            'Beat Trap Navideño Chilling': 'https://www.webpay.cl/form-pay/329222',
            'Beat Rellax Reggaeton': 'https://www.webpay.cl/form-pay/329218',
            'Beat Sin Frontera': 'https://www.webpay.cl/form-pay/329220',
            'Beat Hip Hop Piano Gigant': 'https://www.webpay.cl/form-pay/329219'
        };

        // Redirigir directamente al link de WebPay correspondiente
        if (webpayLinks[beatName]) {
            window.location.href = webpayLinks[beatName];
        } else {
            // Si no se encuentra el beat, redirigir a login como fallback
            window.location.href = 'login.html?beat=' + encodeURIComponent(beatName);
        }
    } catch (error) {
        console.error('Error verificando stock:', error);
        alert('Error al verificar disponibilidad. Inténtalo de nuevo.');
    }
}

function buyCurrentBeat() {
    const currentBeat = tracks[currentTrackIndex];
    buyBeat(currentBeat.title);
}

// Event listener para el botón de compra en el reproductor
document.getElementById('buy-current-btn').addEventListener('click', buyCurrentBeat);

// Event listener para clicks en la waveform
waveformContainer.addEventListener('click', setWaveformProgress);

// Event listener para mouse move en la waveform para mostrar preview
waveformContainer.addEventListener('mousemove', (e) => {
    const rect = waveformContainer.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const width = rect.width;
    const duration = audioPlayer.duration;
    const hoverTime = (clickX / width) * duration;

    // Mostrar tooltip con el tiempo
    showWaveformTooltip(e, formatTime(hoverTime));
});

// Event listener para mouse leave en la waveform
waveformContainer.addEventListener('mouseleave', () => {
    hideWaveformTooltip();
});

// Función para mostrar tooltip en la waveform
function showWaveformTooltip(e, timeString) {
    let tooltip = document.getElementById('waveform-tooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.id = 'waveform-tooltip';
        tooltip.style.position = 'absolute';
        tooltip.style.background = 'rgba(0, 0, 0, 0.8)';
        tooltip.style.color = '#fff';
        tooltip.style.padding = '4px 8px';
        tooltip.style.borderRadius = '4px';
        tooltip.style.fontSize = '12px';
        tooltip.style.pointerEvents = 'none';
        tooltip.style.zIndex = '1000';
        document.body.appendChild(tooltip);
    }

    tooltip.textContent = timeString;
    tooltip.style.left = e.pageX + 10 + 'px';
    tooltip.style.top = e.pageY - 30 + 'px';
    tooltip.style.display = 'block';
}

// Función para ocultar tooltip
function hideWaveformTooltip() {
    const tooltip = document.getElementById('waveform-tooltip');
    if (tooltip) {
        tooltip.style.display = 'none';
    }
}

// Cargar beats disponibles y la primera pista al inicio
document.addEventListener('DOMContentLoaded', () => {
    loadAvailableBeats();
    loadTrack(currentTrackIndex);
});
