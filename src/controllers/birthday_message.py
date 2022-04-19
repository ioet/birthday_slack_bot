from typing import List, Tuple
from collections import OrderedDict
from itertools import repeat
from random import choice, choices
from src.utils import dateutils


class BirthdayMessageController:

    gif_keywords: frozenset = frozenset(('birthday', 'party'))
    gif_search_limit: int = 8

    @staticmethod
    def choose_template(templates: tuple):
        return choice(templates)

    @staticmethod
    def fill_from_template(username: str, template: str) -> str:
        return template.format(username)

    @classmethod
    def get_best_matchig_template_keyword(cls, template: str) -> str:
        searchable_template = template.replace('\n', ' ').strip('.!?').split(' ')
        keyword_count = OrderedDict(zip(cls.gif_keywords, repeat(0, len(cls.gif_keywords))))
        total_count = 0
        for word in searchable_template:
            if (lower_word := word.lower()) in keyword_count:
                keyword_count[lower_word] += 1
                total_count += 1
        return choices(list(keyword_count.keys()), weights=[count/total_count for count in keyword_count.values()])

    @staticmethod
    def get_birthday_employees(users: List[dict]):

        def is_birthday(birthday: str, current_day_month: tuple):
            return True

        current_day_month = dateutils.get_current_day_month('-5')
        # We might need to store the slack username in bamboo
        return [user.get('slackUsername') for user in users if is_birthday(user.get('birthday'), current_day_month)]

    @classmethod
    def send(cls, hr_integration, slack_integration, gif_integration, templates: Tuple[str]):
        birthday_employees = cls.get_birthday_employees(hr_integration.get_employees())
        templates_copy = list(templates)
        for employee in birthday_employees:
            template = cls.choose_template(templates_copy)
            if len(templates_copy) > 1:
                templates_copy.remove(template)

            message = cls.fill_from_template(employee, template)
            best_matching_keyword = cls.get_best_matchig_template_keyword(message)
            selected_gif = gif_integration.get_random_gif(best_matching_keyword, cls.gif_search_limit)
            slack_integration.send_message(message, selected_gif.get('url'), selected_gif.get('description'))
