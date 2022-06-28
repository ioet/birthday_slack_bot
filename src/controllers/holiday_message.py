from typing import List

from src.config import EnvManager
from src.controllers.base import BaseController
from src.utils.date_utils import get_date_plus_interval


class HolidayMessageController(BaseController):

    gif_keywords: frozenset = frozenset(('holiday', 'vacation'))

    @classmethod
    def render_holiday_message(cls, holidays: List[dict], gif_integration) -> dict:
        message = '<!here> Holidays for next week:'
        holidays_message = [f'• {holiday.get("start")} : {holiday.get("name")}' for holiday in holidays]
        best_matching_keyword = cls.get_best_matching_template_keyword(message)
        selected_gif = gif_integration.get_random_gif(best_matching_keyword, cls.gif_search_limit)
        return {
            'text': 'Upcoming holidays:',
            'blocks': [
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': message
                    }
                },
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': "\n".join(holidays_message)
                    }
                },
                {
                    'type': 'image',
                    'image_url': selected_gif.get('url'),
                    'alt_text': selected_gif.get('description')
                }
            ]
        }

    @classmethod
    def send(cls, hr_integration, slack_message_integration, gif_integration):
        start = get_date_plus_interval(3, EnvManager.UTC_HOUR_OFFSET)
        end = get_date_plus_interval(30, EnvManager.UTC_HOUR_OFFSET)
        holidays = hr_integration.get_holidays(start, end)
        if holidays:
            holiday_message = cls.render_holiday_message(holidays, gif_integration)
            slack_message_integration.send_raw_message(holiday_message)
