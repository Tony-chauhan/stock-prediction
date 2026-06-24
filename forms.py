"""WTForms for input validation."""
import re
from datetime import date, timedelta

from wtforms import Form, StringField, DateField, IntegerField, validators
from wtforms.validators import ValidationError

from config import config


TICKER_PATTERN = re.compile(config.ALLOWED_TICKER_PATTERN)


def validate_ticker(form, field):
    if not TICKER_PATTERN.match(field.data.upper()):
        raise ValidationError('Invalid ticker format. Use 1-5 letters, optionally with .XX suffix (e.g., BRK.B)')


class DashboardForm(Form):
    ticker = StringField('Ticker', [
        validators.DataRequired(),
        validators.Length(min=1, max=10),
        validate_ticker,
    ])
    start = DateField('Start Date', [
        validators.Optional(),
    ], format='%Y-%m-%d')
    end = DateField('End Date', [
        validators.Optional(),
    ], format='%Y-%m-%d')
    forecast_days = IntegerField('Forecast Days', [
        validators.NumberRange(
            min=config.MIN_FORECAST_DAYS, 
            max=config.MAX_FORECAST_DAYS,
            message=f'Forecast days must be between {config.MIN_FORECAST_DAYS} and {config.MAX_FORECAST_DAYS}'
        ),
    ])

    def validate_end(self, field):
        if field.data and self.start.data and field.data < self.start.data:
            raise ValidationError('End date must be after start date')
        if field.data and field.data > date.today():
            raise ValidationError('End date cannot be in the future')


class CompareForm(Form):
    tickers = StringField('Tickers', [
        validators.DataRequired(),
        validators.Length(min=1, max=100),
    ])

    def validate_tickers(self, field):
        symbols = [t.strip().upper() for t in field.data.split(',') if t.strip()]
        if len(symbols) > config.MAX_TICKERS_COMPARE:
            raise ValidationError(f'Maximum {config.MAX_TICKERS_COMPARE} tickers allowed for comparison')
        for sym in symbols:
            if not TICKER_PATTERN.match(sym):
                raise ValidationError(f'Invalid ticker: {sym}')


class WatchlistForm(Form):
    ticker = StringField('Ticker', [
        validators.DataRequired(),
        validators.Length(min=1, max=10),
        validate_ticker,
    ])
    action = StringField('Action', [
        validators.AnyOf(['add', 'remove']),
    ])


class APIQuoteForm(Form):
    ticker = StringField('Ticker', [
        validators.DataRequired(),
        validate_ticker,
    ])