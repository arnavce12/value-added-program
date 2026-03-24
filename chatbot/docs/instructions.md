# Chatbot Feature Implementation Instructions

> **Agent Efficiency Rules** — Read before starting:
> - Implement features **incrementally**: complete and test one feature before moving to the next.
> - **Never regenerate** existing working code. Use targeted edits only.
> - **Reuse** the same `<select>` UI pattern across all three features.
> - Make **one API/TTS call at a time** — do not batch or duplicate calls.
> - Cache voice/language lists at startup; never re-fetch them per message.

---

## Project Structure (Assumed)

```
chatbot/
├── index.html
├── style.css
└── app.js
```

All three features plug into this existing structure. No new files needed unless you split logic intentionally.

---

## Feature 1 — Edge TTS Audio (English + Regional Languages)

### What It Does
Converts chatbot text responses to speech using Microsoft Edge TTS voices. Supports both English and Indian regional language voices.

### Backend Setup (Node.js — one-time)

Install the Edge TTS package:
```bash
npm install edge-tts
```

Create a minimal TTS endpoint (`server.js`):
```js
const edgeTTS = require('edge-tts');
const express = require('express');
const app = express();
app.use(express.json());

app.post('/tts', async (req, res) => {
  const { text, voice } = req.body;
  // voice example: "en-US-AriaNeural" or "hi-IN-SwaraNeural"
  const tts = new edgeTTS.EdgeTTS();
  const { audioStream } = await tts.tts(text, voice);
  res.setHeader('Content-Type', 'audio/mpeg');
  audioStream.pipe(res);
});

app.listen(3001);
```

> **Efficiency note:** One POST call per chatbot response only. Do not call TTS mid-stream or on partial text.

### Supported Voice Reference (cache this list in JS — do not re-fetch)

```js
const VOICES = {
  "English (US)":   "en-US-AriaNeural",
  "English (UK)":   "en-GB-SoniaNeural",
  "Hindi":          "hi-IN-SwaraNeural",
  "Marathi":        "mr-IN-AarohiNeural",
  "Tamil":          "ta-IN-PallaviNeural",
  "Telugu":         "te-IN-MohanNeural",
  "Bengali":        "bn-IN-TanishaaNeural",
  "Kannada":        "kn-IN-SapnaNeural",
  "Gujarati":       "gu-IN-DhwaniNeural",
  "Punjabi":        "pa-IN-OjasNeural"
};
```

### HTML — Add Voice Select Tab

Add inside your toolbar/settings area:
```html
<label for="voiceSelect">🔊 Voice:</label>
<select id="voiceSelect">
  <option value="">-- Off --</option>
  <!-- Populated by JS from VOICES object -->
</select>
```

### JS — Populate & Play

```js
// Populate dropdown once on load
const voiceSelect = document.getElementById('voiceSelect');
Object.entries(VOICES).forEach(([label, val]) => {
  const opt = document.createElement('option');
  opt.value = val;
  opt.textContent = label;
  voiceSelect.appendChild(opt);
});

// Call after bot responds
async function speakText(text) {
  const voice = voiceSelect.value;
  if (!voice) return; // TTS off
  const res = await fetch('/tts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, voice })
  });
  const blob = await res.blob();
  const audio = new Audio(URL.createObjectURL(blob));
  audio.play();
}
```

> Call `speakText(botReply)` exactly once after the full bot reply is received.

---

## Feature 2 — Multilingual Responses

### What It Does
Instructs the chatbot to respond in the user's selected language by prepending a language directive to the system prompt or user message.

### No Extra API Calls Needed
This works by modifying the prompt — zero overhead.

### Supported Languages (hardcode this — do not fetch)

```js
const LANGUAGES = {
  "English":  "en",
  "Hindi":    "hi",
  "Marathi":  "mr",
  "Tamil":    "ta",
  "Telugu":   "te",
  "Bengali":  "bn",
  "Kannada":  "kn",
  "Gujarati": "gu",
  "Punjabi":  "pa",
  "French":   "fr",
  "Spanish":  "es"
};
```

### HTML — Add Language Select Tab

```html
<label for="langSelect">🌐 Language:</label>
<select id="langSelect">
  <!-- Populated by JS -->
</select>
```

### JS — Populate & Inject into Prompt

```js
// Populate once on load
const langSelect = document.getElementById('langSelect');
Object.keys(LANGUAGES).forEach(lang => {
  const opt = document.createElement('option');
  opt.value = lang;
  opt.textContent = lang;
  if (lang === 'English') opt.selected = true;
  langSelect.appendChild(opt);
});

// When building your API request, prepend language instruction
function getSystemPrompt() {
  const lang = langSelect.value;
  return `You are a helpful assistant. Always respond in ${lang} only, regardless of the language the user writes in.`;
}
```

> **Efficiency:** This adds ~10 tokens to the system prompt. That is the only cost. Do not send separate translation requests.

---

## Feature 3 — Response Style / Mode Select

### What It Does
Lets the user pick the chatbot's response mode: Default, Concise, Detailed, Formal, or Simple.

### HTML — Add Style Select Tab

```html
<label for="styleSelect">🎛️ Style:</label>
<select id="styleSelect">
  <option value="default">Default</option>
  <option value="concise">Concise</option>
  <option value="detailed">Detailed</option>
  <option value="formal">Formal</option>
  <option value="simple">Simple / ELI5</option>
</select>
```

### JS — Inject into System Prompt

```js
const STYLE_INSTRUCTIONS = {
  default:  "",
  concise:  "Keep responses brief — 2 to 3 sentences max.",
  detailed: "Give thorough, well-structured responses with examples.",
  formal:   "Use formal, professional language at all times.",
  simple:   "Explain everything simply, as if speaking to a beginner."
};

function getStyleInstruction() {
  return STYLE_INSTRUCTIONS[document.getElementById('styleSelect').value] || "";
}
```

Merge into your system prompt builder:
```js
function buildSystemPrompt() {
  const lang  = langSelect.value || 'English';
  const style = getStyleInstruction();
  return [
    `You are a helpful assistant. Always respond in ${lang} only.`,
    style
  ].filter(Boolean).join(' ');
}
```

---

## Wiring Everything Together

Inside your existing message-send handler, make these small changes only:

```js
async function sendMessage(userInput) {
  const systemPrompt = buildSystemPrompt(); // Features 2 + 3

  const response = await callYourChatAPI({
    system: systemPrompt,
    message: userInput
  });

  displayBotMessage(response);
  await speakText(response);  // Feature 1 — only if voice is selected
}
```

> **Do not** call `buildSystemPrompt()` or `speakText()` more than once per user message.

---

## UI Layout Suggestion

Place all three selects in a single settings bar above or below the chat input:

```html
<div id="settingsBar">
  <label>🔊 Voice: <select id="voiceSelect"><option value="">Off</option></select></label>
  <label>🌐 Language: <select id="langSelect"></select></label>
  <label>🎛️ Style: <select id="styleSelect">
    <option value="default">Default</option>
    <option value="concise">Concise</option>
    <option value="detailed">Detailed</option>
    <option value="formal">Formal</option>
    <option value="simple">Simple</option>
  </select></label>
</div>
```

```css
#settingsBar {
  display: flex;
  gap: 1rem;
  padding: 0.5rem;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
  flex-wrap: wrap;
}
#settingsBar label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.9rem;
}
```

---

## Token/Cost Efficiency Summary

| Feature | Token Cost per Message | Notes |
|---|---|---|
| Edge TTS | 0 tokens | Separate audio endpoint, no LLM tokens used |
| Language select | ~10 tokens | Added to system prompt only |
| Style select | ~10 tokens | Added to system prompt only |
| **Total overhead** | **~20 tokens/message** | Negligible |

**Avoid these common wasteful patterns:**
- ❌ Sending a second API call to translate the response
- ❌ Re-fetching the voice or language list on every message
- ❌ Calling TTS on streaming partial text
- ❌ Hardcoding language instructions inside each user message instead of the system prompt

---

## Implementation Order

1. Set up the TTS backend endpoint (Feature 1 backend)
2. Add and wire the `#settingsBar` HTML
3. Populate dropdowns on page load (one-time JS)
4. Update `buildSystemPrompt()` to include language + style
5. Add `speakText()` call at the end of the bot reply handler
6. Test each select independently before combining
