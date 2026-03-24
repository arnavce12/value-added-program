const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');
const pdfParse = require('pdf-parse');
const db = require('../db');
const router = express.Router();

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
    if (!req.file) return res.status(400).json({ error: 'No file uploaded' });

    const { path: tmpPath, mimetype, originalname } = req.file;

    // Give file a stable name
    const ext = path.extname(originalname);
    const filename = `${uuidv4()}${ext}`;
    const destPath = path.join(__dirname, '../../uploads/', filename);
    fs.renameSync(tmpPath, destPath);

    // For text-based PDFs: extract text now, store it — never re-extract later
    let extracted = null;
    if (mimetype === 'application/pdf') {
        try {
            const buffer = fs.readFileSync(destPath);
            const data = await pdfParse(buffer);
            extracted = data.text?.trim() || null;
            // If no text extracted, it's a scanned PDF — Pixtral will handle it as image
        } catch { extracted = null; }
    }

    db.createSession(sessionId);  // creates if not exists
    db.saveUpload(sessionId, originalname, destPath, mimetype, extracted);

    res.json({
        success: true,
        filename: originalname,
        isPdf: mimetype === 'application/pdf',
        hasText: !!extracted
    });
});

// Multer error handler (covers file size + type rejections)
router.use((err, req, res, next) => {
    if (err.code === 'LIMIT_FILE_SIZE')
        return res.status(413).json({ error: 'File exceeds 10MB limit' });
    res.status(400).json({ error: err.message });
});

module.exports = router;
