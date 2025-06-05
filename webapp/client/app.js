const e = React.createElement;

function StockApp() {
  const [symbol, setSymbol] = React.useState('SPY');
  const [price, setPrice] = React.useState(null);
  const chartRef = React.useRef(null);
  let chart;

  const fetchPrice = async () => {
    const res = await axios.get(`/api/stock/${symbol}`);
    setPrice(res.data.price);
  };

  const runBacktest = async () => {
    const res = await axios.post('/api/backtest', { symbol });
    alert(res.data.output);
  };

  React.useEffect(() => {
    fetchPrice();
  }, [symbol]);

  React.useEffect(() => {
    if (!chartRef.current) return;
    if (chart) chart.destroy();
    if (price) {
      const ctx = chartRef.current.getContext('2d');
      chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: [symbol],
          datasets: [{ label: symbol, data: [price] }]
        }
      });
    }
  }, [price]);

  return e('div', null,
    e('input', {
      value: symbol,
      onChange: (ev) => setSymbol(ev.target.value)
    }),
    e('button', { onClick: fetchPrice }, 'Fetch'),
    e('button', { onClick: runBacktest }, 'Run Backtest'),
    e('p', null, price !== null ? `Price: ${price}` : 'Loading...'),
    e('canvas', { id: 'chart', ref: chartRef })
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(e(StockApp));
