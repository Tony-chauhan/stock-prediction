"""Stock Market Prediction web application (Flask).

Routes:
    /                 Homepage with search form
    /dashboard        Historical chart + prediction for a single ticker
    /compare          Multi-stock comparison chart
    /watchlist        Add/remove/view watchlist (SQLite)
"""
import datetime as dt

import plotly.graph_objects as go
import plotly.io as pio
from flask import Flask, render_template, request, redirect, url_for

from model import get_stock_data, predict_prices
import db

app = Flask(__name__)
db.init_db()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    ticker = request.args.get('ticker', 'AAPL').upper().strip()
    start = request.args.get('start') or (dt.date.today() - dt.timedelta(days=365)).isoformat()
    end = request.args.get('end') or dt.date.today().isoformat()
    forecast_days = int(request.args.get('forecast_days', 30))

    error = None
    chart_html = pred_chart_html = None
    confidence = last_price = next_price = None

    try:
        df = get_stock_data(ticker, start, end)
        future_dates, future_preds, confidence = predict_prices(df, forecast_days)

        hist = go.Figure()
        hist.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='Close', mode='lines'))
        hist.update_layout(title=f'{ticker} Historical Close', template='plotly_dark',
                           xaxis_title='Date', yaxis_title='Price (USD)', height=420)
        chart_html = pio.to_html(hist, full_html=False, include_plotlyjs='cdn')

        pred = go.Figure()
        pred.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='Historical', mode='lines'))
        pred.add_trace(go.Scatter(x=future_dates, y=future_preds, name='Forecast',
                                  mode='lines', line=dict(dash='dash')))
        pred.update_layout(title=f'{ticker} {forecast_days}-Day Forecast', template='plotly_dark',
                           xaxis_title='Date', yaxis_title='Price (USD)', height=420)
        pred_chart_html = pio.to_html(pred, full_html=False, include_plotlyjs=False)

        last_price = round(float(df['Close'].iloc[-1]), 2)
        next_price = round(float(future_preds[-1]), 2)
    except Exception as exc:  # noqa: BLE001 - surface friendly message to UI
        error = str(exc)

    return render_template('dashboard.html', ticker=ticker, start=start, end=end,
                           forecast_days=forecast_days, chart_html=chart_html,
                           pred_chart_html=pred_chart_html, confidence=confidence,
                           last_price=last_price, next_price=next_price, error=error,
                           watchlist=db.get_watchlist())


@app.route('/compare')
def compare():
    tickers = request.args.get('tickers', 'AAPL,MSFT,GOOGL')
    symbols = [t.strip().upper() for t in tickers.split(',') if t.strip()]
    start = (dt.date.today() - dt.timedelta(days=365)).isoformat()
    end = dt.date.today().isoformat()

    error = None
    chart_html = None
    try:
        fig = go.Figure()
        for sym in symbols:
            df = get_stock_data(sym, start, end)
            fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name=sym, mode='lines'))
        fig.update_layout(title='Stock Comparison (Close)', template='plotly_dark',
                          xaxis_title='Date', yaxis_title='Price (USD)', height=500)
        chart_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
    except Exception as exc:  # noqa: BLE001
        error = str(exc)

    return render_template('compare.html', tickers=tickers, chart_html=chart_html, error=error)


@app.route('/watchlist', methods=['GET', 'POST'])
def watchlist():
    if request.method == 'POST':
        action = request.form.get('action')
        ticker = request.form.get('ticker', '').strip()
        if ticker and action == 'add':
            db.add_to_watchlist(ticker)
        elif ticker and action == 'remove':
            db.remove_from_watchlist(ticker)
        return redirect(url_for('watchlist'))
    return render_template('watchlist.html', watchlist=db.get_watchlist())


if __name__ == '__main__':
    app.run(debug=True)
