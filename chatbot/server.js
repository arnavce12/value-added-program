require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');
const app = express();
const { mistralKey } = require('./src/config');

app.use(cors());
app.use(express.json());

// Serve frontend
app.use(express.static(path.join(__dirname, 'public')));

// Check if default API key is available
app.get('/api/config', (req, res) => {
  res.json({
    status: mistralKey ? 'ready' : 'missing_key'
  });
});

// Routes
app.use('/api/chat', require('./src/routes/chat'));
app.use('/api/tts', require('./src/routes/tts'));
app.use('/api/upload', require('./src/routes/upload'));
app.use('/api/session', require('./src/routes/session'));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
