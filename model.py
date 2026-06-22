"""Machine learning model for stock price prediction.

Uses Linear Regression on a time index to forecast future closing prices.
The model returns an R2-based confidence indicator computed on a held-out
(time-ordered) test split.
"""
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score


def get_stock_data(ticker, start, end):
    """Fetch historical OHLCV data from Yahoo Finance."""
    df = yf.download(ticker, start=start, end=end, progress=False)
    if df is None or df.empty:
        raise ValueError(f"No data found for ticker '{ticker}'")
    # Flatten multi-index columns that yfinance returns for single tickers
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.reset_index()
    return df


def predict_prices(df, forecast_days=30):
    """Train a regression model on historical closes and forecast future prices.

    Returns:
        future_dates (pd.DatetimeIndex): business days being forecast
        future_preds (np.ndarray): predicted closing prices
        confidence (float): R2 score (%) on the held-out test set
    """
    data = df[['Close']].copy().dropna()
    data['day_index'] = np.arange(len(data))

    X = data[['day_index']].values
    y = data['Close'].values.ravel()

    if len(data) < 10:
        raise ValueError("Not enough data to train the model.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    model = LinearRegression()
    model.fit(X_train, y_train)

    confidence = round(float(r2_score(y_test, model.predict(X_test))) * 100, 2)

    future_idx = np.arange(len(data), len(data) + forecast_days).reshape(-1, 1)
    future_preds = model.predict(future_idx)
    future_dates = pd.date_range(
        start=df['Date'].iloc[-1], periods=forecast_days + 1, freq='B'
    )[1:]

    return future_dates, future_preds, confidence
