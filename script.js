// @ts-nocheck
// Majestic Beats — catálogo, reproductor y compra.

const CONTACT_EMAIL = 'altorangofilms@gmail.com';

// Catálogo local. Si el servidor responde en /api/beats se usa su lista
// (precio, género y disponibilidad); el audio y las carátulas siempre salen de aquí.
// El audio público es un adelanto de 45 segundos: los MP3 completos no están en el sitio.
const tracksFallback = [
    {
        title: 'Beat Verano Reggaeton',
        genre: 'Reggaeton',
        src: 'previews/verano-reggaeton.mp3',
        art: 'covers/verano-reggaeton.webp',
        price: '$20.000 CLP'
    },
    {
        title: 'Beat 2025 Verano Trap',
        genre: 'Trap',
        src: 'previews/verano-trap-2025.mp3',
        art: 'covers/verano-trap-2025.webp',
        price: '$25.000 CLP'
    },
    {
        title: 'Beat Rellax Reggaeton',
        genre: 'Reggaeton Relax',
        src: 'previews/rellax-reggaeton.mp3',
        art: 'covers/rellax-reggaeton.webp',
        price: '$22.000 CLP'
    },
    {
        title: 'Beat Hip Hop Piano Gigant',
        genre: 'Hip Hop',
        src: 'previews/hip-hop-piano-gigant.mp3',
        art: 'covers/hip-hop-piano-gigant.webp',
        price: '$28.000 CLP'
    },
    {
        title: 'Beat Sin Frontera',
        genre: 'Instrumental',
        src: 'previews/sin-frontera.mp3',
        art: 'covers/sin-frontera.webp',
        price: '$30.000 CLP'
    },
    {
        title: 'Beat Trap Navideño Chilling',
        genre: 'Trap Navideño',
        src: 'previews/trap-navideno-chilling.mp3',
        art: 'covers/trap-navideno-chilling.webp',
        price: '$26.000 CLP'
    }
];

const GENRE_FAMILIES = ['Reggaeton', 'Trap', 'Hip Hop', 'Instrumental'];

const $ = (id) => document.getElementById(id);
const audioPlayer = $('audio-player');
const playPauseBtn = $('play-pause-btn');
const prevBtn = $('prev-btn');
const nextBtn = $('next-btn');
const volumeBar = $('volume-bar');
const muteBtn = $('mute-btn');
const currentTimeEl = $('current-time');
const durationEl = $('duration');
const currentTitle = $('current-title');
const currentGenre = $('current-genre');
const currentArt = $('current-art');
const waveformCanvas = $('waveform-canvas');
const waveformContainer = $('waveform-container');
const trackList = $('track-list');
const filtersEl = $('filters');
const heroPlayBtn = $('hero-play');
const heroPlayLabel = $('hero-play-label');
const buyCurrentBtn = $('buy-current-btn');
const buyCurrentPrice = $('buy-current-price');
const buyDialog = $('buy-dialog');
const toastEl = $('toast');

let tracks = [];
let apiOnline = false;
let currentTrackIndex = 0;
let trackLoaded = false;
let activeFilter = 'Todos';
let previousVolume = 1;

// ---------- Utilidades ----------
function formatTime(time) {
    if (!Number.isFinite(time) || time < 0) return '0:00';
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

function displayName(title) {
    return title.replace(/^Beat\s+/i, '');
}

function shortPrice(price) {
    return String(price).replace(/\s*CLP$/i, '');
}

function genreFamily(genre) {
    return GENRE_FAMILIES.find((g) => genre.toLowerCase().includes(g.toLowerCase())) || genre;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

let toastTimer;
function showToast(message) {
    toastEl.textContent = message;
    toastEl.classList.add('is-visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove('is-visible'), 4200);
}

// ---------- Carga del catálogo ----------
async function loadTracksFromApi() {
    try {
        const resp = await fetch('/api/beats');
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const data = await resp.json();
        const byTitle = new Map(tracksFallback.map((t) => [t.title, t]));

        tracks = (data.beats || [])
            .map((b) => {
                const local = byTitle.get(b.name);
                if (!local) return null;
                return { ...local, genre: b.genre || local.genre, price: b.price || local.price };
            })
            .filter(Boolean);
        apiOnline = true;
    } catch (e) {
        // Sitio estático (por ejemplo GitHub Pages): se muestra el catálogo local.
        tracks = tracksFallback.slice();
        apiOnline = false;
    }
}

function renderFilters() {
    const families = ['Todos', ...GENRE_FAMILIES.filter((g) => tracks.some((t) => genreFamily(t.genre) === g))];
    filtersEl.innerHTML = '';
    if (families.length <= 2) return;

    families.forEach((family) => {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'chip';
        chip.textContent = family;
        chip.setAttribute('aria-pressed', String(family === activeFilter));
        chip.addEventListener('click', () => {
            activeFilter = family;
            renderFilters();
            renderTracks();
        });
        filtersEl.appendChild(chip);
    });
}

function renderTracks() {
    trackList.innerHTML = '';

    if (tracks.length === 0) {
        trackList.innerHTML = '<p class="empty">Todos los beats se vendieron. Vuelve pronto: subimos beats nuevos cada cierto tiempo.</p>';
        return;
    }

    tracks.forEach((beat, index) => {
        if (activeFilter !== 'Todos' && genreFamily(beat.genre) !== activeFilter) return;

        const name = escapeHtml(displayName(beat.title));
        const card = document.createElement('article');
        card.className = 'track';
        card.dataset.index = String(index);
        card.innerHTML = `
            <button type="button" class="track-cover play-btn" aria-label="Reproducir ${name}">
                <img src="${beat.art}" alt="Carátula de ${name}" width="720" height="720" loading="lazy">
                <span class="track-cover-btn" aria-hidden="true">
                    <svg class="icon icon-play" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                    <svg class="icon icon-pause" viewBox="0 0 24 24"><path d="M6 5h4v14H6zm8 0h4v14h-4z"/></svg>
                </span>
            </button>
            <div class="track-body">
                <div>
                    <h3>${name}</h3>
                    <p class="track-genre">${escapeHtml(beat.genre)}</p>
                </div>
                <p class="track-price">${escapeHtml(beat.price)}</p>
            </div>
            <button type="button" class="neon-btn buy-btn">Comprar</button>
        `;

        card.querySelector('.play-btn').addEventListener('click', () => togglePlay(index));
        card.querySelector('.buy-btn').addEventListener('click', () => buyBeat(beat.title));
        trackList.appendChild(card);
    });

    syncPlayingState();
}

// ---------- Reproductor ----------
function loadTrack(index) {
    const track = tracks[index];
    if (!track) return;

    currentTrackIndex = index;
    trackLoaded = true;
    audioPlayer.src = track.src;
    audioPlayer.load();
    showTrackInfo(track);
    loadWaveform(track);
}

function showTrackInfo(track) {
    currentTitle.textContent = displayName(track.title);
    currentGenre.textContent = track.genre;
    currentArt.src = track.art;
    buyCurrentPrice.textContent = shortPrice(track.price);
    $('stage-cover').src = track.art;
    $('vinyl-label').src = track.art;
    currentTimeEl.textContent = '0:00';
    durationEl.textContent = '0:00';
}

function playTrack() {
    const attempt = audioPlayer.play();
    if (attempt && attempt.catch) {
        attempt.catch((error) => {
            if (error.name !== 'AbortError') showToast('No se pudo reproducir este beat. Intenta de nuevo.');
        });
    }
}

function pauseTrack() {
    audioPlayer.pause();
}

function togglePlay(index = currentTrackIndex) {
    if (tracks.length === 0) return;

    if (!trackLoaded || index !== currentTrackIndex) {
        loadTrack(index);
        playTrack();
    } else if (audioPlayer.paused) {
        playTrack();
    } else {
        pauseTrack();
    }
}

function stepTrack(direction) {
    if (tracks.length === 0) return;
    const next = (currentTrackIndex + direction + tracks.length) % tracks.length;
    loadTrack(next);
    playTrack();
}

function syncPlayingState() {
    const playing = trackLoaded && !audioPlayer.paused;
    document.body.classList.toggle('is-playing', playing);
    playPauseBtn.setAttribute('aria-label', playing ? 'Pausar' : 'Reproducir');
    heroPlayLabel.textContent = playing ? 'Pausar' : trackLoaded ? 'Seguir escuchando' : 'Escuchar ahora';

    trackList.querySelectorAll('.track').forEach((card) => {
        const isCurrent = trackLoaded && Number(card.dataset.index) === currentTrackIndex;
        card.classList.toggle('is-current', isCurrent);
        card.classList.toggle('is-playing', isCurrent && playing);
        const name = displayName(tracks[Number(card.dataset.index)].title);
        card.querySelector('.play-btn').setAttribute('aria-label', (isCurrent && playing ? 'Pausar ' : 'Reproducir ') + name);
    });
}

function progressPercent() {
    const { currentTime, duration } = audioPlayer;
    return duration > 0 ? (currentTime / duration) * 100 : 0;
}

function updateProgress() {
    currentTimeEl.textContent = formatTime(audioPlayer.currentTime);
    durationEl.textContent = formatTime(audioPlayer.duration);
    waveformContainer.setAttribute('aria-valuenow', String(Math.round(progressPercent())));
    waveformContainer.setAttribute('aria-valuetext', `${formatTime(audioPlayer.currentTime)} de ${formatTime(audioPlayer.duration)}`);
    drawWaveform();
}

// ---------- Onda de audio ----------
const canvasContext = waveformCanvas.getContext('2d');
const waveformCache = new Map();
let waveformData = [];
let waveformRequest = 0;
let audioContext = null;

// Onda provisional (misma forma siempre para el mismo beat) mientras se analiza el audio.
function placeholderWaveform(seedText, bars = 160) {
    let seed = 0;
    for (const ch of seedText) seed = (seed * 31 + ch.charCodeAt(0)) >>> 0;
    const data = [];
    for (let i = 0; i < bars; i++) {
        seed = (seed * 1664525 + 1013904223) >>> 0;
        const noise = seed / 4294967295;
        const envelope = 0.55 + 0.45 * Math.sin((i / bars) * Math.PI);
        data.push((0.3 + 0.7 * noise) * envelope);
    }
    return data;
}

function computeWaveform(buffer, bars = 160) {
    const raw = buffer.getChannelData(0);
    const blockSize = Math.floor(raw.length / bars) || 1;
    const stride = Math.max(1, Math.floor(blockSize / 400)); // muestreo: suficiente para dibujar
    const data = [];
    for (let i = 0; i < bars; i++) {
        const start = blockSize * i;
        let sum = 0;
        let count = 0;
        for (let j = 0; j < blockSize; j += stride) {
            sum += Math.abs(raw[start + j] || 0);
            count++;
        }
        data.push(sum / count);
    }
    return data;
}

async function loadWaveform(track) {
    const request = ++waveformRequest;

    if (waveformCache.has(track.src)) {
        waveformData = waveformCache.get(track.src);
        drawWaveform();
        return;
    }

    waveformData = placeholderWaveform(track.title);
    drawWaveform();

    try {
        const response = await fetch(track.src);
        const arrayBuffer = await response.arrayBuffer();
        audioContext = audioContext || new (window.AudioContext || window.webkitAudioContext)();
        const buffer = await audioContext.decodeAudioData(arrayBuffer);
        const data = computeWaveform(buffer);
        waveformCache.set(track.src, data);
        if (request === waveformRequest) {
            waveformData = data;
            drawWaveform();
        }
    } catch (error) {
        // Se mantiene la onda provisional; el audio se reproduce igual.
        console.warn('No se pudo analizar la onda:', error);
    }
}

function resizeCanvas() {
    const ratio = window.devicePixelRatio || 1;
    const rect = waveformContainer.getBoundingClientRect();
    waveformCanvas.width = Math.max(1, Math.round(rect.width * ratio));
    waveformCanvas.height = Math.max(1, Math.round(rect.height * ratio));
    drawWaveform();
}

function drawWaveform() {
    const ctx = canvasContext;
    const { width, height } = waveformCanvas;
    ctx.clearRect(0, 0, width, height);
    if (waveformData.length === 0 || width < 2) return;

    const ratio = window.devicePixelRatio || 1;
    const step = 4 * ratio; // 3px de barra + 1px de separación
    const bars = Math.max(1, Math.floor(width / step));
    const max = Math.max(...waveformData) || 1;
    const playedX = (progressPercent() / 100) * width;

    const played = ctx.createLinearGradient(0, 0, width, 0);
    played.addColorStop(0, '#ff9a3d');
    played.addColorStop(1, '#ff3d8b');

    for (let i = 0; i < bars; i++) {
        const sample = waveformData[Math.floor((i / bars) * waveformData.length)] / max;
        const barHeight = Math.max(2 * ratio, sample * height * 0.92);
        const x = i * step;
        ctx.fillStyle = x < playedX ? played : 'rgba(255, 244, 230, 0.26)';
        ctx.fillRect(x, (height - barHeight) / 2, 3 * ratio, barHeight);
    }
}

function seekFromPointer(event) {
    if (!trackLoaded || !(audioPlayer.duration > 0)) return;
    const rect = waveformContainer.getBoundingClientRect();
    const fraction = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width));
    audioPlayer.currentTime = fraction * audioPlayer.duration;
    updateProgress();
}

// ---------- Compra ----------
function openBuyDialog(beatName) {
    const name = displayName(beatName);
    $('buy-dialog-beat').textContent = name;
    $('buy-dialog-mail').href =
        `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent('Quiero comprar el beat ' + name)}` +
        `&body=${encodeURIComponent('Hola, quiero comprar el beat "' + name + '". ¿Cómo puedo pagarlo?')}`;
    buyDialog.showModal();
}

async function buyBeat(beatName) {
    const beat = tracks.find((t) => t.title === beatName);
    if (!beat) return;

    // Sin servidor de pagos (sitio estático) se ofrece reservar por correo.
    if (!apiOnline) {
        openBuyDialog(beatName);
        return;
    }

    try {
        const stockResp = await fetch('/api/check_stock/' + encodeURIComponent(beatName));
        if (stockResp.status === 404) {
            showToast('Este beat ya no está disponible.');
            return;
        }
        if (!stockResp.ok) throw new Error('HTTP ' + stockResp.status);
        const stock = await stockResp.json();
        if (!stock.available) {
            showToast('Este beat ya se vendió.');
            return;
        }
    } catch (e) {
        console.error(e);
        openBuyDialog(beatName);
        return;
    }

    const token = localStorage.getItem('auth_token');
    const page = token ? 'checkout.html' : 'login.html';
    window.location.href = page + '?beat=' + encodeURIComponent(beatName);
}

// ---------- Sesión ----------
function setupSession() {
    const loginLink = $('login-link');
    const logoutBtn = $('logout-btn');
    const hasToken = Boolean(localStorage.getItem('auth_token'));

    // Iniciar sesión solo tiene sentido cuando el servidor está disponible.
    loginLink.hidden = !apiOnline || hasToken;
    logoutBtn.hidden = !hasToken;

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('auth_token');
        logoutBtn.hidden = true;
        loginLink.hidden = !apiOnline;
        showToast('Cerraste sesión.');
    });
}

// ---------- Eventos ----------
playPauseBtn.addEventListener('click', () => togglePlay());
heroPlayBtn.addEventListener('click', () => togglePlay());
prevBtn.addEventListener('click', () => stepTrack(-1));
nextBtn.addEventListener('click', () => stepTrack(1));
buyCurrentBtn.addEventListener('click', () => {
    const beat = tracks[currentTrackIndex];
    if (beat) buyBeat(beat.title);
});

audioPlayer.addEventListener('play', syncPlayingState);
audioPlayer.addEventListener('pause', syncPlayingState);
audioPlayer.addEventListener('timeupdate', updateProgress);
audioPlayer.addEventListener('loadedmetadata', updateProgress);
audioPlayer.addEventListener('ended', () => stepTrack(1));
audioPlayer.addEventListener('error', () => {
    if (trackLoaded) showToast('No se pudo cargar el audio de este beat.');
});

volumeBar.addEventListener('input', (e) => {
    audioPlayer.volume = Number(e.target.value);
    document.body.classList.toggle('is-muted', audioPlayer.volume === 0);
});

muteBtn.addEventListener('click', () => {
    if (audioPlayer.volume === 0) {
        audioPlayer.volume = previousVolume || 1;
    } else {
        previousVolume = audioPlayer.volume;
        audioPlayer.volume = 0;
    }
    volumeBar.value = String(audioPlayer.volume);
    const muted = audioPlayer.volume === 0;
    document.body.classList.toggle('is-muted', muted);
    muteBtn.setAttribute('aria-label', muted ? 'Activar sonido' : 'Silenciar');
});

let seeking = false;
waveformContainer.addEventListener('pointerdown', (e) => {
    seeking = true;
    waveformContainer.setPointerCapture(e.pointerId);
    seekFromPointer(e);
});
waveformContainer.addEventListener('pointermove', (e) => {
    if (seeking) seekFromPointer(e);
});
waveformContainer.addEventListener('pointerup', () => {
    seeking = false;
});
waveformContainer.addEventListener('pointercancel', () => {
    seeking = false;
});
waveformContainer.addEventListener('keydown', (e) => {
    if (!(audioPlayer.duration > 0)) return;
    if (e.key === 'ArrowRight') audioPlayer.currentTime = Math.min(audioPlayer.duration, audioPlayer.currentTime + 5);
    else if (e.key === 'ArrowLeft') audioPlayer.currentTime = Math.max(0, audioPlayer.currentTime - 5);
    else return;
    e.preventDefault();
});

// Barra espaciadora: reproducir o pausar (salvo al escribir o sobre un botón).
document.addEventListener('keydown', (e) => {
    if (e.code !== 'Space' || buyDialog.open) return;
    const tag = e.target.tagName;
    if (['INPUT', 'TEXTAREA', 'BUTTON', 'A', 'SUMMARY', 'SELECT'].includes(tag)) return;
    e.preventDefault();
    togglePlay();
});

$('buy-dialog-close').addEventListener('click', () => buyDialog.close());
buyDialog.addEventListener('click', (e) => {
    if (e.target === buyDialog) buyDialog.close(); // clic fuera del cuadro
});

window.addEventListener('resize', resizeCanvas);

// ---------- Inicio ----------
document.addEventListener('DOMContentLoaded', async () => {
    await loadTracksFromApi();
    renderFilters();
    renderTracks();
    setupSession();

    if (tracks.length > 0) {
        // Se muestra el primer beat, pero su audio no se descarga hasta que se pulse reproducir.
        showTrackInfo(tracks[0]);
        waveformData = placeholderWaveform(tracks[0].title);
    }
    resizeCanvas();
});
