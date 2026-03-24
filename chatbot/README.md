# Chatbot — Value Added Program

## Setup
1. Copy `.env.example` to `.env` and fill in your API keys.
2. Run `npm install`
3. Run `node server.js`
4. Open `http://localhost:3000`

## Structure
- `public/`        → Frontend (HTML, CSS, JS)
- `src/routes/`    → Backend API routes (chat, TTS)
- `src/config.js`  → Environment config
- `docs/`          → Project documentation & instructions

## Features
See `docs/instructions.md` for implementation details on:
- Edge TTS (English + regional language audio)
- Multilingual responses
- Response style/mode selector
