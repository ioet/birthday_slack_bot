from typing import List, Tuple

from src.controllers.base import BaseController
from src.config import EnvManager
from src.utils import date_utils


class AnniversaryMessageController(BaseController):

    gif_keywords: frozenset = frozenset(('work', 'party'))

    @staticmethod
    def fill_from_template(username: str, anniversary_years: str, template: str) -> str:
        return template.format(username=username, anniversary_years=anniversary_years)

    @staticmethod
    def get_anniversary_employees(employees: List[dict], anniversary_field) -> List[dict]:
        return [employee for employee in employees if date_utils.is_current_date(employee.get(anniversary_field))]

    @classmethod
    def send(cls, hr_integration, slack_api_integration, slack_message_integration, gif_integration, templates: Tuple[str]):
        anniversary_employees = cls.get_anniversary_employees(hr_integration.get_employees_with_anniversary(), hr_integration.employee_hire_field)
        templates_copy = list(templates)
        for employee in anniversary_employees:
            employee_id = slack_api_integration.get_member_id_by_email(employee.get(hr_integration.employee_email_field))
            employee_hire_date = employee.get(hr_integration.employee_hire_field)
            employee_years_anniversary = date_utils.get_years_difference_from_current_date(EnvManager.UTC_HOUR_OFFSET, employee_hire_date)
            template = cls.choose_template(templates_copy)
            if len(templates_copy) > 1:
                templates_copy.remove(template)

            message = cls.fill_from_template(f'<@{employee_id}>', str(employee_years_anniversary), template)
            best_matching_keyword = cls.get_best_matching_template_keyword(message)
            selected_gif = gif_integration.get_random_gif(best_matching_keyword, cls.gif_search_limit)
            slack_message_integration.send_message(message, selected_gif.get('url'), selected_gif.get('description'))
