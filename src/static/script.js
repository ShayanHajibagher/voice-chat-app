let socket = null;
let authToken = localStorage.getItem('auth_token');
let currentUsername = '';
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let stream = null;
let currentTheme = localStorage.getItem('theme') || 'dark';
let lastResponse = '';
let audioCtx = null;
let analyserNode = null;
let animFrameId = null;
let conversationsCache = [];
let currentMemoryTab = 'memory';
let streamingMsgEl = null;
let currentSessionId = '';

const $ = (id) => document.getElementById(id);

// ---- Auth ----

function showLogin() {
    $('login-form').style.display = 'block';
    $('signup-form').style.display = 'none';
    $('login-error').textContent = '';
    $('signup-error').textContent = '';
    if ($('auth-subtitle')) $('auth-subtitle').textContent = 'Sign in to your account';
}

function showSignup() {
    $('login-form').style.display = 'none';
    $('signup-form').style.display = 'block';
    $('login-error').textContent = '';
    $('signup-error').textContent = '';
    if ($('auth-subtitle')) $('auth-subtitle').textContent = 'Create a new account';
}

async function doLogin() {
    const username = $('login-username').value.trim();
    const password = $('login-password').value;
    const btn = $('login-btn');
    const errEl = $('login-error');
    if (!username || !password) { errEl.textContent = 'Fill in all fields'; return; }
    btn.disabled = true;
    btn.textContent = 'Signing in...';
    try {
        const resp = await fetch('/api/login', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await resp.json();
        if (data.success) {
            authToken = data.token;
            currentUsername = data.username;
            localStorage.setItem('auth_token', authToken);
            initApp();
        } else {
            errEl.textContent = data.error || 'Login failed';
        }
    } catch (e) {
        errEl.textContent = 'Connection error: ' + e.message;
    }
    btn.disabled = false;
    btn.textContent = 'Sign In';
}

async function doSignup() {
    const username = $('signup-username').value.trim();
    const password = $('signup-password').value;
    const confirm = $('signup-confirm').value;
    const btn = $('signup-btn');
    const errEl = $('signup-error');
    if (!username || !password) { errEl.textContent = 'Fill in all fields'; return; }
    if (password !== confirm) { errEl.textContent = 'Passwords do not match'; return; }
    if (password.length < 4) { errEl.textContent = 'Password must be at least 4 characters'; return; }
    btn.disabled = true;
    btn.textContent = 'Creating...';
    try {
        const resp = await fetch('/api/signup', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await resp.json();
        if (data.success) {
            authToken = data.token;
            currentUsername = data.username;
            localStorage.setItem('auth_token', authToken);
            initApp();
        } else {
            errEl.textContent = data.error || 'Signup failed';
        }
    } catch (e) {
        errEl.textContent = 'Connection error: ' + e.message;
    }
    btn.disabled = false;
    btn.textContent = 'Create Account';
}

async function deleteAccount() {
    if (!confirm('Are you sure you want to permanently delete your account? This will remove all your data and cannot be undone.')) return;
    if (!confirm('This is your final warning. Type "yes" to confirm.') || prompt('Type "yes" to confirm deletion:') !== 'yes') return;
    try {
        const resp = await fetch('/api/delete-account', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({token: authToken, username: currentUsername})
        });
        const data = await resp.json();
        if (data.success) {
            showNotification('Account deleted', 'success');
            if (socket) { socket.disconnect(); socket = null; }
            authToken = '';
            currentUsername = '';
            localStorage.removeItem('auth_token');
            $('app').style.display = 'none';
            $('auth-overlay').style.display = 'flex';
            showLogin();
        } else {
            showNotification('Failed to delete account: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (e) {
        showNotification('Connection error: ' + e.message, 'error');
    }
}

async function doLogout() {
    try {
        await fetch('/api/logout', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({token: authToken})
        });
    } catch (e) {}
    if (socket) { socket.disconnect(); socket = null; }
    authToken = '';
    currentUsername = '';
    localStorage.removeItem('auth_token');
    $('app').style.display = 'none';
    $('auth-overlay').style.display = 'flex';
    $('login-username').value = '';
    $('login-password').value = '';
    showLogin();
}

async function verifyAuth() {
    if (!authToken) return false;
    try {
        const resp = await fetch('/api/verify', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({token: authToken})
        });
        const data = await resp.json();
        if (data.success) {
            currentUsername = data.username;
            return true;
        }
    } catch (e) {}
    return false;
}

function initApp() {
    $('auth-overlay').style.display = 'none';
    $('app').style.display = 'flex';
    $('user-badge').textContent = '@' + currentUsername;
    initSocket();
}

function initSocket() {
    if (socket) socket.disconnect();
    socket = io({
        transports: ['websocket', 'polling'],
        auth: { token: authToken }
    });
    setupSocketEvents();
}

// ---- SocketIO Events ----

function setupSocketEvents() {

socket.on('connect', () => {
    $('status-dot').classList.add('connected');
    $('status-text').textContent = 'Connected';
});

socket.on('auth_ok', (data) => {
    currentUsername = data.username;
    $('user-badge').textContent = '@' + currentUsername;
    socket.emit('command', { command: 'list_conversations' });
});

socket.on('disconnect', () => {
    $('status-dot').classList.remove('connected');
    $('status-text').textContent = 'Disconnected';
});

socket.on('connect_error', (err) => {
    if (err.message === 'authentication error' || err.message?.includes('auth')) {
        localStorage.removeItem('auth_token');
        authToken = '';
        $('app').style.display = 'none';
        $('auth-overlay').style.display = 'flex';
        showLogin();
        $('login-error').textContent = 'Session expired. Please sign in again.';
    }
});

socket.on('status', (data) => {
    if (data.mode === 'processing') { $('status-text').textContent = 'Processing...'; return; }
    if (data.mode === 'idle') $('status-text').textContent = 'Ready';
    if (data.language && $('language-select')) {
        $('language-select').value = data.language;
        document.documentElement.dir = data.language === 'fa' ? 'rtl' : 'ltr';
    }
    if (data.volume !== undefined) {
        if ($('volume-slider')) $('volume-slider').value = data.volume;
        if ($('volume-value')) $('volume-value').textContent = data.volume.toFixed(1);
    }
    if (data.speed !== undefined) {
        if ($('speed-slider')) $('speed-slider').value = data.speed;
        if ($('speed-value')) $('speed-value').textContent = data.speed.toFixed(2);
    }
    if (data.stats) {
        $('status-text').textContent = 'Ready';
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
    if (data.language && $('language-select')) {
        $('language-select').value = data.language;
        document.documentElement.dir = data.language === 'fa' ? 'rtl' : 'ltr';
    }
    if ($('backend-badge')) $('backend-badge').textContent = data.stt_backend || 'whisper';
    if (data.custom_system_prompt !== undefined && $('system-prompt-editor')) {
        $('system-prompt-editor').value = data.custom_system_prompt;
    }
    if (data.username) {
        currentUsername = data.username;
        if ($('user-badge')) $('user-badge').textContent = '@' + currentUsername;
    }
    if (data.session_id) {
        currentSessionId = data.session_id;
        if ($('session-id-badge')) $('session-id-badge').textContent = data.session_id;
    }
    if (data.tts_voices) {
        if (data.tts_voices.en && $('tts-voice-en')) {
            $('tts-voice-en').value = data.tts_voices.en.model_path.replace('.onnx', '');
        }
        if (data.tts_voices.fa && $('tts-voice-fa')) {
            $('tts-voice-fa').value = data.tts_voices.fa.model_path.replace('.onnx', '');
        }
    }
});

socket.on('conversation', (data) => renderMessages(data.messages || []));
socket.on('user_text', (data) => showTypingIndicator(data.text));

socket.on('stream_chunk', (data) => {
    if (data.done) {
        if (streamingMsgEl) {
            streamingMsgEl.classList.remove('streaming-cursor');
            streamingMsgEl = null;
        }
        removeTypingIndicator();
        const aiMsgs = $('messages').querySelectorAll('.message.ai');
        const lastAi = aiMsgs[aiMsgs.length - 1];
        if (lastAi && !lastAi.querySelector('.msg-time')) {
            const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const timeDiv = document.createElement('div');
            timeDiv.className = 'msg-time';
            timeDiv.textContent = ts;
            lastAi.appendChild(timeDiv);
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'msg-actions';
            actionsDiv.innerHTML = `
                <button class="msg-action-btn" onclick="copyMessage(this)" title="Copy"><span class="msg-icon">\uD83D\uDCCB</span></button>
                <button class="msg-action-btn" onclick="speakMessage(this)" title="Listen"><span class="msg-icon">\uD83D\uDD0A</span></button>
                <button class="msg-action-btn" onclick="retryMessage()" title="Retry"><span class="msg-icon">\uD83D\uDD04</span></button>
                <button class="msg-action-btn" onclick="deleteMessage(-1)" title="Delete"><span class="msg-icon">\uD83D\uDDD1</span></button>`;
            lastAi.appendChild(actionsDiv);
        }
    } else {
        updateStreamingMessage(data.chunk);
    }
});

socket.on('response', (data) => {
    if (data.text) lastResponse = data.text;
    if (data.audio) playAudio(data.audio);
    removeTypingIndicator();
    if (data.text) re_enableSpeakButtons();
    if (data.text && document.hidden) {
        try {
            if (Notification.permission === 'granted') {
                new Notification('AI Voice Chat', { body: data.text.substring(0, 120) + (data.text.length > 120 ? '...' : '') });
            } else if (Notification.permission !== 'denied') {
                Notification.requestPermission();
            }
        } catch (e) {}
    }
});

socket.on('speak_audio', (data) => {
    if (data.audio) playAudio(data.audio);
    re_enableSpeakButtons();
});

socket.on('notify', (data) => showNotification(data.message || '', data.type || 'info'));
socket.on('error', (data) => { showNotification(data.message || 'An error occurred', 'error'); removeTypingIndicator(); });

socket.on('conversations', (data) => {
    conversationsCache = data.list || [];
    renderConversationList();
});

socket.on('memory_list', (data) => {
    renderMemoryEntries('memory', data.memory, data.memory_usage);
    renderMemoryEntries('user', data.user, data.user_usage);
});

socket.on('memory_raw', (data) => {
    if ($('memory-raw-text')) {
        $('memory-raw-text').value = data.content || '';
        $('memory-raw-text').dataset.target = data.target || 'memory';
    }
});

} // end setupSocketEvents

// ---- Check auth on load ----

(async function() {
    if (authToken && await verifyAuth()) {
        initApp();
    } else {
        localStorage.removeItem('auth_token');
        $('auth-overlay').style.display = 'flex';
        $('app').style.display = 'none';
    }
})();

// ---- Audio Recording ----

async function toggleRecording() {
    if (isRecording) stopRecording();
    else await startRecording();
}

async function startRecording() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true }
        });
        if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioCtx.createMediaStreamSource(stream);
        analyserNode = audioCtx.createAnalyser();
        analyserNode.fftSize = 256;
        source.connect(analyserNode);
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
        audioChunks = [];
        let recordingStart = Date.now();
        mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
        mediaRecorder.onstop = async () => {
            cancelAnimationFrame(animFrameId);
            const webmBlob = new Blob(audioChunks, { type: 'audio/webm' });
            try {
                const buf = await webmBlob.arrayBuffer();
                const audioBuf = await audioCtx.decodeAudioData(buf);
                const wavBlob = encodeWAV(audioBuf.getChannelData(0), audioBuf.sampleRate);
                sendAudio(wavBlob);
            } catch (_) {
                showNotification('Audio format conversion failed', 'error');
                $('status-text').textContent = 'Ready';
            }
            if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
            analyserNode = null;
            $('recording-timer').textContent = '0:00';
        };
        mediaRecorder.start();
        isRecording = true;
        $('record-btn').classList.add('recording');
        $('record-btn').querySelector('.mic-icon').textContent = '\u23F9';
        $('waveform-container').style.display = 'flex';
        drawRealWaveform();
        recordingStart = Date.now();
        const timerInterval = setInterval(() => {
            if (!isRecording) { clearInterval(timerInterval); return; }
            const elapsed = Math.floor((Date.now() - recordingStart) / 1000);
            const m = Math.floor(elapsed / 60);
            const s = elapsed % 60;
            $('recording-timer').textContent = `${m}:${String(s).padStart(2, '0')}`;
            if (elapsed >= 60) stopRecording();
        }, 200);
    } catch (err) {
        showNotification('Microphone access denied: ' + err.message, 'error');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        $('record-btn').classList.remove('recording');
        $('record-btn').querySelector('.mic-icon').textContent = '\uD83C\uDFA4';
        $('waveform-container').style.display = 'none';
        $('status-text').textContent = 'Processing...';
    }
}

function drawRealWaveform() {
    if (!waveformCtx || !analyserNode) return;
    const w = 400, h = 60;
    const bufferLength = analyserNode.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    function draw() {
        if (!isRecording || !analyserNode) return;
        animFrameId = requestAnimationFrame(draw);
        analyserNode.getByteTimeDomainData(dataArray);
        waveformCtx.fillStyle = '#252530';
        waveformCtx.fillRect(0, 0, w, h);
        const barCount = 60;
        const barWidth = (w / barCount) - 2;
        for (let i = 0; i < barCount; i++) {
            const sampleIndex = Math.floor(i * bufferLength / barCount);
            let sum = 0;
            for (let j = 0; j < 3 && sampleIndex + j < bufferLength; j++) sum += Math.abs(dataArray[sampleIndex + j] - 128);
            const avg = sum / 3;
            const barH = Math.max(2, (avg / 128) * h * 0.9);
            const x = (w / barCount) * i + 1;
            const gradient = waveformCtx.createLinearGradient(x, h, x, h - barH);
            gradient.addColorStop(0, '#6c5ce7');
            gradient.addColorStop(1, '#a29bfe');
            waveformCtx.fillStyle = gradient;
            waveformCtx.beginPath();
            if (waveformCtx.roundRect) waveformCtx.roundRect(x, h - barH, barWidth, barH, [2, 2, 0, 0]);
            else waveformCtx.rect(x, h - barH, barWidth, barH);
            waveformCtx.fill();
        }
    }
    draw();
}

const waveform = $('waveform');
const waveformCtx = waveform?.getContext('2d');

function sendAudio(blob) {
    const reader = new FileReader();
    reader.onloadend = () => socket.emit('audio', { audio: reader.result.split(',')[1] });
    reader.readAsDataURL(blob);
}

function playAudio(base64Audio) {
    new Audio('data:audio/wav;base64,' + base64Audio).play()
        .catch(err => showNotification('Audio playback error', 'error'));
}

function encodeWAV(samples, sampleRate) {
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
    w(0, 'RIFF'); v.setUint32(4, 36 + len * 2, true); w(8, 'WAVE');
    w(12, 'fmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true);
    v.setUint16(22, 1, true); v.setUint32(24, targetRate, true);
    v.setUint32(28, targetRate * 2, true); v.setUint16(32, 2, true);
    v.setUint16(34, 16, true); w(36, 'data'); v.setUint32(40, len * 2, true);
    for (let i = 0, o = 44; i < len; i++, o += 2) {
        const s = Math.max(-1, Math.min(1, data[i]));
        v.setInt16(o, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    return new Blob([buf], { type: 'audio/wav' });
}

// ---- Text Messaging ----

function onTextKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendTextMessage(); }
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function sendTextMessage() {
    const input = $('text-input');
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    input.style.height = 'auto';
    $('send-btn').disabled = true;
    socket.emit('text_message', { text, stream: true });
    setTimeout(() => { if ($('send-btn')) $('send-btn').disabled = false; }, 500);
}

// ---- Streaming ----

function showTypingIndicator(userText) {
    removeTypingIndicator();
    const es = $('empty-state');
    if (es) es.remove();
    streamingMsgEl = null;
    const userDiv = document.createElement('div');
    userDiv.className = 'message user';
    userDiv.innerHTML = `<div class="msg-label">You</div><div class="msg-bubble">${escapeHtml(userText)}</div><div class="msg-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>`;
    $('messages').appendChild(userDiv);
    const aiDiv = document.createElement('div');
    aiDiv.className = 'message ai';
    aiDiv.innerHTML = `<div class="msg-label">AI Assistant</div><div class="msg-bubble"><div class="typing-indicator" id="typing-indicator"><span></span><span></span><span></span></div></div>`;
    $('messages').appendChild(aiDiv);
    $('messages').scrollTop = $('messages').scrollHeight;
}

function updateStreamingMessage(chunk) {
    const ti = $('typing-indicator');
    if (ti) {
        const bubble = ti.closest('.msg-bubble');
        bubble.innerHTML = '';
        streamingMsgEl = document.createElement('span');
        streamingMsgEl.className = 'streaming-cursor';
        streamingMsgEl.textContent = chunk;
        bubble.appendChild(streamingMsgEl);
    } else {
        const aiMsgs = $('messages').querySelectorAll('.message.ai');
        const lastAi = aiMsgs[aiMsgs.length - 1];
        if (lastAi) {
            const bubble = lastAi.querySelector('.msg-bubble');
            if (bubble) {
                if (!streamingMsgEl) { bubble.innerHTML = ''; streamingMsgEl = document.createElement('span'); streamingMsgEl.className = 'streaming-cursor'; bubble.appendChild(streamingMsgEl); }
                streamingMsgEl.textContent += chunk;
            }
        }
    }
    $('messages').scrollTop = $('messages').scrollHeight;
}

function removeTypingIndicator() {
    const ti = $('typing-indicator');
    if (ti) { const b = ti.closest('.msg-bubble'); if (b) b.innerHTML = ''; streamingMsgEl = null; }
}

// ---- Render Messages ----

function renderMessages(messages) {
    if (!messages || messages.length === 0) {
        $('messages').innerHTML = `<div class="empty-state"><div class="empty-icon">\uD83C\uDFA4</div><h3>Ready to talk</h3><p>Press the mic button or type a message to start</p></div>`;
        return;
    }
    $('messages').innerHTML = '';
    messages.forEach((msg, idx) => {
        const div = document.createElement('div');
        div.className = `message ${msg.role}`;
        const ts = msg.timestamp ? new Date(msg.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        div.innerHTML = `
            <div class="msg-label">${msg.role === 'user' ? 'You' : 'AI Assistant'}</div>
            <div class="msg-bubble">${escapeHtml(msg.content)}</div>
            <div class="msg-time">${ts}</div>
            <div class="msg-actions">
                <button class="msg-action-btn" onclick="copyMessage(this)" title="Copy"><span class="msg-icon">\uD83D\uDCCB</span></button>
                ${msg.role === 'assistant' ? `<button class="msg-action-btn" onclick="speakMessage(this)" title="Listen"><span class="msg-icon">\uD83D\uDD0A</span></button>` : ''}
                ${msg.role === 'assistant' ? `<button class="msg-action-btn" onclick="retryMessage()" title="Retry"><span class="msg-icon">\uD83D\uDD04</span></button>` : ''}
                <button class="msg-action-btn" onclick="deleteMessage(${idx})" title="Delete"><span class="msg-icon">\uD83D\uDDD1</span></button>
            </div>`;
        $('messages').appendChild(div);
    });
    $('messages').scrollTop = $('messages').scrollHeight;
}

// ---- Message Actions ----

function copyMessage(btn) {
    const bubble = btn.closest('.message')?.querySelector('.msg-bubble');
    if (bubble) navigator.clipboard.writeText(bubble.textContent).then(() => showNotification('Copied')).catch(() => showNotification('Failed to copy', 'error'));
}

function speakMessage(btn) {
    const bubble = btn.closest('.message')?.querySelector('.msg-bubble');
    const text = bubble?.textContent?.trim();
    if (!text) return;
    const icon = btn.querySelector('.msg-icon');
    if (icon) icon.textContent = '\u23F3';
    btn.disabled = true;
    socket.emit('command', { command: 'speak', text });
}

function re_enableSpeakButtons() {
    document.querySelectorAll('.msg-action-btn[onclick*="speakMessage"]').forEach(b => {
        b.disabled = false;
        const icon = b.querySelector('.msg-icon');
        if (icon) icon.textContent = '\uD83D\uDD0A';
    });
}

function retryMessage() { socket.emit('command', { command: 'retry' }); }
function deleteMessage(index) { socket.emit('command', { command: 'delete_message', index }); }

function copyLastResponse() {
    if (!lastResponse) { showNotification('No AI response to copy', 'warning'); return; }
    navigator.clipboard.writeText(lastResponse).then(() => showNotification('Copied')).catch(() => showNotification('Failed to copy', 'error'));
}

// ---- View Switching ----

function switchView(view) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    const v = document.getElementById('view-' + view);
    if (v) v.classList.add('active');
    const btn = document.querySelector(`.nav-btn[data-view="${view}"]`);
    if (btn) btn.classList.add('active');
    if (window.innerWidth <= 768) document.getElementById('sidebar').classList.remove('open');
    if (view === 'memory') refreshMemory();
    if (view === 'conversations') refreshConversations();
}

function toggleSidebar() { document.getElementById('sidebar').classList.toggle('open'); }

// ---- Commands ----

function changeLanguage(lang) {
    socket.emit('command', { command: 'language', language: lang });
    document.documentElement.dir = lang === 'fa' ? 'rtl' : 'ltr';
    showNotification(`Switched to ${lang === 'en' ? 'English' : 'Persian'}`);
}
function changeVolume(val) { socket.emit('command', { command: 'volume', value: parseFloat(val) }); }
function changeSpeed(val) { socket.emit('command', { command: 'speed', value: parseFloat(val) }); }
function setApiUrl(val) { socket.emit('command', { command: 'set_api_url', value: val }); }
function setApiKey(val) { socket.emit('command', { command: 'set_api_key', value: val }); }
function setApiModel(val) { socket.emit('command', { command: 'set_api_model', value: val }); }
function setSttBackend(val) { socket.emit('command', { command: 'set_stt_backend', value: val }); }
function setWhisperModel(val) { socket.emit('command', { command: 'set_whisper_model', value: val }); }
function setTtsVoice(lang, val) { socket.emit('command', { command: 'set_tts_voice', lang, model_path: val + '.onnx', config_path: val + '.onnx.json' }); }
function setSystemPrompt(val) { socket.emit('command', { command: 'set_system_prompt', value: val }); }
function downloadModels() { socket.emit('command', { command: 'download_models' }); }

function newConversation() {
    if (confirm('Start a new conversation?')) socket.emit('command', { command: 'new_conversation' });
}
function saveConversation() { socket.emit('command', { command: 'save' }); showNotification('Saved'); }

function exportJSON() { window.open('/export/json?user=' + currentUsername + '&id=' + currentSessionId + '&t=' + Date.now(), '_blank'); }
function exportText() { window.open('/export/text?user=' + currentUsername + '&id=' + currentSessionId + '&t=' + Date.now(), '_blank'); }
function exportMarkdown() { window.open('/export/markdown?user=' + currentUsername + '&id=' + currentSessionId + '&t=' + Date.now(), '_blank'); }

// ---- Theme ----

function toggleTheme() {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);
    localStorage.setItem('theme', currentTheme);
    if ($('theme-icon')) $('theme-icon').textContent = currentTheme === 'dark' ? '\uD83C\uDF19' : '\u2600\uFE0F';
    if ($('theme-label')) $('theme-label').textContent = currentTheme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
}
if (!localStorage.getItem('theme') && window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
    currentTheme = 'light';
    document.documentElement.setAttribute('data-theme', 'light');
}

// ---- Conversations ----

function refreshConversations() { socket.emit('command', { command: 'list_conversations' }); }

function renderConversationList() {
    const list = $('conversation-list');
    const sidebarList = $('session-list');
    const renderItems = (container) => {
        if (!container) return;
        container.innerHTML = '<div class="sidebar-sessions-header">' + (conversationsCache.length ? 'Conversations' : 'No saved conversations') + '</div>'
            + conversationsCache.map(id => `<div class="session-item" onclick="loadConversation('${id}')">${id}</div>`).join('');
    };
    renderItems(sidebarList);
    if (!list) return;
    if (!conversationsCache.length) { list.innerHTML = '<div class="setting-desc">No saved conversations yet.</div>'; return; }
    list.innerHTML = conversationsCache.map(id =>
        `<div class="conversation-item" onclick="loadConversation('${id}')"><span class="conversation-item-name">${id}</span></div>`
    ).join('');
}

function loadConversation(id) { socket.emit('command', { command: 'load_conversation', id }); switchView('chat'); }

function searchConversations(query) {
    if (query) renderConversationListFiltered(conversationsCache.filter(id => id.includes(query)));
    else renderConversationList();
}

function renderConversationListFiltered(filtered) {
    const list = $('conversation-list');
    if (!list) return;
    list.innerHTML = filtered.length ? filtered.map(id =>
        `<div class="conversation-item" onclick="loadConversation('${id}')"><span class="conversation-item-name">${id}</span></div>`
    ).join('') : '<div class="setting-desc">No matches.</div>';
}

// ---- Memory ----

function switchMemoryTab(target) {
    currentMemoryTab = target;
    document.querySelectorAll('.memory-tab').forEach(t => t.classList.toggle('active', t.dataset.target === target));
    const entriesEl = $('memory-entries');
    const addForm = document.querySelector('.memory-add-form');
    const rawEditor = $('memory-raw-editor');
    const usageBar = document.querySelector('.memory-usage-bar');
    const usageText = $('memory-usage-text');
    if (target === 'soul') {
        if (entriesEl) entriesEl.style.display = 'none';
        if (addForm) addForm.style.display = 'none';
        if (usageBar) usageBar.style.display = 'none';
        if (usageText) usageText.style.display = 'none';
        if (rawEditor) rawEditor.style.display = 'block';
    } else {
        if (entriesEl) entriesEl.style.display = 'block';
        if (addForm) addForm.style.display = 'block';
        if (usageBar) usageBar.style.display = 'block';
        if (usageText) usageText.style.display = 'block';
        if (rawEditor) rawEditor.style.display = 'none';
    }
    refreshMemory();
}

function refreshMemory() {
    if (currentMemoryTab === 'soul') socket.emit('memory', { action: 'get_raw', target: 'soul' });
    else { socket.emit('memory', { action: 'list' }); socket.emit('memory', { action: 'get_raw', target: currentMemoryTab }); }
}

function renderMemoryEntries(target, entries, usage) {
    if (target !== currentMemoryTab) return;
    if ($('memory-usage-fill') && usage) $('memory-usage-fill').style.width = Math.min(usage.percent, 100) + '%';
    if ($('memory-usage-text') && usage) $('memory-usage-text').textContent = `${usage.current} / ${usage.limit} chars (${usage.percent}%)`;
    const entriesEl = $('memory-entries');
    if (!entriesEl) return;
    if (!entries || !entries.length) entriesEl.innerHTML = '<div class="setting-desc">No entries yet.</div>';
    else entriesEl.innerHTML = entries.map((entry, i) =>
        `<div class="memory-entry"><span class="memory-entry-num">#${i + 1}</span><span class="memory-entry-text">${escapeHtml(entry)}</span><button class="memory-entry-remove" onclick="removeMemoryEntry('${target}', this)">&times;</button></div>`
    ).join('');
}

function addMemoryEntry() {
    const content = $('memory-new-entry').value.trim();
    if (!content) return;
    socket.emit('memory', { action: 'add', target: currentMemoryTab, content });
    $('memory-new-entry').value = '';
    setTimeout(refreshMemory, 300);
}

function removeMemoryEntry(target, btn) {
    const entryDiv = btn.closest('.memory-entry');
    const textEl = entryDiv?.querySelector('.memory-entry-text');
    const text = textEl?.textContent?.trim();
    if (!text) return;
    socket.emit('memory', { action: 'remove', target, old_text: text });
    setTimeout(refreshMemory, 300);
}

function saveMemoryRaw() {
    const textarea = $('memory-raw-text');
    const target = textarea.dataset.target || currentMemoryTab;
    socket.emit('memory', { action: 'set_raw', target, content: textarea.value });
    showNotification('Saved');
}

// ---- Diagnostics ----

async function runDiagnostics() {
    const resultsEl = $('diag-results');
    if (!resultsEl) return;
    resultsEl.innerHTML = '<div class="setting-desc">Running diagnostics...</div>';
    try {
        const resp = await fetch('/api/diagnostics', { headers: { 'X-Auth-Token': authToken } });
        if (!resp.ok) { resultsEl.innerHTML = '<div class="diag-item diag-fail"><div class="diag-header"><span class="diag-status">\u274C</span><span class="diag-name">Not authenticated</span></div></div>'; return; }
        const data = await resp.json();
        const items = [
            { label: 'STT Backend', pass: data.stt?.available, detail: `${data.stt?.backend}: ${data.stt?.model}` },
            { label: 'TTS Model', pass: data.tts?.available, detail: data.tts?.model },
            { label: 'Vosk Model', pass: data.vosk?.available, detail: data.vosk?.model },
            { label: 'API Connection', pass: data.api?.available, detail: `${data.api?.url} — ${data.api?.message}` },
            { label: 'Memory', pass: true, detail: `${data.memory?.memory_entries} memory, ${data.memory?.user_entries} user` },
            { label: 'Languages', pass: (data.languages || []).length > 0, detail: (data.languages || []).join(', ') + ` (${data.current_language})` },
            { label: 'User', pass: true, detail: data.user },
        ];
        resultsEl.innerHTML = items.map(item =>
            `<div class="diag-item ${item.pass ? 'diag-pass' : 'diag-fail'}"><div class="diag-header"><span class="diag-status">${item.pass ? '\u2705' : '\u274C'}</span><span class="diag-name">${item.label}</span></div><div class="diag-detail">${escapeHtml(item.detail || '')}</div></div>`
        ).join('');
    } catch (e) {
        resultsEl.innerHTML = `<div class="diag-item diag-fail"><div class="diag-header"><span class="diag-status">\u274C</span><span class="diag-name">Error</span></div><div class="diag-detail">${escapeHtml(e.message)}</div></div>`;
    }
}

// ---- Notifications ----

function showNotification(msg, type) {
    const container = $('notifications');
    if (!container) return;
    const el = document.createElement('div');
    el.className = 'notification ' + (type || 'info');
    el.textContent = msg;
    container.appendChild(el);
    requestAnimationFrame(() => el.classList.add('show'));
    setTimeout(() => { el.classList.remove('show'); setTimeout(() => el.remove(), 300); }, 3500);
}

// ---- Keyboard Shortcuts ----

document.addEventListener('keydown', (e) => {
    if (e.key === ' ' && e.target === document.body && !$('text-input')?.contains(e.target)) { e.preventDefault(); toggleRecording(); }
    if (e.key === 'Escape' && isRecording) stopRecording();
});

// ---- Utilities ----

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
