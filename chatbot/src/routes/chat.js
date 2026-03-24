const express = require('express');
const fs = require('fs');
const path = require('path');
const fetch = require('node-fetch');
const router = express.Router();
const db = require('../db');
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
    const { sessionId, message, systemPrompt, model, temperature, max_tokens } = req.body;
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
            } catch (e) {
                // File missing — skip silently
            }
        }
    }

    // Save user message to history (text only — don't store base64 in SQLite)
    db.addMessage(sessionId, 'user', message);

    // Build full message history for Mistral
    const history = db.getMessages(sessionId);

    // Replace last user message with the enriched version (with file attachments)
    const messagesPayload = [];
    if (systemPrompt) {
        messagesPayload.push({ role: 'system', content: systemPrompt });
    }

    messagesPayload.push(...history.slice(0, -1).map(m => ({ role: m.role, content: m.content })));
    messagesPayload.push({ role: 'user', content: userContent });

    // Call Mistral
    try {
        const response = await fetch('https://api.mistral.ai/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': `Bearer ${mistralKey}`
            },
            body: JSON.stringify({
                model: model || mistralModel || 'pixtral-large-latest',
                messages: messagesPayload,
                temperature: temperature ?? 0.7,
                max_tokens: max_tokens ?? 512
            })
        });

        const data = await response.json();

        if (!response.ok) {
            console.error('Mistral API Error:', data);
            return res.status(response.status).json({ message: data.message || 'Mistral API error', detail: data });
        }

        const reply = data.choices?.[0]?.message?.content || '';

        // Save assistant reply
        db.addMessage(sessionId, 'assistant', reply);

        res.json(data);
    } catch (err) {
        console.error('Proxy Fetch Error:', err);
        res.status(500).json({ message: 'Server error: failed to connect to Mistral API', error: err.message });
    }
});

module.exports = router;
