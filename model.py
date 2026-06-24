"""L99 production-grade stock forecasting pipeline with caching and persistence."""
from __future__ import annotations

import hashlib
import logging
import pickle
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import diskcache as dc
import numpy as np
import pandas as pd
import yfinance as yf
from joblib import dump, load
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import config

# --------------------------------------------------------------------------- #
# Logging & Cache Setup
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)

CACHE_DIR = config.CACHE_DIR
CACHE_DIR.mkdir(exist_ok=True)
MODEL_DIR = config.MODEL_DIR
MODEL_DIR.mkdir(exist_ok=True)

# Disk cache for yfinance data
_yf_cache = dc.Cache(str(CACHE_DIR / 'yfinance'), size_limit=2**30)  # 1GB
# Disk cache for trained models
_model_cache = dc.Cache(str(CACHE_DIR / 'models'), size_limit=2**30)


# --------------------------------------------------------------------------- #
# Data Access with Caching
# --------------------------------------------------------------------------- #
def _cache_key(ticker: str, start: str, end: str) -> str:
    """Generate deterministic cache key."""
    return hashlib.sha256(f"{ticker}|{start}|{end}".encode()).hexdigest()[:32]


def get_stock_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Fetch historical OHLCV data from Yahoo Finance with caching."""
    ticker = ticker.upper().strip()
    key = _cache_key(ticker, start, end)
    
    # Check cache first
    cached = _yf_cache.get(key)
    if cached is not None:
        logger.debug("Cache hit for %s %s-%s", ticker, start, end)
        return cached.copy()
    
    logger.info("Fetching fresh data for %s %s-%s", ticker, start, end)
    try:
        df = yf.download(
            ticker, 
            start=start, 
            end=end, 
            progress=False, 
            auto_adjust=True,
            timeout=config.YFINANCE_TIMEOUT
        )
    except Exception as e:
        logger.error("yfinance download failed for %s: %s", ticker, e)
        raise ValueError(f"Failed to fetch data for '{ticker}'") from e
    
    if df is None or df.empty:
        raise ValueError(f"No data found for ticker '{ticker}' in range {start} to {end}")
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df = df.reset_index()
    
    # Cache for 24 hours
    _yf_cache.set(key, df.copy(), expire=config.CACHE_TTL_HOURS * 3600)
    return df


# --------------------------------------------------------------------------- #
# Technical Indicators / Feature Engineering
# --------------------------------------------------------------------------- #
def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    sig = macd.ewm(span=signal, adjust=False).mean()
    return macd - sig


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Construct a feature matrix with a next-day log-return target."""
    f = pd.DataFrame(index=df.index)
    close = df['Close']
    vol = df['Volume'] if 'Volume' in df else pd.Series(1.0, index=df.index)

    log_ret = np.log(close / close.shift(1))
    f['ret_1'] = log_ret
    f['ret_3'] = log_ret.rolling(3).sum()
    f['ret_5'] = log_ret.rolling(5).sum()
    f['sma_ratio'] = close / close.rolling(10).mean() - 1
    f['ema_ratio'] = close / close.ewm(span=10, adjust=False).mean() - 1
    f['rsi'] = _rsi(close)
    f['macd_hist'] = _macd(close)

    mid = close.rolling(20).mean()
    std = close.rolling(20).std()
    f['bb_pctb'] = (close - (mid - 2 * std)) / (4 * std)
    f['volatility'] = log_ret.rolling(10).std()
    f['vol_z'] = (vol - vol.rolling(20).mean()) / vol.rolling(20).std()

    # Target: next-day log return (shift -1 so row t predicts t+1)
    f['target'] = log_ret.shift(-1)
    return f.replace([np.inf, -np.inf], np.nan).dropna()


# --------------------------------------------------------------------------- #
# Model Persistence
# --------------------------------------------------------------------------- #
def _model_cache_key(ticker: str, feature_hash: str) -> str:
    return f"{ticker}_{feature_hash}"


def _get_feature_hash(feature_cols: list[str]) -> str:
    return hashlib.md5("|".join(sorted(feature_cols)).encode()).hexdigest()[:8]


def _save_model(ticker: str, model: Pipeline, feature_cols: list[str], metrics: dict) -> None:
    """Persist trained model to disk."""
    key = _model_cache_key(ticker, _get_feature_hash(feature_cols))
    model_path = MODEL_DIR / f"{key}.joblib"
    meta_path = MODEL_DIR / f"{key}.meta"
    
    dump(model, model_path)
    with open(meta_path, 'wb') as f:
        pickle.dump({
            'feature_cols': feature_cols,
            'metrics': metrics,
            'trained_at': datetime.utcnow().isoformat(),
            'ticker': ticker,
        }, f)
    logger.info("Saved model for %s to %s", ticker, model_path)


def _load_model(ticker: str, feature_cols: list[str]) -> tuple[Pipeline | None, dict | None]:
    """Load persisted model if exists and not stale."""
    key = _model_cache_key(ticker, _get_feature_hash(feature_cols))
    model_path = MODEL_DIR / f"{key}.joblib"
    meta_path = MODEL_DIR / f"{key}.meta"
    
    if not model_path.exists() or not meta_path.exists():
        return None, None
    
    try:
        with open(meta_path, 'rb') as f:
            meta = pickle.load(f)
        
        # Check if model is stale (older than MODEL_RETRAIN_DAYS)
        trained_at = datetime.fromisoformat(meta['trained_at'])
        if datetime.utcnow() - trained_at > timedelta(days=config.MODEL_RETRAIN_DAYS):
            logger.info("Model for %s is stale, will retrain", ticker)
            return None, None
        
        # Verify feature columns match
        if meta['feature_cols'] != feature_cols:
            logger.info("Feature columns changed for %s, will retrain", ticker)
            return None, None
        
        model = load(model_path)
        logger.info("Loaded cached model for %s (trained %s)", ticker, trained_at)
        return model, meta['metrics']
    except Exception as e:
        logger.warning("Failed to load model for %s: %s", ticker, e)
        return None, None


# --------------------------------------------------------------------------- #
# Model Training & Evaluation
# --------------------------------------------------------------------------- #
def _build_estimator() -> Pipeline:
    return Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestRegressor(
            n_estimators=100, max_depth=6, min_samples_leaf=20,
            n_jobs=-1, random_state=42)),
    ])


def _walk_forward_metrics(X: np.ndarray, y: np.ndarray) -> dict:
    tscv = TimeSeriesSplit(n_splits=3)
    dir_acc, rmses, maes = [], [], []
    for tr, te in tscv.split(X):
        est = _build_estimator()
        est.fit(X[tr], y[tr])
        pred = est.predict(X[te])
        dir_acc.append(float(np.mean(np.sign(pred) == np.sign(y[te]))))
        rmses.append(float(np.sqrt(mean_squared_error(y[te], pred))))
        maes.append(float(mean_absolute_error(y[te], pred)))
    return {
        'directional_accuracy': round(np.mean(dir_acc) * 100, 2),
        'rmse': float(np.mean(rmses)),
        'mae': float(np.mean(maes)),
    }


# --------------------------------------------------------------------------- #
# Main Prediction Function
# --------------------------------------------------------------------------- #
def predict_prices(df: pd.DataFrame, forecast_days: int = 30, ticker: str = "UNKNOWN") -> dict:
    """Train on engineered features and forecast a future price path with bands.
    
    Returns a dict with future_dates, future_preds, lower, upper, confidence
    (directional accuracy %), rmse, mae.
    """
    if forecast_days < config.MIN_FORECAST_DAYS or forecast_days > config.MAX_FORECAST_DAYS:
        raise ValueError(f"forecast_days must be between {config.MIN_FORECAST_DAYS} and {config.MAX_FORECAST_DAYS}")
    
    feats = build_features(df)
    if len(feats) < 60:
        raise ValueError('Not enough data to train (need ~60+ rows).')
    
    feature_cols = [c for c in feats.columns if c != 'target']
    X = feats[feature_cols].values
    y = feats['target'].values
    
    # Try to load cached model
    cached_model, cached_metrics = _load_model(ticker, feature_cols)
    
    if cached_model is not None and cached_metrics is not None:
        est = cached_model
        metrics = cached_metrics
    else:
        # Train new model
        metrics = _walk_forward_metrics(X, y)
        est = _build_estimator()
        est.fit(X, y)
        _save_model(ticker, est, feature_cols, metrics)
    
    # Iterative multi-step forecast
    work = df.copy()
    last_price = float(work['Close'].iloc[-1])
    preds, lowers, uppers = [], [], []
    sigma = metrics['rmse']  # per-step return std proxy
    
    price = last_price
    for step in range(1, forecast_days + 1):
        cur_feats = build_features(work)
        if cur_feats.empty:
            break
        # Ensure feature columns match training
        missing_cols = set(feature_cols) - set(cur_feats.columns)
        if missing_cols:
            logger.warning("Missing feature columns at step %d: %s", step, missing_cols)
            break
        x_last = cur_feats[feature_cols].values[-1].reshape(1, -1)
        r_hat = float(est.predict(x_last)[0])
        price = price * np.exp(r_hat)
        
        # sqrt-time scaled 1-sigma band on the price (log-normal approximation)
        band = price * sigma * np.sqrt(step)
        preds.append(price)
        lowers.append(price - band)
        uppers.append(price + band)
        
        # Append synthetic row so indicators roll forward
        new_row = work.iloc[[-1]].copy()
        new_row['Close'] = price
        if 'Open' in new_row: new_row['Open'] = price
        if 'High' in new_row: new_row['High'] = price
        if 'Low' in new_row: new_row['Low'] = price
        work = pd.concat([work, new_row], ignore_index=True)
    
    # Generate future business days
    future_dates = pd.bdate_range(
        start=df['Date'].iloc[-1], periods=len(preds) + 1, freq='B'
    )[1:]
    
    return {
        'future_dates': future_dates,
        'future_preds': np.array(preds),
        'lower': np.array(lowers),
        'upper': np.array(uppers),
        'confidence': metrics['directional_accuracy'],
        'rmse': round(metrics['rmse'], 5),
        'mae': round(metrics['mae'], 5),
    }


# --------------------------------------------------------------------------- #
# Cache Management
# --------------------------------------------------------------------------- #
def clear_cache() -> dict:
    """Clear all caches. Returns stats."""
    yf_count = len(_yf_cache)
    model_count = len(_model_cache)
    _yf_cache.clear()
    _model_cache.clear()
    # Also clear joblib models
    for f in MODEL_DIR.glob("*"):
        f.unlink()
    return {'yfinance_cleared': yf_count, 'models_cleared': model_count}


def get_cache_stats() -> dict:
    return {
        'yfinance_entries': len(_yf_cache),
        'yfinance_size_mb': _yf_cache.volume() / 1024 / 1024,
        'model_entries': len(_model_cache),
        'model_size_mb': _model_cache.volume() / 1024 / 1024,
    }