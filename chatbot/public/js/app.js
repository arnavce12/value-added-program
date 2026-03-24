// Generate once per page load — persists for the tab's lifetime
const SESSION_ID = crypto.randomUUID();

// Clean up session when tab closes
window.addEventListener('beforeunload', () => {
  navigator.sendBeacon(`/api/session/${SESSION_ID}`,
    new Blob([JSON.stringify({ _method: 'DELETE' })], { type: 'application/json' })
  );
});

// ── STATE ──────────────────────────────────────────
let IS_READY = false;
let MODEL = "mistral-large-latest";
let TEMPERATURE = 0.7;
let MAX_TOKENS = 512;
const API_URL = "/api/chat"; // proxied through server.js to avoid CORS
const CONFIG_URL = "/api/config";
const history = [];

let currentAudio = null;
let currentPlayBtn = null;

const PLAY_ICON = '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
const PAUSE_ICON = '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>';

const VOICES = {
  "English (US)": "en-US-AriaNeural",
  "English (UK)": "en-GB-SoniaNeural",
  "Hindi": "hi-IN-SwaraNeural",
  "Marathi": "mr-IN-AarohiNeural",
  "Tamil": "ta-IN-PallaviNeural",
  "Telugu": "te-IN-MohanNeural",
  "Bengali": "bn-IN-TanishaaNeural",
  "Kannada": "kn-IN-SapnaNeural",
  "Gujarati": "gu-IN-DhwaniNeural",
  "Punjabi": "pa-IN-OjasNeural"
};

const LANGUAGES = {
  "English": "en",
  "Hindi": "hi",
  "Marathi": "mr",
  "Tamil": "ta",
  "Telugu": "te",
  "Bengali": "bn",
  "Kannada": "kn",
  "Gujarati": "gu",
  "Punjabi": "pa",
  "French": "fr",
  "Spanish": "es"
};

const STYLE_INSTRUCTIONS = {
  default: "",
  concise: "Keep responses brief — 2 to 3 sentences max.",
  detailed: "Give thorough, well-structured responses with examples.",
  formal: "Use formal, professional language at all times.",
  simple: "Explain everything simply, as if speaking to a beginner."
};
// ───────────────────────────────────────────────────

const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const emptyState = document.getElementById("empty-state");
const keyBadge = document.getElementById("key-status-badge");
const keyDisplay = document.getElementById("key-display");
const modelSelect = document.getElementById("model-select");
const tempSlider = document.getElementById("temp-slider");
const tempVal = document.getElementById("temp-val");
const tokensSlider = document.getElementById("tokens-slider");
const tokensVal = document.getElementById("tokens-val");
const toast = document.getElementById("toast");

const voiceSelect = document.getElementById('voiceSelect');
const langSelect = document.getElementById('langSelect');
const styleSelect = document.getElementById('styleSelect');

const fileInput = document.getElementById('fileInput');
const uploadLabel = document.getElementById('uploadLabel');
const uploadStatus = document.getElementById('uploadStatus');

uploadLabel.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', async () => {
  const file = fileInput.files[0];
  if (!file) return;

  if (file.size > 10 * 1024 * 1024) {
    uploadStatus.textContent = '❌ File exceeds 10MB limit';
    return;
  }

  uploadStatus.textContent = '⏳ Uploading...';

  const formData = new FormData();
  formData.append('file', file);
  formData.append('sessionId', SESSION_ID);

  try {
    const res = await fetch('/api/upload', { method: 'POST', body: formData });
    const data = await res.json();

    if (res.ok) {
      uploadStatus.textContent = `✅ ${data.filename} attached`;
    } else {
      uploadStatus.textContent = `❌ ${data.error}`;
    }
  } catch (e) {
    uploadStatus.textContent = '❌ Upload Failed';
  }
  fileInput.value = '';
});

Object.entries(VOICES).forEach(([label, val]) => {
  const opt = document.createElement('option');
  opt.value = val;
  opt.textContent = label;
  voiceSelect.appendChild(opt);
});

Object.keys(LANGUAGES).forEach(lang => {
  const opt = document.createElement('option');
  opt.value = lang;
  opt.textContent = lang;
  if (lang === 'English') opt.selected = true;
  langSelect.appendChild(opt);
});

// ── TABS ───────────────────────────────────────────
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
    if (btn.dataset.tab === "chat") inputEl.focus();
  });
});

// ── KEY UI ─────────────────────────────────────────
function updateKeyUI() {
  if (IS_READY) {
    keyBadge.textContent = "server ready";
    keyBadge.className = "set";
    keyDisplay.innerHTML = `Status: <span class="key-val">active</span>`;
    emptyState.style.display = history.length === 0 ? "" : "none";
  } else {
    keyBadge.textContent = "no configuration";
    keyBadge.className = "unset";
    keyDisplay.innerHTML = `<span style="color:var(--red)">API key missing on server</span>`;
    emptyState.style.display = "none";
  }
}

// ── SERVER READY ────────────────────────────────────
async function checkServerStatus() {
  try {
    const response = await fetch(CONFIG_URL);
    const data = await response.json();
    if (data.status === 'ready') {
      IS_READY = true;
    } else {
      IS_READY = false;
    }
    updateKeyUI();
  } catch (err) {
    console.error("Failed to check server config:", err);
    IS_READY = false;
    updateKeyUI();
  }
}

// ── MODEL ──────────────────────────────────────────
modelSelect.addEventListener("change", () => {
  MODEL = modelSelect.value;
  showToast(`Model → ${MODEL}`, "success");
});

tempSlider.addEventListener("input", () => {
  TEMPERATURE = parseFloat(tempSlider.value);
  tempVal.textContent = TEMPERATURE.toFixed(1);
});

tokensSlider.addEventListener("input", () => {
  MAX_TOKENS = parseInt(tokensSlider.value);
  tokensVal.textContent = MAX_TOKENS;
});

// ── TOAST ──────────────────────────────────────────
let toastTimer;
function showToast(msg, type = "") {
  toast.textContent = msg;
  toast.className = `show ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.className = "", 2200);
}

// ── CHAT ───────────────────────────────────────────
inputEl.addEventListener("input", () => {
  inputEl.style.height = "auto";
  inputEl.style.height = inputEl.scrollHeight + "px";
});

inputEl.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

sendBtn.addEventListener("click", sendMessage);

function appendMessage(role, content) {
  emptyState.style.display = "none";

  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "YOU" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = content;

  const playBtn = document.createElement("button");
  playBtn.className = "play-btn";
  playBtn.innerHTML = PLAY_ICON;
  playBtn.onclick = () => toggleSpeech(content, playBtn);
  playBtn.title = "Play Message";

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  wrapper.appendChild(playBtn);
  chatEl.appendChild(wrapper);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function appendTyping() {
  emptyState.style.display = "none";

  const wrapper = document.createElement("div");
  wrapper.className = "message ai";
  wrapper.id = "typing-msg";

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble typing-indicator";
  bubble.innerHTML = "<span></span><span></span><span></span>";

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  chatEl.appendChild(wrapper);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function removeTyping() {
  const el = document.getElementById("typing-msg");
  if (el) el.remove();
}

function buildSystemPrompt() {
  const lang = langSelect.value || 'English';
  const style = STYLE_INSTRUCTIONS[styleSelect.value] || "";
  return [
    `You are a helpful assistant. Always respond in ${lang} only, regardless of the language the user writes in.`,
    style
  ].filter(Boolean).join(' ');
}

async function toggleSpeech(text, btn) {
  if (currentPlayBtn === btn && currentAudio) {
    if (currentAudio.paused) {
      currentAudio.play();
      btn.innerHTML = PAUSE_ICON;
    } else {
      currentAudio.pause();
      btn.innerHTML = PLAY_ICON;
    }
    return;
  }

  if (currentAudio && currentPlayBtn) {
    currentAudio.pause();
    currentPlayBtn.innerHTML = PLAY_ICON;
  }

  currentPlayBtn = btn;
  btn.innerHTML = PAUSE_ICON;

  const voice = voiceSelect.value;
  if (!voice) {
    btn.innerHTML = PLAY_ICON;
    showToast("Please select a voice first", "error");
    return;
  }

  if (btn._audio && btn._voice === voice) {
    currentAudio = btn._audio;
    currentAudio.play();
    return;
  }

  btn.style.opacity = "0.5";
  try {
    const res = await fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, voice })
    });
    if (!res.ok) throw new Error("TTS failed");
    const blob = await res.blob();
    currentAudio = new Audio(URL.createObjectURL(blob));

    btn._audio = currentAudio;
    btn._voice = voice;

    currentAudio.onended = () => {
      btn.innerHTML = PLAY_ICON;
      if (currentPlayBtn === btn) currentAudio = null;
    };

    btn.style.opacity = "1";
    currentAudio.play();
  } catch (e) {
    console.error("TTS Output Error", e);
    btn.innerHTML = PLAY_ICON;
    btn.style.opacity = "1";
    showToast("Failed to load audio", "error");
  }
}

async function sendMessage() {
  if (!IS_READY) {
    showToast("Server is not ready (API key missing)", "error");
    return;
  }

  const text = inputEl.value.trim();
  if (!text) return;

  inputEl.value = "";
  inputEl.style.height = "auto";
  sendBtn.disabled = true;

  appendMessage("user", text);
  history.push({ role: "user", content: text });
  appendTyping();

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: MODEL,
        sessionId: SESSION_ID,
        message: text,
        systemPrompt: buildSystemPrompt(),
        temperature: TEMPERATURE,
        max_tokens: MAX_TOKENS
      })
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.message || `HTTP ${response.status}`);
    }

    const data = await response.json();
    const reply = data.choices[0].message.content;

    history.push({ role: "assistant", content: reply });
    removeTyping();
    appendMessage("ai", reply);

  } catch (err) {
    removeTyping();

    const wrapper = document.createElement("div");
    wrapper.className = "message ai";
    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = "AI";
    const bubble = document.createElement("div");
    bubble.className = "error-bubble";
    bubble.textContent = `Error: ${err.message}`;
    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);
    chatEl.appendChild(wrapper);
    chatEl.scrollTop = chatEl.scrollHeight;

    history.pop();
  }

  sendBtn.disabled = false;
  inputEl.focus();
}

// Init
checkServerStatus();
