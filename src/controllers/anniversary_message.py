import asyncio
import logging
from typing import List, Tuple

from src.controllers.base import BaseController
from src.config import EnvManager
from src.utils import date_utils

logger = logging.getLogger(__name__)


class AnniversaryMessageController(BaseController):

    gif_keywords: frozenset = frozenset(('dance', 'party', 'celebrate'))
    default_gif_keyword: str = 'celebrate'

    @staticmethod
    def fill_from_template(username: str, anniversary_years: str, template: str) -> str:
        return template.format(username=username, anniversary_years=anniversary_years)

    @staticmethod
    def get_anniversary_employees(employees: List[dict], anniversary_field) -> List[dict]:
        return (employee for employee in employees if date_utils.is_current_date(employee.get(anniversary_field)))

    @classmethod
    async def _build_message(
        cls,
        employee: dict,
        employee_id: str,
        employee_years_anniversary: int,
        employee_manager,
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
                return await message_generator.generate_message(
                    'anniversary',
                    employee_name,
                    slack_mention,
                    anniversary_years=employee_years_anniversary,
                )
            except Exception as error:
                logger.warning('Bedrock message generation failed, using template fallback: %s', error)

        template = cls.choose_template(templates_copy)
        if len(templates_copy) > 1:
            templates_copy.remove(template)
        return cls.fill_from_template(slack_mention, str(employee_years_anniversary), template)

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
            selected_gif = await cls.get_gender_agnostic_gif(
                gif_integration,
                message_generator,
                cls.default_gif_keyword,
                gif_search_limit,
            )
            await slack_message_integration.send_message(message, selected_gif.get('url'), selected_gif.get('description'))

        anniversary_employees = list(cls.get_anniversary_employees(
            await employee_manager.get_employees_with_anniversary(),
            employee_manager.integration.employee_hire_field,
        ))
        employee_slack_ids = list(await slack_api_integration.get_members_id_by_email(
            employee_manager.integration.get_employees_email(anniversary_employees)
        ))
        templates_copy = list(templates)
        message_coros = []
        for employee, employee_id in zip(anniversary_employees, employee_slack_ids):
            employee_hire_date = employee.get(employee_manager.integration.employee_hire_field)
            employee_years_anniversary = date_utils.get_years_difference_from_current_date(
                EnvManager.UTC_HOUR_OFFSET,
                employee_hire_date,
            )
            message = await cls._build_message(
                employee,
                employee_id,
                employee_years_anniversary,
                employee_manager,
                templates_copy,
                message_generator,
            )
            message_coros.append(send_message_coro(cls.gif_search_limit, message))

        await asyncio.gather(*message_coros)
