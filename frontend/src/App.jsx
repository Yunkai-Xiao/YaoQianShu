import { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  TimeScale,
  Tooltip,
  Legend
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import './App.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, TimeScale, Tooltip, Legend);

function App() {
  const [symbol, setSymbol] = useState('SPY');
  const [strategies, setStrategies] = useState([]);
  const [strategy, setStrategy] = useState('');
  const [prices, setPrices] = useState([]);
  const [history, setHistory] = useState([]);
  const [trades, setTrades] = useState([]);
  const [report, setReport] = useState(null);

  useEffect(() => {
    fetch('/strategies')
      .then(r => r.json())
      .then(d => {
        setStrategies(d.strategies);
        if (d.strategies.length > 0) setStrategy(d.strategies[0]);
      });
  }, []);

  useEffect(() => {
    fetch(`/data/${symbol}`)
      .then(r => r.json())
      .then(d => setPrices(d.data));
  }, [symbol]);

  const runBacktest = async () => {
    const res = await fetch('/backtest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol, strategy })
    });
    const data = await res.json();
    setHistory(data.history);
    setTrades(data.trades);
    setReport(data.report);
  };

  const priceData = {
    datasets: [
      {
        label: 'Close',
        data: prices.map(p => ({ x: p.timestamp, y: p.Close })),
        borderColor: 'blue',
        fill: false,
      },
      {
        label: 'Buy',
        data: trades.filter(t => t.side === 'buy').map(t => ({ x: t.timestamp, y: t.price })),
        type: 'scatter',
        pointBackgroundColor: 'green',
        showLine: false,
      },
      {
        label: 'Sell',
        data: trades.filter(t => t.side === 'sell').map(t => ({ x: t.timestamp, y: t.price })),
        type: 'scatter',
        pointBackgroundColor: 'red',
        showLine: false,
      },
    ],
  };

  const pnlData = {
    datasets: [
      {
        label: 'Portfolio value',
        data: history.map(h => ({ x: h.timestamp, y: h.value })),
        borderColor: 'orange',
        fill: false,
      },
    ],
  };

  return (
    <div id="root">
      <h1>Backtest UI</h1>
      <div className="controls">
        <input value={symbol} onChange={e => setSymbol(e.target.value)} />
        <select value={strategy} onChange={e => setStrategy(e.target.value)}>
          {strategies.map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button onClick={runBacktest}>Run Backtest</button>
      </div>
      <div className="chart">
        <Line data={priceData} options={{ scales: { x: { type: 'time' } } }} />
      </div>
      <div className="chart">
        <Line data={pnlData} options={{ scales: { x: { type: 'time' } } }} />
      </div>
      {report && (
        <pre className="report">{JSON.stringify(report, null, 2)}</pre>
      )}
    </div>
  );
}

export default App;
