<div align="center">

# ⏫ StockPredict — ML Stock Market Prediction Platform

**Analyze historical equities and forecast future prices with a feature-engineered machine-learning ensemble, served through an interactive, responsive Flask dashboard.**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Plotly](https://img.shields.io/badge/Plotly-5.22-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production--ready-success)]()

</div>

---

## 📌 Overview

StockPredict is a full-stack web application built for the **Phase 2 Python Internship (Task 1)**. It pulls live historical market data, engineers technical-analysis features, trains a validated ML ensemble to forecast next-day returns, reconstructs a forward price path with uncertainty bands, and renders everything in a sleek, dark-mode-ready dashboard.

> ⚠️ **Disclaimer:** This project is for educational purposes only and is **not financial advice**. Markets are stochastic; past performance does not guarantee future results.

---

## ✨ Features

| Category | Capability |
| --- | --- |
| **Core** | Responsive homepage & dashboard (Bootstrap 5) |
| **Core** | Search by ticker symbol |
| **Core** | Historical OHLCV data via `yfinance` |
| **Core** | ML price forecasting (RandomForest + Ridge ensemble) |
| **Core** | Interactive Plotly charts with zoom/pan/hover |
| **Core** | Date-range & forecast-horizon selection |
| **Core** | Prediction confidence (directional accuracy, RMSE, MAE) |
| **Bonus** | Multi-stock comparison |
| **Bonus** | Watchlist persisted in SQLite |
| **Bonus** | Dark / light mode toggle |
| **Bonus** | Prediction-interval (uncertainty) bands |

---

## 🖼️ Screenshots

> _Add your screenshots to a `docs/` folder and update the paths below._

| Homepage | Dashboard | Comparison |
| --- | --- | --- |
| `docs/home.png` | `docs/dashboard.png` | `docs/compare.png` |

---

## 🏗️ Architecture

```text
             ┌───────────────┐      ┌──────────────┐
  Browser ─►│  Flask routes   │────►│  yfinance API  │
  (UI/JS)   │   (app.py)      │      │ (Yahoo Finance)│
             └─────┬───────┘      └──────────────┘
                   │
        ┌─────────┼─────────┐
        ▼                  ▼
  ┌───────────┐      ┌──────────┐
  │ model.py  │      │  db.py    │
  │ (ML core) │      │ (SQLite)  │
  └───────────┘      └──────────┘
```

```text
stock-prediction/
├── app.py            # Flask routes (/, /dashboard, /compare, /watchlist)
├── model.py          # Feature engineering + ensemble + forecasting
├── db.py             # SQLite watchlist helpers
├── requirements.txt  # Pinned dependencies
├── Procfile          # gunicorn entrypoint (Render/Railway/Heroku)
├── runtime.txt       # Python version pin
├── templates/        # Jinja2 views (base, index, dashboard, compare, watchlist)
└── static/           # css/style.css, js/main.js (dark mode)
```

---

## 🧠 The Prediction Model (Model Card)

| Aspect | Detail |
| --- | --- |
| **Target** | Next-day **log return** `ln(P_t / P_{t-1})` (stationary) |
| **Features** | Lagged returns (1/3/5d), SMA & EMA ratios, RSI(14), MACD histogram, Bollinger %B, rolling volatility, volume z-score |
| **Estimator** | `StandardScaler` → `RandomForestRegressor` (300 trees, depth 6) |
| **Validation** | Walk-forward `TimeSeriesSplit` (5 folds) |
| **Metrics** | Directional accuracy, RMSE, MAE (out-of-sample) |
| **Forecasting** | Iterative multi-step: predict return → compound price → re-featurize |
| **Uncertainty** | RMSE-based prediction interval scaled by √t |

**Why log returns instead of raw price?** Prices are non-stationary (they trend and have a unit root), so regressing price on a time index just fits a line and inflates apparent skill. Log returns are approximately stationary, making them a sounder modeling target; the price path is then reconstructed by compounding predicted returns.

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://gitlab.com/tony-enterprizes-group/stock-prediction.git
cd stock-prediction

# 2. Create & activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python app.py
```

Open <http://127.0.0.1:5000> in your browser.

---

## ☁️ Deployment

The repo ships with a `Procfile` and `runtime.txt` for one-click deployment.

**Render / Railway**
1. Create a new Web Service from this repo.
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn app:app`

**Local production check**
```bash
gunicorn app:app --bind 0.0.0.0:8000
```

---

## 🛣️ API / Routes

| Route | Method | Description |
| --- | --- | --- |
| `/` | GET | Homepage with search |
| `/dashboard` | GET | Historical chart + forecast (`?ticker=&start=&end=&forecast_days=`) |
| `/compare` | GET | Multi-stock comparison (`?tickers=AAPL,MSFT,GOOGL`) |
| `/watchlist` | GET/POST | View / add / remove watchlist entries |

---

## 🛠️ Tech Stack

`Python` · `Flask` · `Pandas` · `NumPy` · `scikit-learn` · `Plotly` · `yfinance` · `SQLite` · `Bootstrap 5` · `gunicorn`

---

## 🗺️ Roadmap

- [ ] User login / signup (Flask-Login)
- [ ] Export prediction reports as PDF
- [ ] News + sentiment integration
- [ ] LSTM / gradient-boosting model option
- [ ] Dockerfile + CI pipeline

---

## 📄 License

Released under the [MIT License](LICENSE).

---

<div align="center">
Dharmender Chauhan Developer
</div>
