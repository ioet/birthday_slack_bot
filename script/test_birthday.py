#!/usr/bin/env python3
"""Dry-run the birthday bot: fetch from Bamboo and Giphy, print Slack payload."""

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def load_dotenv() -> None:
    env_file = ROOT / '.env'
    if not env_file.exists():
        return

    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip().split('#', 1)[0].strip()
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv()

from src.controllers.birthday_message import BirthdayMessageController
from src.controllers.employee_controller import EmployeeController
from src.data.wishes import BIRTHDAY_WISH_TEMPLATES
from src.integrations.bamboo import BambooIntegration
from src.integrations.giphy_gif import GiphyGifIntegration


def _gif_search_keyword(keyword) -> str:
    if isinstance(keyword, list):
        return keyword[0]
    return keyword


def _employee_label(employee: dict) -> str:
    name = employee.get('fullName1') or employee.get(BambooIntegration.employee_email_field, 'Unknown')
    email = employee.get(BambooIntegration.employee_email_field, '')
    return f'{name} ({email})' if email else name


def _slack_payload(message: str, image_url: str, image_alt_text: str) -> dict:
    return {
        'text': message,
        'blocks': [
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': message,
                },
            },
            {
                'type': 'image',
                'image_url': image_url,
                'alt_text': image_alt_text,
            },
        ],
    }


async def main() -> None:
    employee_manager = EmployeeController(BambooIntegration)

    employees_with_birthday = await employee_manager.get_employees_with_birthday()
    birthday_employees = list(
        BirthdayMessageController.get_birthday_employees(
            employees_with_birthday,
            BambooIntegration.employee_birthday_field,
        )
    )

    if not birthday_employees:
        print('No birthdays today.')
        return

    print(f'Found {len(birthday_employees)} birthday(s) today.\n')

    templates_copy = list(BIRTHDAY_WISH_TEMPLATES)

    for index, employee in enumerate(birthday_employees, start=1):
        template = BirthdayMessageController.choose_template(templates_copy)
        if len(templates_copy) > 1:
            templates_copy.remove(template)

        label = _employee_label(employee)
        message = BirthdayMessageController.fill_from_template(label, template)
        keyword = _gif_search_keyword(
            BirthdayMessageController.get_best_matching_template_keyword(message)
        )
        gif = await GiphyGifIntegration.get_random_gif(
            keyword,
            BirthdayMessageController.gif_search_limit,
        )

        payload = _slack_payload(
            message,
            gif.get('url', ''),
            gif.get('description', ''),
        )

        print(f'--- Birthday {index}: {label} ---')
        print(f'GIF keyword: {keyword}')
        print(f'Message:\n{message}\n')
        print('GIF:')
        print(json.dumps(gif, indent=2))
        print('\nSlack payload:')
        print(json.dumps(payload, indent=2))
        print()


if __name__ == '__main__':
    asyncio.run(main())
