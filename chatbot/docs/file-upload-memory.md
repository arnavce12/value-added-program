# File Upload + Session Memory Instructions

> **Agent Efficiency Rules** — Read before starting:
> - Implement in the order given: dependencies → backend routes → SQLite → frontend.
> - **Never re-extract** file content on every message. Extract once on upload, store in SQLite, reuse.
> - **Never send full file bytes** to Mistral on every message. Send base64 only on the initial upload message.
> - Session ID is generated once per page load on the frontend and sent with every request. Never regenerate it mid-session.
> - Do not touch `src/routes/chat.js` until Step 4 — understand the existing code first before modifying.

---

## Model Change — Switch to Pixtral

> **Do this first, before any other step.**

In `src/config.js`, update the model name:

```js
module.exports = {
  port:        process.env.PORT || 3000,
  mistralKey:  process.env.MISTRAL_API_KEY,
  mistralModel: 'pixtral-large-latest'   // ← was mistral-large-latest or similar
};
```

In `src/routes/chat.js`, confirm the model value is read from config:
```js
const { mistralKey, mistralModel } = require('../config');
// use mistralModel in your API call body, not a hardcoded string
```

Pixtral is a drop-in replacement for Mistral Large — same API shape, same endpoint, adds vision support. No other changes to the chat route are needed at this step.

---

## Step 1 — Install Dependencies

Run from inside `chatbot/`:

```bash
npm install multer uuid better-sqlite3 pdf-parse
```

| Package | Purpose |
|---|---|
| `multer` | Handles multipart file uploads, enforces 10MB limit |
| `uuid` | Generates unique session IDs and upload filenames |
| `better-sqlite3` | Synchronous SQLite — simpler than async alternatives for session data |
| `pdf-parse` | Extracts text from text-based PDFs before sending to Pixtral |

> **Do not install** `tesseract.js` or any OCR library — Pixtral handles images and scanned PDFs natively.

---

## Step 2 — Create Upload Directory

```bash
mkdir -p chatbot/uploads
```

Add to `.gitignore`:
```
uploads/
```

> Uploaded files are temporary. They are deleted when the session ends (page unload). Never commit them.

---

## Step 3 — SQLite Setup (`src/db.js`)

Create `src/db.js` — this is the single source of truth for all session and message data:

```js
const Database = require('better-sqlite3');
const path     = require('path');

const db = new Database(path.join(__dirname, '../chatbot.db'));

// Run once on startup — creates tables if they don't exist
db.exec(`
  CREATE TABLE IF NOT EXISTS sessions (
    id         TEXT PRIMARY KEY,
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
  );

  CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role       TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content    TEXT NOT NULL,
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (session_id) REFERENCES sessions(id)
  );

  CREATE TABLE IF NOT EXISTS uploads (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    filename   TEXT NOT NULL,
    filepath   TEXT NOT NULL,
    mimetype   TEXT NOT NULL,
    extracted  TEXT,            -- extracted text for PDFs; NULL for images
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (session_id) REFERENCES sessions(id)
  );
`);

module.exports = {

  // Sessions
  createSession: (id) => {
    db.prepare('INSERT OR IGNORE INTO sessions (id) VALUES (?)').run(id);
  },

  deleteSession: (id) => {
    db.prepare('DELETE FROM messages WHERE session_id = ?').run(id);
    db.prepare('DELETE FROM uploads  WHERE session_id = ?').run(id);
    db.prepare('DELETE FROM sessions WHERE id = ?').run(id);
  },

  // Messages
  addMessage: (sessionId, role, content) => {
    db.prepare('INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)')
      .run(sessionId, role, content);
  },

  getMessages: (sessionId) => {
    return db.prepare('SELECT role, content FROM messages WHERE session_id = ? ORDER BY created_at ASC')
      .all(sessionId);
  },

  // Uploads
  saveUpload: (sessionId, filename, filepath, mimetype, extracted = null) => {
    db.prepare('INSERT INTO uploads (session_id, filename, filepath, mimetype, extracted) VALUES (?, ?, ?, ?, ?)')
      .run(sessionId, filename, filepath, mimetype, extracted);
  },

  getUploads: (sessionId) => {
    return db.prepare('SELECT * FROM uploads WHERE session_id = ?').all(sessionId);
  },

  getUploadFilepaths: (sessionId) => {
    return db.prepare('SELECT filepath FROM uploads WHERE session_id = ?').all(sessionId)
      .map(r => r.filepath);
  }
};
```

---

## Step 4 — File Upload Route (`src/routes/upload.js`)

Create `src/routes/upload.js`:

```js
const express  = require('express');
const multer   = require('multer');
const path     = require('path');
const fs       = require('fs');
const { v4: uuidv4 } = require('uuid');
const pdfParse = require('pdf-parse');
const db       = require('../db');
const router   = express.Router();

// 10MB limit, images and PDFs only
const upload = multer({
  dest: path.join(__dirname, '../../uploads/'),
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const allowed = ['image/jpeg', 'image/png', 'application/pdf'];
    allowed.includes(file.mimetype)
      ? cb(null, true)
      : cb(new Error('Only JPG, PNG, and PDF files are allowed'));
  }
});

router.post('/', upload.single('file'), async (req, res) => {
  const { sessionId } = req.body;
  if (!sessionId) return res.status(400).json({ error: 'sessionId required' });
  if (!req.file)  return res.status(400).json({ error: 'No file uploaded' });

  const { path: tmpPath, mimetype, originalname } = req.file;

  // Give file a stable name
  const ext      = path.extname(originalname);
  const filename = `${uuidv4()}${ext}`;
  const destPath = path.join(__dirname, '../../uploads/', filename);
  fs.renameSync(tmpPath, destPath);

  // For text-based PDFs: extract text now, store it — never re-extract later
  let extracted = null;
  if (mimetype === 'application/pdf') {
    try {
      const buffer = fs.readFileSync(destPath);
      const data   = await pdfParse(buffer);
      extracted    = data.text?.trim() || null;
      // If no text extracted, it's a scanned PDF — Pixtral will handle it as image
    } catch { extracted = null; }
  }

  db.createSession(sessionId);  // creates if not exists
  db.saveUpload(sessionId, originalname, destPath, mimetype, extracted);

  res.json({
    success:   true,
    filename:  originalname,
    isPdf:     mimetype === 'application/pdf',
    hasText:   !!extracted
  });
});

// Multer error handler (covers file size + type rejections)
router.use((err, req, res, next) => {
  if (err.code === 'LIMIT_FILE_SIZE')
    return res.status(413).json({ error: 'File exceeds 10MB limit' });
  res.status(400).json({ error: err.message });
});

module.exports = router;
```

---

## Step 5 — Update Chat Route (`src/routes/chat.js`)

This is the most significant change. The chat route now needs to:
1. Load message history from SQLite
2. Attach uploaded files (as base64 images or extracted text) to the Mistral request
3. Save both user message and assistant reply to SQLite

**Full updated `src/routes/chat.js`:**

```js
const express  = require('express');
const fs       = require('fs');
const path     = require('path');
const router   = express.Router();
const db       = require('../db');
const { mistralKey, mistralModel } = require('../config');

// Convert a file to base64 image block for Pixtral
function fileToImageBlock(filepath, mimetype) {
  const data = fs.readFileSync(filepath).toString('base64');
  return {
    type: 'image_url',
    image_url: { url: `data:${mimetype};base64,${data}` }
  };
}

router.post('/', async (req, res) => {
  const { sessionId, message } = req.body;
  if (!sessionId || !message)
    return res.status(400).json({ error: 'sessionId and message required' });

  // Ensure session exists
  db.createSession(sessionId);

  // Build user message content — start with text
  const userContent = [{ type: 'text', text: message }];

  // Attach any uploads from this session
  const uploads = db.getUploads(sessionId);
  for (const upload of uploads) {
    if (upload.extracted) {
      // Text-based PDF: inject extracted text inline — no base64 needed
      userContent.push({
        type: 'text',
        text: `[Attached PDF: ${upload.filename}]\n${upload.extracted}`
      });
    } else {
      // Image or scanned PDF: send as base64 to Pixtral
      try {
        userContent.push(fileToImageBlock(upload.filepath, upload.mimetype));
      } catch {
        // File missing — skip silently
      }
    }
  }

  // Save user message to history (text only — don't store base64 in SQLite)
  db.addMessage(sessionId, 'user', message);

  // Build full message history for Mistral
  const history = db.getMessages(sessionId);
  // Replace last user message with the enriched version (with file attachments)
  const messages = [
    ...history.slice(0, -1).map(m => ({ role: m.role, content: m.content })),
    { role: 'user', content: userContent }
  ];

  // Call Mistral
  const response = await fetch('https://api.mistral.ai/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type':  'application/json',
      'Authorization': `Bearer ${mistralKey}`
    },
    body: JSON.stringify({ model: mistralModel, messages })
  });

  if (!response.ok) {
    const err = await response.text();
    return res.status(502).json({ error: 'Mistral API error', detail: err });
  }

  const data  = await response.json();
  const reply = data.choices?.[0]?.message?.content || '';

  // Save assistant reply
  db.addMessage(sessionId, 'assistant', reply);

  res.json({ reply });
});

module.exports = router;
```

---

## Step 6 — Session Cleanup Route (`src/routes/session.js`)

This route is called when the browser tab closes (via `beforeunload`). It deletes the session from SQLite and removes uploaded files from disk.

```js
const express = require('express');
const fs      = require('fs');
const db      = require('../db');
const router  = express.Router();

router.delete('/:sessionId', (req, res) => {
  const { sessionId } = req.params;

  // Delete uploaded files from disk first
  const filepaths = db.getUploadFilepaths(sessionId);
  filepaths.forEach(fp => {
    try { fs.unlinkSync(fp); } catch { /* already gone */ }
  });

  // Clear session from SQLite
  db.deleteSession(sessionId);

  res.json({ success: true });
});

module.exports = router;
```

---

## Step 7 — Register All Routes in `server.js`

Add three lines to `server.js`:

```js
app.use('/api/upload',  require('./src/routes/upload'));
app.use('/api/session', require('./src/routes/session'));
// chat route already registered — no change needed there
```

Full `server.js` for reference:
```js
require('dotenv').config();
const express = require('express');
const path    = require('path');
const app     = express();

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.use('/api/chat',    require('./src/routes/chat'));
app.use('/api/tts',     require('./src/routes/tts'));
app.use('/api/upload',  require('./src/routes/upload'));
app.use('/api/session', require('./src/routes/session'));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
```

---

## Step 8 — Frontend (`public/js/app.js`)

### 8a — Generate Session ID on Page Load

Add at the very top of `app.js`:

```js
// Generate once per page load — persists for the tab's lifetime
const SESSION_ID = crypto.randomUUID();

// Clean up session when tab closes
window.addEventListener('beforeunload', () => {
  navigator.sendBeacon(`/api/session/${SESSION_ID}`,
    new Blob([JSON.stringify({ _method: 'DELETE' })], { type: 'application/json' })
  );
});
```

> `navigator.sendBeacon` is used because `fetch` is unreliable during page unload.
> The backend DELETE route handles the actual cleanup.

### 8b — Add File Upload UI to `index.html`

Add inside your chat input area:

```html
<div id="uploadArea">
  <label for="fileInput" id="uploadLabel">
    📎 Attach file (JPG, PNG, PDF — max 10MB)
  </label>
  <input type="file" id="fileInput" accept=".jpg,.jpeg,.png,.pdf" style="display:none">
  <span id="uploadStatus"></span>
</div>
```

### 8c — Handle Upload in `app.js`

```js
const fileInput    = document.getElementById('fileInput');
const uploadLabel  = document.getElementById('uploadLabel');
const uploadStatus = document.getElementById('uploadStatus');

// Trigger file picker on label click
uploadLabel.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', async () => {
  const file = fileInput.files[0];
  if (!file) return;

  // Client-side size check before sending
  if (file.size > 10 * 1024 * 1024) {
    uploadStatus.textContent = '❌ File exceeds 10MB limit';
    return;
  }

  uploadStatus.textContent = '⏳ Uploading...';

  const formData = new FormData();
  formData.append('file', file);
  formData.append('sessionId', SESSION_ID);

  const res  = await fetch('/api/upload', { method: 'POST', body: formData });
  const data = await res.json();

  if (res.ok) {
    uploadStatus.textContent = `✅ ${data.filename} attached`;
  } else {
    uploadStatus.textContent = `❌ ${data.error}`;
  }

  fileInput.value = ''; // reset so same file can be re-attached if needed
});
```

### 8d — Pass Session ID with Every Chat Message

In your existing send-message function, add `sessionId` to every chat request:

```js
async function sendMessage(userInput) {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sessionId: SESSION_ID,   // ← add this
      message:   userInput
    })
  });
  const data = await res.json();
  displayBotMessage(data.reply);
  await speakText(data.reply);
}
```

---

## Final Project Structure (after this feature)

```
chatbot/
├── public/
│   ├── index.html
│   ├── style.css
│   └── js/
│       └── app.js
├── src/
│   ├── routes/
│   │   ├── chat.js       ← updated (session history + file context)
│   │   ├── tts.js
│   │   ├── upload.js     ← new
│   │   └── session.js    ← new
│   ├── db.js             ← new (SQLite)
│   └── config.js         ← updated (pixtral model)
├── uploads/              ← gitignored, auto-cleaned on session end
├── chatbot.db            ← auto-created by better-sqlite3
├── docs/
├── .env
├── .gitignore
├── package.json
└── server.js             ← two new route lines added
```

Add `chatbot.db` to `.gitignore`:
```
uploads/
chatbot.db
```

---

## Token Efficiency Summary

| Concern | How it's handled |
|---|---|
| File re-sent every message | ❌ Never — file attached only on first user message per session |
| PDF text stored in SQLite | ✅ Extracted once on upload, reused as plain text |
| Base64 images in SQLite | ❌ Never stored — read from disk only when needed |
| History sent to Mistral | ✅ Full history per session (needed for memory), text only |
| Scanned PDFs | ✅ Sent as base64 image to Pixtral — no OCR overhead |

---

## Smoke Test

```bash
# Start server
node server.js

# Test upload (replace with a real file path)
curl -X POST http://localhost:3000/api/upload \
  -F "file=@/path/to/test.png" \
  -F "sessionId=test-session-123"

# Test chat with session
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "test-session-123", "message": "What is in the uploaded image?"}'

# Test session cleanup
curl -X DELETE http://localhost:3000/api/session/test-session-123
```
