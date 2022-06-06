import logging
from datetime import datetime, timedelta
from src.config import EnvManager

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_day_month(date: datetime) -> tuple:
    return date.day, date.month


def get_current_day_month(utc_hour_offset: str) -> tuple:
    current_date = datetime.utcnow() + timedelta(hours=int(utc_hour_offset))
    return get_day_month(current_date)


def get_years_difference_from_current_date(utc_hour_offset: str, date: str, date_format: str = '%Y-%m-%d') -> int:
    date = datetime.strptime(date, date_format)
    current_date = datetime.utcnow() + timedelta(hours=int(utc_hour_offset))
    return current_date.year - date.year


def is_current_date(date: str, date_format: str = '%Y-%m-%d') -> bool:
    if not date:
        return False

    try:
        current_day_month = get_current_day_month(EnvManager.UTC_HOUR_OFFSET)
        date = datetime.strptime(date, date_format)
    except ValueError:
       logger.warning('Date has an invalid format')
       return False

    return current_day_month == (date.day, date.month)
