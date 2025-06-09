import React, { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  TimeScale,
  Tooltip,
  Legend,
} from "chart.js";
import "chartjs-adapter-date-fns";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  TimeScale,
  Tooltip,
  Legend
);

export default function Backtest() {
  const [tab, setTab] = useState("backtest");
  const [symbols, setSymbols] = useState([]);
  const [selectedSyms, setSelectedSyms] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [strategy, setStrategy] = useState("");
  const [prices, setPrices] = useState([]);
  const [history, setHistory] = useState([]);
  const [trades, setTrades] = useState([]);
  const [report, setReport] = useState(null);
  const [fetchSym, setFetchSym] = useState("");
  const [fetchStart, setFetchStart] = useState("2000-01-01");
  const [fetchEnd, setFetchEnd] = useState("");
  const [availSel, setAvailSel] = useState([]);
  const [chosenSel, setChosenSel] = useState([]);

  useEffect(() => {
    fetch("/symbols")
      .then((r) => r.json())
      .then((d) => {
        setSymbols(d.symbols);
        if (d.symbols.length) setSelectedSyms([d.symbols[0]]);
      });
    fetch("/strategies")
      .then((r) => r.json())
      .then((d) => {
        setStrategies(d.strategies);
        if (d.strategies.length) setStrategy(d.strategies[0]);
      });
  }, []);

  useEffect(() => {
    if (!selectedSyms.length) return;
    fetch(`/data/${selectedSyms[0]}`)
      .then((r) => r.json())
      .then((d) => setPrices(d.data));
  }, [selectedSyms]);

  const runBacktest = async () => {
    const res = await fetch("/backtest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbols: selectedSyms, strategy }),
    });
    const data = await res.json();
    setHistory(data.history);
    setTrades(data.trades);
    setReport(data.report);
  };

  const fetchData = async () => {
    const res = await fetch("/fetch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol: fetchSym, start: fetchStart, end: fetchEnd }),
    });
    const data = await res.json();
    alert(`Fetched ${data.rows} rows for ${fetchSym}`);
    const syms = await fetch("/symbols").then((r) => r.json());
    setSymbols(syms.symbols);
  };

  const addSelected = () => {
    setSelectedSyms([...selectedSyms, ...availSel]);
    setAvailSel([]);
  };

  const removeSelected = () => {
    setSelectedSyms(selectedSyms.filter((s) => !chosenSel.includes(s)));
    setChosenSel([]);
  };

  const priceData = {
    datasets: [
      {
        label: "Close",
        data: prices.map((p) => ({ x: p.timestamp, y: p.Close })),
        borderColor: "#00f",
        fill: false,
      },
      {
        label: "Buy",
        data: trades
          .filter((t) => t.side === "buy")
          .map((t) => ({ x: t.timestamp, y: t.price })),
        type: "scatter",
        pointBackgroundColor: "green",
        showLine: false,
      },
      {
        label: "Sell",
        data: trades
          .filter((t) => t.side === "sell")
          .map((t) => ({ x: t.timestamp, y: t.price })),
        type: "scatter",
        pointBackgroundColor: "red",
        showLine: false,
      },
    ],
  };

  const pnlData = {
    datasets: [
      {
        label: "Portfolio value",
        data: history.map((h) => ({ x: h.timestamp, y: h.value })),
        borderColor: "orange",
        fill: false,
      },
    ],
  };

  const Analysis = () =>
    report && (
      <table className="report">
        <tbody>
          {Object.entries(report).map(([k, v]) => (
            <tr key={k}>
              <td>{k}</td>
              <td>{v.toFixed ? v.toFixed(4) : v}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );

  return (
    <div className="content">
      <div className="toolbar" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <h2>Backtest Dashboard</h2>
        <div className="tabs">
          <button onClick={() => setTab("backtest")}>Backtest</button>
          <button onClick={() => setTab("fetch")}>Fetch Data</button>
        </div>
      </div>

      {tab === "backtest" && (
        <div>
          <div className="controls" style={{ display: "flex", justifyContent: "center", gap: "1rem", marginBottom: "1rem" }}>
            <div className="symbol-select" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <select
                multiple
                size={5}
                value={availSel}
                onChange={(e) =>
                  setAvailSel(Array.from(e.target.selectedOptions, (o) => o.value))
                }
              >
                {symbols
                  .filter((s) => !selectedSyms.includes(s))
                  .map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
              </select>
              <div className="symbol-buttons" style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                <button onClick={addSelected}>&gt;</button>
                <button onClick={removeSelected}>&lt;</button>
              </div>
              <select
                multiple
                size={5}
                value={chosenSel}
                onChange={(e) =>
                  setChosenSel(Array.from(e.target.selectedOptions, (o) => o.value))
                }
              >
                {selectedSyms.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <select value={strategy} onChange={(e) => setStrategy(e.target.value)}>
              {strategies.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <button onClick={runBacktest}>Run Backtest</button>
          </div>

          <div className="chart-container" style={{ position: "relative", height: 400, width: "100%", marginTop: "1rem" }}>
            <Line
              data={priceData}
              options={{ scales: { x: { type: "time" } }, responsive: true, maintainAspectRatio: false }}
            />
          </div>
          <div className="chart-container" style={{ position: "relative", height: 400, width: "100%", marginTop: "1rem" }}>
            <Line
              data={pnlData}
              options={{ scales: { x: { type: "time" } }, responsive: true, maintainAspectRatio: false }}
            />
          </div>
          <Analysis />
        </div>
      )}

      {tab === "fetch" && (
        <div className="controls" style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
          <div>
            <input
              placeholder="Symbol"
              value={fetchSym}
              onChange={(e) => setFetchSym(e.target.value.toUpperCase())}
            />
            <input
              type="date"
              value={fetchStart}
              onChange={(e) => setFetchStart(e.target.value)}
            />
            <input type="date" value={fetchEnd} onChange={(e) => setFetchEnd(e.target.value)} />
            <button onClick={fetchData}>Fetch</button>
          </div>
        </div>
      )}
    </div>
  );
}
