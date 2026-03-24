const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());
app.use(express.static('.')); // serves index.html in src

// Proxy route — receives request from browser, forwards to Mistral
app.post('/api/chat', async (req, res) => {
  const { messages, model, apiKey } = req.body;

  if (!apiKey) {
    return res.status(400).json({ message: 'No API key provided.' });
  }

  if (!messages || !Array.isArray(messages)) {
    return res.status(400).json({ message: 'Invalid messages format.' });
  }

  try {
    const response = await fetch('https://api.mistral.ai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: model || 'mistral-large-latest',
        messages
      })
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json({ message: data.message || 'Mistral API error.' });
    }

    res.json(data);

  } catch (err) {
    console.error('Proxy error:', err.message);
    res.status(500).json({ message: `Server error: ${err.message}` });
  }
});

app.listen(PORT, () => {
  console.log(`\n  Mistral Chat running at http://localhost:${PORT}\n`);
});
