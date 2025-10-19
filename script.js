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

// Cargar la primera pista al inicio
loadTrack(currentTrackIndex);
