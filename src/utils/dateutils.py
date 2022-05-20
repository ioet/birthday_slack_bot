from datetime import datetime, timedelta
from src.config import EnvManager


def get_day_month(date: datetime) -> tuple:
    return date.day, date.month


def get_current_day_month(utc_hour_offset: str) -> tuple:
    current_date = datetime.utcnow() + timedelta(hours=int(utc_hour_offset))
    return get_day_month(current_date)


def get_years_difference_from_current_date(utc_hour_offset: str, date: str, date_format: str = '%Y-%m-%d') -> int:
    date = datetime.strptime(date, date_format)
    current_date = datetime.utcnow() + timedelta(hours=int(utc_hour_offset))
    return current_date.year - date.year


def is_current_date(date: str, date_format: str = '%Y-%m-%d'):
    if not date:
        return False
    current_day_month = get_current_day_month(EnvManager.UTC_HOUR_OFFSET)
    date = datetime.strptime(date, date_format)
    return current_day_month == (date.day, date.month)