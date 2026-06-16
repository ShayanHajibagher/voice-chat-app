const socket = io({
    transports: ['websocket', 'polling'],
});

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let stream = null;
let currentTheme = 'dark';
let lastResponse = '';
let audioCtx = null;

const $ = (id) => document.getElementById(id);
const messagesEl = $('messages');
const recordBtn = $('record-btn');
const statusDot = $('status-dot');
const statusText = $('status-text');
const toast = $('toast');
const waveform = $('waveform');
const waveformCtx = waveform?.getContext('2d');
const waveformContainer = $('waveform-container');

// ---- SocketIO Events ----

socket.on('connect', () => {
    statusDot.classList.add('connected');
    statusText.textContent = 'Connected';
});

socket.on('disconnect', () => {
    statusDot.classList.remove('connected');
    statusText.textContent = 'Disconnected';
});

socket.on('status', (data) => {
    if (data.mode === 'processing') { statusText.textContent = 'Processing...'; return; }
    if (data.mode === 'idle') statusText.textContent = 'Ready';
    if (data.language && $('language-select')) $('language-select').value = data.language;
    if (data.volume !== undefined) {
        if ($('volume-slider')) $('volume-slider').value = data.volume;
        if ($('volume-value')) $('volume-value').textContent = data.volume.toFixed(1);
    }
    if (data.speed !== undefined) {
        if ($('speed-slider')) $('speed-slider').value = data.speed;
        if ($('speed-value')) $('speed-value').textContent = data.speed.toFixed(2);
    }
    if (data.stats) {
        statusText.textContent = 'Ready';
        if ($('stat-user-msgs')) $('stat-user-msgs').textContent = data.stats.user_messages || 0;
        if ($('stat-ai-msgs')) $('stat-ai-msgs').textContent = data.stats.ai_messages || 0;
        if ($('stat-words')) $('stat-words').textContent = data.stats.words_spoken || 0;
        if ($('stat-time')) {
            const m = Math.floor((data.stats.elapsed || 0) / 60);
            const s = (data.stats.elapsed || 0) % 60;
            $('stat-time').textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        }
    }
});

socket.on('config', (data) => {
    if (data.stt_backend && $('stt-backend')) $('stt-backend').value = data.stt_backend;
    if (data.whisper_model && $('whisper-model')) $('whisper-model').value = data.whisper_model;
    if (data.api_url !== undefined && $('api-url')) $('api-url').value = data.api_url;
    if (data.api_key !== undefined && $('api-key')) $('api-key').value = data.api_key;
    if (data.language && $('language-select')) $('language-select').value = data.language;
    if ($('backend-badge')) $('backend-badge').textContent = data.stt_backend || 'whisper';

    if (data.tts_voices) {
        if (data.tts_voices.en && $('tts-voice-en')) {
            const v = data.tts_voices.en.model_path.replace('.onnx', '');
            $('tts-voice-en').value = v;
        }
        if (data.tts_voices.fa && $('tts-voice-fa')) {
            const v = data.tts_voices.fa.model_path.replace('.onnx', '');
            $('tts-voice-fa').value = v;
        }
    }
});

socket.on('conversation', (data) => {
    renderMessages(data.messages || []);
});

socket.on('response', (data) => {
    if (data.text) lastResponse = data.text;
    if (data.audio) playAudio(data.audio);
});

socket.on('notify', (data) => {
    showToast(data.message || '', data.type || 'info');
});

socket.on('error', (data) => {
    showToast(data.message || 'An error occurred', 'error');
});

// ---- Audio Recording ----

async function toggleRecording() {
    if (isRecording) { stopRecording(); }
    else { await startRecording(); }
}

async function startRecording() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true }
        });
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
        audioChunks = [];
        mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
        mediaRecorder.onstop = async () => {
            const webmBlob = new Blob(audioChunks, { type: 'audio/webm' });
            try {
                if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const buf = await webmBlob.arrayBuffer();
                const audioBuf = await audioCtx.decodeAudioData(buf);
                const wavBlob = encodeWAV(audioBuf.getChannelData(0), audioBuf.sampleRate);
                sendAudio(wavBlob);
            } catch (_) {
                showToast('Audio format conversion failed', 'error');
                statusText.textContent = 'Ready';
            }
            if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
        };
        mediaRecorder.start();
        isRecording = true;
        recordBtn.classList.add('recording');
        recordBtn.querySelector('.mic-icon').textContent = '\u23F9';
        showToast('Recording... speak now');
        waveformContainer.style.display = 'flex';
        drawWaveform();
    } catch (err) {
        showToast('Microphone access denied: ' + err.message, 'error');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        recordBtn.classList.remove('recording');
        recordBtn.querySelector('.mic-icon').textContent = '\uD83C\uDFA4';
        waveformContainer.style.display = 'none';
        statusText.textContent = 'Processing...';
    }
}

function sendAudio(blob) {
    const reader = new FileReader();
    reader.onloadend = () => {
        socket.emit('audio', { audio: reader.result.split(',')[1] });
    };
    reader.readAsDataURL(blob);
}

function playAudio(base64Audio) {
    const audio = new Audio('data:audio/wav;base64,' + base64Audio);
    audio.play().catch(err => showToast('Audio playback error: ' + err.message, 'error'));
}

function encodeWAV(samples, sampleRate) {
    // Resample to 16kHz to avoid artifacts (Whisper expects 16kHz input)
    const targetRate = 16000;
    let data = samples;
    if (sampleRate !== targetRate) {
        const ratio = targetRate / sampleRate;
        const newLen = Math.round(samples.length * ratio);
        data = new Float32Array(newLen);
        for (let i = 0; i < newLen; i++) {
            const src = i / ratio;
            const lo = Math.floor(src);
            const hi = Math.min(lo + 1, samples.length - 1);
            const frac = src - lo;
            data[i] = samples[lo] + (samples[hi] - samples[lo]) * frac;
        }
    }

    const len = data.length;
    const buf = new ArrayBuffer(44 + len * 2);
    const v = new DataView(buf);

    function w(off, str) { for (let i = 0; i < str.length; i++) v.setUint8(off + i, str.charCodeAt(i)); }

    w(0, 'RIFF');
    v.setUint32(4, 36 + len * 2, true);
    w(8, 'WAVE');
    w(12, 'fmt ');
    v.setUint32(16, 16, true);
    v.setUint16(20, 1, true);
    v.setUint16(22, 1, true);
    v.setUint32(24, targetRate, true);
    v.setUint32(28, targetRate * 2, true);
    v.setUint16(32, 2, true);
    v.setUint16(34, 16, true);
    w(36, 'data');
    v.setUint32(40, len * 2, true);

    for (let i = 0, o = 44; i < len; i++, o += 2) {
        const s = Math.max(-1, Math.min(1, data[i]));
        v.setInt16(o, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    return new Blob([buf], { type: 'audio/wav' });
}

// ---- Waveform ----

let animFrame = null;

function drawWaveform() {
    if (!waveformCtx) return;
    const w = waveform.width;
    const h = waveform.height;
    const bars = 60;

    function draw() {
        if (!isRecording) return;
        waveformCtx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--bg-tertiary').trim() || '#252530';
        waveformCtx.fillRect(0, 0, w, h);
        for (let i = 0; i < bars; i++) {
            const barH = Math.random() * h * 0.8 + 4;
            const x = (w / bars) * i + 2;
            const bw = w / bars - 4;
            const gradient = waveformCtx.createLinearGradient(x, h, x, h - barH);
            gradient.addColorStop(0, '#6c5ce7');
            gradient.addColorStop(1, '#a29bfe');
            waveformCtx.fillStyle = gradient;
            waveformCtx.beginPath();
            waveformCtx.roundRect(x, h - barH, bw, barH, [2, 2, 0, 0]);
            waveformCtx.fill();
        }
        animFrame = requestAnimationFrame(draw);
    }
    draw();
}

// ---- Render Messages ----

function renderMessages(messages) {
    if (!messages || messages.length === 0) {
        messagesEl.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">\uD83C\uDFA4</div>
                <h3>Ready to talk</h3>
                <p>Press the mic button and start speaking</p>
            </div>
        `;
        return;
    }
    messagesEl.innerHTML = '';
    messages.forEach((msg) => {
        const div = document.createElement('div');
        div.className = `message ${msg.role}`;
        const label = document.createElement('div');
        label.className = 'msg-label';
        label.textContent = msg.role === 'user' ? 'You' : 'AI Assistant';
        const bubble = document.createElement('div');
        bubble.className = 'msg-bubble';
        bubble.textContent = msg.content;
        const time = document.createElement('div');
        time.className = 'msg-time';
        time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        div.appendChild(label);
        div.appendChild(bubble);
        div.appendChild(time);
        messagesEl.appendChild(div);
    });
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

// ---- View Switching ----

function switchView(view) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    const v = document.getElementById('view-' + view);
    if (v) v.classList.add('active');
    const btn = document.querySelector(`.nav-btn[data-view="${view}"]`);
    if (btn) btn.classList.add('active');
}

// ---- Commands ----

function changeLanguage(lang) {
    socket.emit('command', { command: 'language', language: lang });
    showToast(`Switched to ${lang === 'en' ? 'English' : 'Persian'}`);
}

function changeVolume(val) {
    socket.emit('command', { command: 'volume', value: parseFloat(val) });
}

function changeSpeed(val) {
    socket.emit('command', { command: 'speed', value: parseFloat(val) });
}

function setApiUrl(val) {
    socket.emit('command', { command: 'set_api_url', value: val });
}

function setApiKey(val) {
    socket.emit('command', { command: 'set_api_key', value: val });
}

function setSttBackend(val) {
    socket.emit('command', { command: 'set_stt_backend', value: val });
}

function setWhisperModel(val) {
    socket.emit('command', { command: 'set_whisper_model', value: val });
}

function setTtsVoice(lang, val) {
    const model_path = val + '.onnx';
    const config_path = val + '.onnx.json';
    socket.emit('command', { command: 'set_tts_voice', lang, model_path, config_path });
}

function downloadModels() {
    socket.emit('command', { command: 'download_models' });
}

function clearConversation() {
    if (confirm('Clear all messages?')) {
        socket.emit('command', { command: 'clear' });
    }
}

function saveConversation() {
    socket.emit('command', { command: 'save' });
    showToast('Conversation saved');
}

function copyLastResponse() {
    if (!lastResponse) {
        showToast('No AI response to copy', 'warning');
        return;
    }
    navigator.clipboard.writeText(lastResponse).then(() => {
        showToast('Copied to clipboard');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}

function exportJSON() {
    window.open('/export/json', '_blank');
}

function exportText() {
    window.open('/export/text', '_blank');
}

// ---- Theme ----

function toggleTheme() {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);
    if ($('theme-icon')) $('theme-icon').textContent = currentTheme === 'dark' ? '\uD83C\uDF19' : '\u2600\uFE0F';
    if ($('theme-label')) $('theme-label').textContent = currentTheme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
}

// ---- Toast ----

function showToast(msg, type = 'info') {
    toast.textContent = msg;
    toast.className = 'toast';
    if (type !== 'info') toast.classList.add(type);
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3500);
}

// ---- Keyboard Shortcuts ----

document.addEventListener('keydown', (e) => {
    if (e.key === ' ' && e.target === document.body) {
        e.preventDefault();
        toggleRecording();
    }
});
