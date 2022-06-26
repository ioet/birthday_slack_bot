from typing import List


class HolidayMessageController:

    @staticmethod
    def render_holiday_message(holidays: List[dict]) -> dict:
        pass

    @classmethod
    def send(cls, hr_integration, slack_message_integration):
        start = 'get_todays_date()'
        end = 'get_todays_date()+7'
        holidays = hr_integration.get_holidays(start, end)
        if holidays:
            holiday_message = cls.render_holiday_message()
            slack_message_integration.send_raw_mesage(holiday_message)
