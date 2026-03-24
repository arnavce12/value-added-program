const express = require('express');
const fs = require('fs');
const db = require('../db');
const router = express.Router();

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
