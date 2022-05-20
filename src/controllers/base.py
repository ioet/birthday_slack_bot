from typing import List
from collections import OrderedDict
from random import choice, choices
from itertools import repeat


class BaseController:

    gif_keywords: frozenset = frozenset()
    gif_search_limit: int = 15

    @staticmethod
    def choose_template(templates: List[str]):
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
