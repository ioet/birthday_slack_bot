from typing import List

from src.config import EnvManager
from src.controllers.base import BaseController
from src.utils.date_utils import get_date_plus_interval


class HolidayMessageController(BaseController):

    gif_keywords: frozenset = frozenset(('holiday', 'vacation'))

    @classmethod
    def render_holiday_message(cls, holidays: List[dict], image_url: str, alt_text: str) -> dict:
        message = '<!here> Holidays for next week:'
        holidays_message = [f'• {holiday.get("start")} : {holiday.get("name")}' for holiday in holidays]
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
                    'image_url': image_url,
                    'alt_text': alt_text
                }
            ]
        }

    @classmethod
    def send(cls, hr_integration, slack_message_integration, gif_integration) -> None:
        start = get_date_plus_interval(days=3, utc_hour_offset=EnvManager.UTC_HOUR_OFFSET)
        end = get_date_plus_interval(days=10, utc_hour_offset=EnvManager.UTC_HOUR_OFFSET)
        holidays = hr_integration.get_holidays(start, end)
        if holidays:
            best_matching_keyword = cls.get_best_matching_template_keyword(' '.join(cls.gif_keywords))
            selected_gif = gif_integration.get_random_gif(best_matching_keyword, cls.gif_search_limit)
            holiday_message = cls.render_holiday_message(holidays, selected_gif.get('url'), selected_gif.get('description'))
            slack_message_integration.send_raw_message(holiday_message)
