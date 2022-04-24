from datetime import datetime, timedelta
from src.config import EnvManager


def get_day_month(date: datetime) -> tuple:
    return date.day, date.month


def get_current_day_month(utc_hour_offset: str = EnvManager.UTC_HOUR_OFFSET) -> tuple:
    current_date = datetime.utcnow() + timedelta(hours=int(utc_hour_offset))
    return get_day_month(current_date)
