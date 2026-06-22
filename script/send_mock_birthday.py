#!/usr/bin/env python3
"""Send a birthday Slack message using a mocked Bamboo employee with today's date."""

import argparse
import asyncio
import logging
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

from src.config import EnvManager
from src.controllers.birthday_message import BirthdayMessageController
from src.controllers.employee_controller import EmployeeController
from src.data.wishes import BIRTHDAY_WISH_TEMPLATES
from src.integrations.bamboo import BambooIntegration
from src.integrations.bedrock import BedrockIntegration
from src.integrations.giphy_gif import GiphyGifIntegration
from src.integrations.slack_api import SlackApiIntegration
from src.integrations.slack_message import SlackMessageIntegration
from src.utils import date_utils

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class MockBambooIntegration(BambooIntegration):
    employee_email: str = ''
    employee_name: str = 'Birthday Test User'

    @classmethod
    async def get_employees(cls):
        day, month = date_utils.get_current_day_month(EnvManager.UTC_HOUR_OFFSET)
        birthday = f'{month:02d}-{day:02d}'
        return [{
            'fullName1': cls.employee_name,
            cls.employee_email_field: cls.employee_email,
            cls.employee_status_field: cls.employees_status,
            cls.employee_birthday_field: birthday,
            cls.employee_hire_field: '2019-01-01',
        }]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Send a birthday Slack message with a mocked Bamboo employee.'
    )
    parser.add_argument(
        '--email',
        default=os.environ.get('TEST_BIRTHDAY_EMAIL'),
        help='Slack user email to mention (defaults to TEST_BIRTHDAY_EMAIL env var)',
    )
    parser.add_argument(
        '--name',
        default='Birthday Test User',
        help='Display name for the mocked Bamboo employee',
    )
    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    if not args.email:
        logger.error('Set TEST_BIRTHDAY_EMAIL in .env or pass --email with a Slack workspace email.')
        sys.exit(1)

    day, month = date_utils.get_current_day_month(EnvManager.UTC_HOUR_OFFSET)
    birthday = f'{month:02d}-{day:02d}'

    MockBambooIntegration.employee_email = args.email
    MockBambooIntegration.employee_name = args.name

    logger.info(
        'Sending mocked birthday message for %s (%s) with birthday %s...',
        args.name,
        args.email,
        birthday,
    )

    employee_manager = EmployeeController(MockBambooIntegration)
    await BirthdayMessageController.send(
        employee_manager,
        SlackApiIntegration,
        SlackMessageIntegration,
        GiphyGifIntegration,
        BIRTHDAY_WISH_TEMPLATES,
        BedrockIntegration,
    )

    logger.info('Done: birthday message sent to Slack.')


if __name__ == '__main__':
    asyncio.run(run())
