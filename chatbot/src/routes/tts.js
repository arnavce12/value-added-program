const express = require('express');
const router = express.Router();
const { MsEdgeTTS, OUTPUT_FORMAT } = require('msedge-tts');

router.post('/', async (req, res) => {
    const { text, voice } = req.body;
    if (!text || !voice) return res.status(400).json({ error: 'text and voice required' });

    try {
        const tts = new MsEdgeTTS();

        // Use a standard MP3 format
        const format = OUTPUT_FORMAT ? OUTPUT_FORMAT.AUDIO_24KHZ_48KBITRATE_MONO_MP3 : 'audio-24khz-48kbitrate-mono-mp3';

        await tts.setMetadata(voice, format);

        // msedge-tts returns an object with audioStream
        const streamData = tts.toStream(text);

        // Handle varying output structures based on package version
        const readable = streamData.audioStream || streamData;

        res.setHeader('Content-Type', 'audio/mpeg');
        readable.pipe(res);

        readable.on('error', (err) => {
            console.error('TTS Stream error:', err);
            if (!res.headersSent) res.status(500).json({ error: 'TTS stream failed' });
        });
    } catch (err) {
        console.error('TTS error:', err);
        if (!res.headersSent) res.status(500).json({ error: 'TTS initialization failed: ' + err.message });
    }
});

module.exports = router;
