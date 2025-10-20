const audioPlayer = document.getElementById('audio-player');
const playPauseBtn = document.getElementById('play-pause-btn');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const progressBar = document.getElementById('progress-bar');
const currentTimeEl = document.getElementById('current-time');
const durationEl = document.getElementById('duration');
const currentTitle = document.getElementById('current-title');
const currentGenre = document.getElementById('current-genre');
const currentArt = document.getElementById('current-art');
const waveformCanvas = document.getElementById('waveform-canvas');
const progressOverlay = document.getElementById('progress-overlay');
const waveformContainer = document.getElementById('waveform-container');

let canvasContext = waveformCanvas.getContext('2d');
let audioBuffer = null;
let waveformData = [];

let currentTrackIndex = 0;
const tracks = [
    {
        title: 'Beat Verano Reggaeton',
        genre: 'Reggaeton',
        src: 'BEATS/BEAT VERANO REGGEATON.mp3',
        art: 'Caratulas de lo beats/beat verano reggeaton.png'
    },
    {
        title: 'Beat 2025 Verano Trap',
        genre: 'Trap',
        src: 'BEATS/BEAT 2025 VERANO TRAP HOUSE.mp3',
        art: 'Caratulas de lo beats/Beat 2025 verano trap.png'
    },
    {
        title: 'Beat Rellax Reggaeton',
        genre: 'Reggaeton Relax',
        src: 'BEATS/BEAT RELLAX REGGEATON.mp3',
        art: 'Caratulas de lo beats/beat rellax reggeaton.png'
    },
    {
        title: 'Beat Hip Hop Piano Gigant',
        genre: 'Hip Hop',
        src: 'BEATS/BEAT HIP HOP PIANO GIGANT.mp3',
        art: 'Caratulas de lo beats/beat hip hop piano gigant.jpg'
    },
    {
        title: 'Beat Sin Frontera',
        genre: 'Instrumental',
        src: 'BEATS/BEAT SIN FRONTERA.mp3',
        art: 'Caratulas de lo beats/beat sin frontera.png'
    },
    {
        title: 'Beat Trap Navideño Chilling',
        genre: 'Trap Navideño',
        src: 'BEATS/BEAT TRAP NAVIDEÑO CHILLING.mp3',
        art: 'Caratulas de lo beats/beat trap navideño chilling.png'
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

    // Update waveform progress overlay
    if (duration > 0) {
        progressOverlay.style.width = progressPercent + '%';
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

function drawWaveform() {
    const canvas = waveformCanvas;
    const ctx = canvasContext;
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    const barWidth = width / waveformData.length;
    const maxAmplitude = Math.max(...waveformData);

    ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';

    waveformData.forEach((amplitude, index) => {
        const barHeight = (amplitude / maxAmplitude) * height * 0.8;
        const x = index * barWidth;
        const y = (height - barHeight) / 2;

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

document.querySelectorAll('.play-btn').forEach((btn, index) => {
    btn.addEventListener('click', () => {
        currentTrackIndex = index;
        loadTrack(currentTrackIndex);
        playTrack();
    });
});

function buyBeat(beatName) {
    // Redirigir a la página de login para completar la compra
    window.location.href = 'login.html?beat=' + encodeURIComponent(beatName);
}

function buyCurrentBeat() {
    const currentBeat = tracks[currentTrackIndex];
    buyBeat(currentBeat.title);
}

// Event listener para el botón de compra en el reproductor
document.getElementById('buy-current-btn').addEventListener('click', buyCurrentBeat);

// Event listener para clicks en la waveform
waveformContainer.addEventListener('click', setWaveformProgress);

// Cargar la primera pista al inicio
loadTrack(currentTrackIndex);
