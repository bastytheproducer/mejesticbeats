// Panel para subir los MP3 completos. La clave no se guarda: se pide en cada visita.
const beatsEl = document.getElementById('beats');
const messageEl = document.getElementById('admin-message');
let adminToken = '';

async function loadBeats() {
    const resp = await fetch('/api/admin/beats', { headers: { 'X-Admin-Token': adminToken } });
    if (resp.status === 401) {
        beatsEl.innerHTML = '';
        messageEl.textContent = 'Clave incorrecta.';
        return;
    }
    const data = await resp.json();
    messageEl.textContent = '';
    beatsEl.innerHTML = '';

    data.beats.forEach((beat) => {
        const row = document.createElement('div');
        row.className = 'admin-row';

        const title = document.createElement('h3');
        title.textContent = beat.name;

        const state = document.createElement('p');
        state.className = 'admin-state' + (beat.uploaded ? ' ok' : '');
        state.textContent =
            (beat.uploaded ? 'MP3 completo en el servidor' : 'Falta subir el MP3 completo') +
            (beat.sold ? ` · Vendido a ${beat.buyer_email}` : ' · A la venta');

        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.mp3,audio/mpeg';
        input.setAttribute('aria-label', `MP3 completo de ${beat.name}`);
        input.addEventListener('change', () => uploadBeat(beat.name, input.files[0]));

        row.append(title, state, input);
        beatsEl.appendChild(row);
    });
}

async function uploadBeat(name, file) {
    if (!file) return;
    messageEl.textContent = `Subiendo ${name}…`;
    const body = new FormData();
    body.append('beat', name);
    body.append('file', file);

    try {
        const resp = await fetch('/api/admin/upload_beat', {
            method: 'POST',
            headers: { 'X-Admin-Token': adminToken },
            body
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error || 'No se pudo subir');
        await loadBeats();
        messageEl.textContent = `${name}: MP3 guardado.`;
    } catch (error) {
        messageEl.textContent = `${name}: ${error.message}.`;
    }
}

document.getElementById('tokenForm').addEventListener('submit', (event) => {
    event.preventDefault();
    adminToken = document.getElementById('adminToken').value;
    loadBeats();
});
