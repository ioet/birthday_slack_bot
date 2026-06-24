import logging
from typing import List

from src.config import EnvManager
from src.controllers.base import BaseController
from src.utils.date_utils import get_date_plus_interval

logger = logging.getLogger(__name__)


class HolidayMessageController(BaseController):

    gif_keywords: frozenset = frozenset(('holiday', 'vacation'))
    default_gif_keyword: str = 'holiday'

    @classmethod
    def _build_static_message(cls, holidays: List[dict]) -> str:
        message = '<!here> Holidays for the next 2 weeks:'
        holidays_message = [f'• {holiday.get("start")} : {holiday.get("name")}' for holiday in holidays]
        return message + '\n' + '\n'.join(holidays_message)

    @classmethod
    async def _build_message(cls, holidays: List[dict], message_generator) -> str:
        if message_generator:
            try:
                return await message_generator.generate_holiday_message(holidays)
            except Exception as error:
                logger.warning('Bedrock message generation failed, using static fallback: %s', error)
        return cls._build_static_message(holidays)

    @classmethod
    def render_holiday_message(cls, text_message: str, image_url: str, alt_text: str) -> dict:
        return {
            'text': 'Upcoming holidays:',
            'blocks': [
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': text_message,
                    },
                },
                {
                    'type': 'image',
                    'image_url': image_url,
                    'alt_text': alt_text,
                },
            ],
        }

    @classmethod
    async def send(cls, hr_integration, slack_message_integration, gif_integration, message_generator=None) -> None:
        start = get_date_plus_interval(days=3, utc_hour_offset=EnvManager.UTC_HOUR_OFFSET)
        end = get_date_plus_interval(days=15, utc_hour_offset=EnvManager.UTC_HOUR_OFFSET)
        holidays = await hr_integration.get_holidays(start, end)
        if holidays:
            text_message = await cls._build_message(holidays, message_generator)
            selected_gif = await gif_integration.get_random_gif(cls.default_gif_keyword, cls.gif_search_limit)
            holiday_message = cls.render_holiday_message(
                text_message,
                selected_gif.get('url'),
                selected_gif.get('description'),
            )
            await slack_message_integration.send_raw_message(holiday_message)
