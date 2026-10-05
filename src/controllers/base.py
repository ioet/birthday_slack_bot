import logging
from typing import List
from collections import OrderedDict
from random import choice, choices
from itertools import repeat

logger = logging.getLogger(__name__)


class BaseController:

    gif_keywords: frozenset = frozenset()
    gif_search_limit: int = 15
    gif_gender_check_max_attempts: int = 10

    @staticmethod
    def choose_template(templates: List[str]) -> str:
        return choice(templates)

    @staticmethod
    def fill_from_template(username: str, template: str) -> str:
        return template.format(username)

    @classmethod
    def get_best_matching_template_keyword(cls, template: str) -> List[str]:
        characters_to_ignore = '.!?'
        template = template.replace('\n', ' ').strip(characters_to_ignore).split(' ')
        searchable_template = [word.strip(characters_to_ignore) for word in template]
        keyword_count = OrderedDict(zip(cls.gif_keywords, repeat(0, len(cls.gif_keywords))))
        total_count = 0
        for word in searchable_template:
            if (lower_word := word.lower()) in keyword_count:
                keyword_count[lower_word] += 1
                total_count += 1

        if total_count == 0:
            return choice(list(keyword_count.keys()))

        return choices(list(keyword_count.keys()), weights=[count / total_count for count in keyword_count.values()])

    @classmethod
    async def get_gender_agnostic_gif(
        cls,
        gif_integration,
        message_generator,
        search_keyword: str,
        gif_search_limit: int,
    ) -> dict:
        last_gif = {'url': '', 'description': ''}
        seen_urls = set()

        for attempt in range(cls.gif_gender_check_max_attempts):
            selected_gif = await gif_integration.get_random_gif(search_keyword, gif_search_limit)
            last_gif = selected_gif or last_gif
            gif_url = (selected_gif or {}).get('url', '')

            if gif_url and gif_url in seen_urls:
                continue
            if gif_url:
                seen_urls.add(gif_url)

            if not message_generator:
                return selected_gif

            try:
                is_gender_agnostic = await message_generator._ensure_gender_agnostic_gif(
                    selected_gif.get('description', ''),
                    selected_gif.get('preview_url') or gif_url,
                )
            except Exception as error:
                logger.warning('Gender-agnostic GIF check failed, trying another GIF: %s', error)
                continue

            if is_gender_agnostic:
                return selected_gif

            logger.info(
                'Rejected gender-specific GIF (attempt %s/%s)',
                attempt + 1,
                cls.gif_gender_check_max_attempts,
            )

        logger.warning(
            'No gender-agnostic GIF found after %s attempts, using last candidate',
            cls.gif_gender_check_max_attempts,
        )
        return last_gif
