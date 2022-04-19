from datetime import datetime, timedelta


def get_day_month(date: datetime) -> tuple:
    return date.day, date.month


def get_current_day_month(utc_hour_offset: str) -> tuple:
    current_date = datetime.utcnow() + timedelta(int(utc_hour_offset))
    return get_day_month(current_date)
