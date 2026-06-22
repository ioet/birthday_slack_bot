import asyncio
import logging
from typing import List, Tuple

from src.controllers.base import BaseController
from src.utils import date_utils

logger = logging.getLogger(__name__)


class BirthdayMessageController(BaseController):

    gif_keywords: frozenset = frozenset(('birthday', 'party', 'cumpleaños'))
    default_gif_keyword: str = 'birthday'

    @staticmethod
    def get_birthday_employees(employees: List[dict], birthday_field) -> List[dict]:
        return (employee for employee in employees if date_utils.is_current_date(employee.get(birthday_field), '%m-%d'))

    @classmethod
    async def _build_message(
        cls,
        employee: dict,
        employee_id: str,
        employee_manager,
        templates: Tuple[str],
        templates_copy: List[str],
        message_generator,
    ) -> str:
        slack_mention = f'<@{employee_id}>'
        employee_name = employee.get('fullName1') or employee.get(
            employee_manager.integration.employee_email_field,
            'teammate',
        )

        if message_generator:
            try:
                return await message_generator.generate_birthday_message(employee_name, slack_mention)
            except Exception as error:
                logger.warning('Bedrock message generation failed, using template fallback: %s', error)

        template = cls.choose_template(templates_copy)
        if len(templates_copy) > 1:
            templates_copy.remove(template)
        return cls.fill_from_template(slack_mention, template)

    @classmethod
    async def send(
        cls,
        employee_manager,
        slack_api_integration,
        slack_message_integration,
        gif_integration,
        templates: Tuple[str],
        message_generator=None,
    ):

        async def send_message_coro(gif_search_limit: int, message: str):
            selected_gif = await gif_integration.get_random_gif(cls.default_gif_keyword, gif_search_limit)
            await slack_message_integration.send_message(message, selected_gif.get('url'), selected_gif.get('description'))

        birthday_employees = list(cls.get_birthday_employees(
            await employee_manager.get_employees_with_birthday(),
            employee_manager.integration.employee_birthday_field,
        ))
        birthday_employees_ids = list(await slack_api_integration.get_members_id_by_email(
            employee_manager.integration.get_employees_email(birthday_employees)
        ))
        templates_copy = list(templates)
        message_coros = []
        for employee, employee_id in zip(birthday_employees, birthday_employees_ids):
            message = await cls._build_message(
                employee,
                employee_id,
                employee_manager,
                templates,
                templates_copy,
                message_generator,
            )
            message_coros.append(send_message_coro(cls.gif_search_limit, message))
        await asyncio.gather(*message_coros)
