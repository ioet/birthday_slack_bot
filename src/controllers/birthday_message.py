import asyncio
from typing import List, Tuple

from src.controllers.base import BaseController
from src.utils import date_utils


class BirthdayMessageController(BaseController):

    gif_keywords: frozenset = frozenset(('birthday', 'party', 'cumpleaños'))

    @staticmethod
    def get_birthday_employees(employees: List[dict], birthday_field) -> List[dict]:
        return (employee for employee in employees if date_utils.is_current_date(employee.get(birthday_field), '%m-%d'))

    @classmethod
    async def send(cls, employee_manager, slack_api_integration, slack_message_integration, gif_integration, templates: Tuple[str]):

        async def send_message_coro(best_matching_keyword: str, gif_search_limit: int, message: str):
            selected_gif = await gif_integration.get_random_gif(best_matching_keyword, gif_search_limit)
            await slack_message_integration.send_message(message, selected_gif.get('url'), selected_gif.get('description'))

        birthday_employees = cls.get_birthday_employees(await employee_manager.get_employees_with_birthday(),
                                                        employee_manager.integration.employee_birthday_field)
        birthday_employees_ids = await slack_api_integration.get_members_id_by_email(employee_manager.integration.get_employees_email(birthday_employees))
        templates_copy = list(templates)
        message_coros = []
        for employee_id in birthday_employees_ids:
            template = cls.choose_template(templates_copy)
            if len(templates_copy) > 1:
                templates_copy.remove(template)

            message = cls.fill_from_template(f'<@{employee_id}>', template)
            best_matching_keyword = cls.get_best_matching_template_keyword(message)
            message_coros.append(send_message_coro(best_matching_keyword, cls.gif_search_limit, message))
        await asyncio.gather(*message_coros)
