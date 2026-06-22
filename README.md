# ⏫ Stock Market Prediction Web App

Internship Task 1 (Phase 2 – Python). A Flask web application that fetches live
historical stock data, forecasts future prices with a machine learning model,
and visualizes everything in an interactive, responsive dashboard.

## Features

- Attractive, responsive homepage and dashboard (Bootstrap 5)
- Search stocks by ticker symbol
- Historical price data via `yfinance` (Yahoo Finance)
- Future price prediction using **Linear Regression** (scikit-learn)
- Interactive Plotly charts
- Date range and forecast-horizon selection
- Prediction results with an **R2-based confidence indicator**
- Multi-stock comparison
- Watchlist backed by **SQLite**
- Dark / light mode toggle

## Tech Stack

Python, Flask, Pandas, NumPy, scikit-learn, Plotly, yfinance, SQLite, Bootstrap 5.

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000

## Prediction Model

The app trains a **Linear Regression** model that maps a sequential time index
to the closing price. Data is split chronologically (80/20, no shuffling) so the
model is validated on the most recent unseen prices. The held-out **R2 score** is
reported as a confidence indicator, and the fitted trend is extrapolated forward
over the chosen forecast horizon to produce future price estimates.

## Project Structure

```
app.py          Flask routes
model.py        Data fetching + ML prediction
db.py           SQLite watchlist helpers
templates/      Jinja2 HTML templates
static/         CSS + JS (dark mode)
```
