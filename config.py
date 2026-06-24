"""Configuration settings for StockPredict."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

class Config:
    """Base configuration."""
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    # Cache settings
    CACHE_DIR = BASE_DIR / 'cache'
    CACHE_TTL_HOURS = 24
    
    # Model settings
    MODEL_DIR = BASE_DIR / 'models'
    MODEL_RETRAIN_DAYS = 7
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = 30
    
    # Validation
    MAX_FORECAST_DAYS = 180
    MIN_FORECAST_DAYS = 1
    MAX_TICKERS_COMPARE = 6
    
    # Security
    ALLOWED_TICKER_PATTERN = r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$'
    
    # External services
    CLEARBIT_BASE_URL = 'https://logo.clearbit.com'
    YFINANCE_TIMEOUT = 10


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}[os.environ.get('FLASK_ENV', 'development')]