<div align="center">

# 🤖 AI Chatbot

**Built on Day 2 of the Value Added Program**

[📄 View Visual README](https://arnavce12.github.io/value-added-program/README.html)

---

![Node.js](https://img.shields.io/badge/Node.js-18+-6af7c8?style=flat-square&logo=nodedotjs&logoColor=6af7c8&labelColor=0a0a0f)
![Express](https://img.shields.io/badge/Express-4.x-ffffff?style=flat-square&logo=express&logoColor=white&labelColor=0a0a0f)
![JavaScript](https://img.shields.io/badge/JavaScript-ES2022-f7c56a?style=flat-square&logo=javascript&logoColor=f7c56a&labelColor=0a0a0f)
![SQLite](https://img.shields.io/badge/SQLite-better--sqlite3-6af7c8?style=flat-square&logo=sqlite&logoColor=6af7c8&labelColor=0a0a0f)
![Mistral](https://img.shields.io/badge/Mistral-Pixtral-f76a8a?style=flat-square&logo=mistral&logoColor=f76a8a&labelColor=0a0a0f)
![Edge TTS](https://img.shields.io/badge/Edge_TTS-Neural_Voices-7c6af7?style=flat-square&logo=microsoft&logoColor=7c6af7&labelColor=0a0a0f)

A full-featured multimodal AI chatbot with multilingual support, regional text-to-speech, file understanding, and SQLite-backed session memory.

</div>

---

## ✨ Features

| | Feature | Details |
|---|---|---|
| 💬 | **AI Chat** | Mistral Pixtral with full session memory and conversation history |
| 📎 | **File Understanding** | Upload JPG, PNG, or PDF (max 10MB) — Pixtral reads and reasons about content natively |
| 🌐 | **Multilingual** | Responds in 11 languages — Hindi, Marathi, Tamil, Telugu, Bengali, and more |
| 🔊 | **Text-to-Speech** | Edge TTS neural voices for English and regional Indian languages |
| 🎛️ | **Response Styles** | Concise, Detailed, Formal, or Simple (ELI5) — switchable per message |
| 🧠 | **Session Memory** | SQLite stores chat history per browser tab, auto-created on first run |
| 🗑️ | **Auto Cleanup** | Uploaded files and session data deleted automatically on tab close |

---

## 🗂️ Project Structure

```
chatbot/
├── public/                  ← Frontend (served statically)
│   ├── index.html
│   ├── style.css
│   └── js/
│       └── app.js
├── src/
│   ├── routes/
│   │   ├── chat.js          ← Pixtral API + session history
│   │   ├── tts.js           ← Edge TTS audio endpoint
│   │   ├── upload.js        ← File upload handler (10MB limit)
│   │   └── session.js       ← Session cleanup on tab close
│   ├── db.js                ← SQLite setup and queries
│   └── config.js            ← Centralised environment config
├── docs/                    ← Implementation guides
│   ├── instructions.md      ← TTS, multilingual, style features
│   ├── refactor.md          ← Project structure refactor guide
│   └── file-upload-memory.md
├── uploads/                 ← Temporary storage (gitignored)
├── chatbot.db               ← Auto-created SQLite DB (gitignored)
├── .env
├── package.json
└── server.js
```

---

## 🚀 Setup

**Prerequisites:** Node.js v18+, a Mistral API key from [console.mistral.ai](https://console.mistral.ai)

**1. Clone and install**
```bash
git clone <your-repo-url>
cd chatbot
npm install
```

**2. Configure environment**
```bash
cp .env.example .env
```
```env
MISTRAL_API_KEY=your_key_here
PORT=3000
```

**3. Start the server**
```bash
node server.js
```

**4. Open** `http://localhost:3000`

> `chatbot.db` and `uploads/` are created automatically on first run — no database setup needed.

---

## 🌐 Supported Languages

| Language | TTS Voice |
|---|---|
| 🇺🇸 English (US) | `en-US-AriaNeural` |
| 🇬🇧 English (UK) | `en-GB-SoniaNeural` |
| 🇮🇳 Hindi | `hi-IN-SwaraNeural` |
| 🇮🇳 Marathi | `mr-IN-AarohiNeural` |
| 🇮🇳 Tamil | `ta-IN-PallaviNeural` |
| 🇮🇳 Telugu | `te-IN-MohanNeural` |
| 🇮🇳 Bengali | `bn-IN-TanishaaNeural` |
| 🇮🇳 Kannada | `kn-IN-SapnaNeural` |
| 🇮🇳 Gujarati | `gu-IN-DhwaniNeural` |
| 🇮🇳 Punjabi | `pa-IN-OjasNeural` |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Send message, get AI reply with session history |
| `POST` | `/api/upload` | Upload file (JPG / PNG / PDF, max 10MB) |
| `POST` | `/api/tts` | Convert text to speech audio |
| `DELETE` | `/api/session/:id` | Clear session data and delete uploaded files |

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `express` | Web server and routing |
| `multer` | File upload with 10MB limit enforcement |
| `better-sqlite3` | Synchronous SQLite for session memory |
| `pdf-parse` | Text extraction from text-based PDFs |
| `edge-tts` | Microsoft Edge neural TTS voices |
| `uuid` | Session ID and upload filename generation |
| `dotenv` | Environment variable loading |

---

## 📄 .gitignore

```
node_modules/
.env
uploads/
chatbot.db
```

---

<div align="center">

Built during the **Value Added Program — Day 2**

</div>