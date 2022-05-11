from typing import List, Tuple

from src.controllers.base import BaseController
from src.config import EnvManager
from src.utils import dateutils


class BirthdayMessageController(BaseController):

    gif_keywords: frozenset = frozenset(('birthday', 'party', 'cumpleaños'))

    @staticmethod
    def get_birthday_employees(employees: List[dict], birthday_field) -> List[dict]:
        def is_birthday(birthday: str):
            if not birthday:
                return False
            delimiter = '-'
            current_day_month = dateutils.get_current_day_month(EnvManager.UTC_HOUR_OFFSET)
            birthday_day_month: tuple = tuple(int(value) for value in reversed(birthday.split(delimiter)))
            return birthday_day_month == current_day_month

        return [employee for employee in employees if is_birthday(employee.get(birthday_field))]

    @classmethod
    def send(cls, hr_integration, slack_api_integration, slack_message_integration, gif_integration, templates: Tuple[str]):
        birthday_employees = cls.get_birthday_employees(hr_integration.get_employees_with_birthday(), hr_integration.employee_birthday_field)
        birthday_employees_ids = slack_api_integration.get_members_id_by_email(hr_integration.get_employees_email(birthday_employees))
        templates_copy = list(templates)
        for employee_id in birthday_employees_ids:
            template = cls.choose_template(templates_copy)
            if len(templates_copy) > 1:
                templates_copy.remove(template)

            message = cls.fill_from_template(f'<@{employee_id}>', template)
            best_matching_keyword = cls.get_best_matching_template_keyword(message)
            selected_gif = gif_integration.get_random_gif(best_matching_keyword, cls.gif_search_limit)
            slack_message_integration.send_message(message, selected_gif.get('url'), selected_gif.get('description'))
