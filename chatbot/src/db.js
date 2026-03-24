const Database = require('better-sqlite3');
const path = require('path');

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
