"""Stock Market Prediction web application (Flask).

Routes:
    /                 Homepage with search form and featured stocks
    /dashboard        Historical chart + prediction for a single ticker
    /compare          Multi-stock comparison chart
    /watchlist        Add/remove/view watchlist (SQLite)
    /api/v1/quote/<ticker>  JSON quote snapshot
    /health           Liveness probe
"""
from __future__ import annotations

import datetime as dt
import logging
import os

import plotly.graph_objects as go
import plotly.io as pio
from flask import Flask, render_template, request, redirect, url_for, jsonify

from model import get_stock_data, predict_prices
import db

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
db.init_db()

# ---------------------------------------------------------------------------
# Company metadata (logo via Clearbit CDN — no API key needed)
# ---------------------------------------------------------------------------
COMPANY_INFO: dict[str, dict] = {
    'AAPL':  {'name': 'Apple Inc.',            'sector': 'Technology',       'domain': 'apple.com',      'country': 'US'},
    'MSFT':  {'name': 'Microsoft Corporation', 'sector': 'Technology',       'domain': 'microsoft.com',  'country': 'US'},
    'GOOGL': {'name': 'Alphabet Inc.',         'sector': 'Communication',    'domain': 'google.com',     'country': 'US'},
    'AMZN':  {'name': 'Amazon.com Inc.',       'sector': 'Consumer Cyclical','domain': 'amazon.com',     'country': 'US'},
    'TSLA':  {'name': 'Tesla Inc.',            'sector': 'Consumer Cyclical','domain': 'tesla.com',      'country': 'US'},
    'NVDA':  {'name': 'NVIDIA Corporation',    'sector': 'Technology',       'domain': 'nvidia.com',     'country': 'US'},
    'META':  {'name': 'Meta Platforms Inc.',   'sector': 'Communication',    'domain': 'meta.com',       'country': 'US'},
    'BRK.B': {'name': 'Berkshire Hathaway',    'sector': 'Financials',       'domain': 'berkshirehathaway.com', 'country': 'US'},
    'JPM':   {'name': 'JPMorgan Chase',        'sector': 'Financials',       'domain': 'jpmorganchase.com', 'country': 'US'},
    'V':     {'name': 'Visa Inc.',             'sector': 'Financials',       'domain': 'visa.com',       'country': 'US'},
    'WMT':   {'name': 'Walmart Inc.',          'sector': 'Consumer Staples', 'domain': 'walmart.com',    'country': 'US'},
    'JNJ':   {'name': 'Johnson & Johnson',     'sector': 'Healthcare',       'domain': 'jnj.com',        'country': 'US'},
}

FEATURED = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'JPM']


def get_company(ticker: str) -> dict:
    """Return company metadata + Clearbit logo URL for a ticker."""
    info = COMPANY_INFO.get(ticker.upper(), {})
    domain = info.get('domain', '')
    logo_url = f'https://logo.clearbit.com/{domain}' if domain else ''
    return {
        'name': info.get('name', ticker),
        'sector': info.get('sector', ''),
        'country': info.get('country', ''),
        'domain': domain,
        'logo_url': logo_url,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    featured = [{'ticker': t, **get_company(t)} for t in FEATURED]
    return render_template('index.html', featured=featured)


@app.route('/dashboard')
def dashboard():
    ticker = request.args.get('ticker', 'AAPL').upper().strip()
    start = request.args.get('start') or (dt.date.today() - dt.timedelta(days=365)).isoformat()
    end = request.args.get('end') or dt.date.today().isoformat()
    forecast_days = int(request.args.get('forecast_days', 30))

    company = get_company(ticker)
    error = None
    chart_html = pred_chart_html = None
    confidence = last_price = next_price = None
    rmse = mae = None

    try:
        df = get_stock_data(ticker, start, end)
        result = predict_prices(df, forecast_days, ticker=ticker)
        future_dates = result['future_dates']
        future_preds = result['future_preds']
        lower, upper = result['lower'], result['upper']
        confidence = result['confidence']
        rmse, mae = result['rmse'], result['mae']

        # Historical chart
        hist = go.Figure()
        hist.add_trace(go.Scatter(
            x=df['Date'], y=df['Close'], name='Close', mode='lines',
            line=dict(color='#6366f1', width=2),
        ))
        hist.update_layout(
            title=f'{ticker} — Historical Close Price',
            template='plotly_dark',
            xaxis_title='Date', yaxis_title='Price (USD)', height=420,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        chart_html = pio.to_html(hist, full_html=False, include_plotlyjs='cdn')

        # Prediction chart
        pred = go.Figure()
        pred.add_trace(go.Scatter(
            x=df['Date'], y=df['Close'], name='Historical', mode='lines',
            line=dict(color='#6366f1', width=2),
        ))
        pred.add_trace(go.Scatter(
            x=future_dates, y=upper, name='Upper Band',
            mode='lines', line=dict(width=0), showlegend=False,
        ))
        pred.add_trace(go.Scatter(
            x=future_dates, y=lower, name='Confidence Band',
            mode='lines', line=dict(width=0), fill='tonexty',
            fillcolor='rgba(99,102,241,0.2)',
        ))
        pred.add_trace(go.Scatter(
            x=future_dates, y=future_preds, name='Forecast',
            mode='lines', line=dict(dash='dash', color='#a855f7', width=2),
        ))
        pred.update_layout(
            title=f'{ticker} — {forecast_days}-Day ML Forecast',
            template='plotly_dark',
            xaxis_title='Date', yaxis_title='Price (USD)', height=420,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        pred_chart_html = pio.to_html(pred, full_html=False, include_plotlyjs=False)

        last_price = round(float(df['Close'].iloc[-1]), 2)
        next_price = round(float(future_preds[-1]), 2)
        logger.info('Dashboard OK: %s  last=%.2f  forecast(%dd)=%.2f', ticker, last_price, forecast_days, next_price)

    except Exception as exc:
        logger.warning('Dashboard error for %s: %s', ticker, exc)
        error = str(exc)

    return render_template(
        'dashboard.html',
        ticker=ticker, start=start, end=end,
        forecast_days=forecast_days,
        chart_html=chart_html, pred_chart_html=pred_chart_html,
        confidence=confidence, last_price=last_price, next_price=next_price,
        error=error, rmse=rmse, mae=mae,
        watchlist=db.get_watchlist(),
        company=company,
    )


@app.route('/compare')
def compare():
    tickers = request.args.get('tickers', 'AAPL,MSFT,GOOGL')
    symbols = [t.strip().upper() for t in tickers.split(',') if t.strip()]
    start = (dt.date.today() - dt.timedelta(days=365)).isoformat()
    end = dt.date.today().isoformat()

    error = None
    chart_html = None
    companies = [{'ticker': s, **get_company(s)} for s in symbols]

    try:
        fig = go.Figure()
        colors = ['#6366f1', '#a855f7', '#06b6d4', '#22c55e', '#f59e0b', '#ef4444']
        for i, sym in enumerate(symbols):
            df = get_stock_data(sym, start, end)
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df['Close'], name=sym, mode='lines',
                line=dict(color=colors[i % len(colors)], width=2),
            ))
        fig.update_layout(
            title='Stock Comparison — Close Price (1 Year)',
            template='plotly_dark',
            xaxis_title='Date', yaxis_title='Price (USD)', height=520,
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        )
        chart_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
    except Exception as exc:
        logger.warning('Compare error: %s', exc)
        error = str(exc)

    return render_template('compare.html', tickers=tickers, chart_html=chart_html,
                           error=error, companies=companies)


@app.route('/watchlist', methods=['GET', 'POST'])
def watchlist():
    if request.method == 'POST':
        action = request.form.get('action')
        ticker = request.form.get('ticker', '').strip().upper()
        if ticker and action == 'add':
            db.add_to_watchlist(ticker)
        elif ticker and action == 'remove':
            db.remove_from_watchlist(ticker)
        return redirect(url_for('watchlist'))
    items = [{'ticker': t, **get_company(t)} for t in db.get_watchlist()]
    return render_template('watchlist.html', watchlist=db.get_watchlist(), items=items)


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
@app.route('/api/v1/quote/<ticker>')
def api_quote(ticker: str):
    ticker = ticker.upper().strip()
    try:
        end = dt.date.today().isoformat()
        start = (dt.date.today() - dt.timedelta(days=5)).isoformat()
        df = get_stock_data(ticker, start, end)
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else last
        close = float(last['Close'])
        prev_close = float(prev['Close'])
        change = close - prev_close
        change_pct = change / prev_close * 100
        company = get_company(ticker)
        return jsonify({
            'ticker': ticker,
            'name': company['name'],
            'logo_url': company['logo_url'],
            'close': round(close, 2),
            'change': round(change, 2),
            'change_pct': round(change_pct, 2),
            'date': str(last['Date'].date() if hasattr(last['Date'], 'date') else last['Date']),
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 404


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': dt.datetime.utcnow().isoformat()})


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    logger.error('500: %s', e)
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)
