const express = require('express');
const yahooFinance = require('yahoo-finance2').default;
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, '../client')));

app.get('/api/stock/:symbol', async (req, res) => {
  try {
    const quote = await yahooFinance.quote(req.params.symbol);
    res.json({ symbol: req.params.symbol, price: quote.regularMarketPrice });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/backtest', (req, res) => {
  const py = spawn('python', [
    'src/scripts/run_backtest.py',
    '--root', 'market_data',
    '--symbol', req.body.symbol || 'SPY',
    '--short', '5',
    '--long', '20',
    '--cash', '10000'
  ]);

  let output = '';
  py.stdout.on('data', data => output += data.toString());
  py.stderr.on('data', data => output += data.toString());
  py.on('close', code => {
    res.json({ code, output });
  });
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});

module.exports = app;
