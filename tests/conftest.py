from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import List
from unittest.mock import AsyncMock

import pytest

from src.config import EnvManager


UTC_HOUR_OFFSET = '-5'


@pytest.fixture(autouse=True)
def configure_env_manager():
    original_offset = EnvManager.UTC_HOUR_OFFSET
    EnvManager.UTC_HOUR_OFFSET = UTC_HOUR_OFFSET
    yield
    EnvManager.UTC_HOUR_OFFSET = original_offset


@pytest.fixture
def today():
    return datetime.now(UTC) + timedelta(hours=int(UTC_HOUR_OFFSET))


@pytest.fixture
def birthday_mm_dd(today):
    return f'{today.month:02d}-{today.day:02d}'


@pytest.fixture
def anniversary_hire_date(today):
    # is_current_date rejects hire dates in the current UTC year
    return f'{today.year - 3}-{today.month:02d}-{today.day:02d}'


@pytest.fixture
def birthday_employee(birthday_mm_dd):
    return {
        'fullName1': 'Ada Lovelace',
        'bestEmail': 'ada@ioet.com',
        'status': 'Active',
        'birthday': birthday_mm_dd,
        'hireDate': '2019-01-01',
    }


@pytest.fixture
def anniversary_employee(anniversary_hire_date):
    return {
        'fullName1': 'Grace Hopper',
        'bestEmail': 'grace@ioet.com',
        'status': 'Active',
        'birthday': '12-09',
        'hireDate': anniversary_hire_date,
    }


@pytest.fixture
def other_employee():
    return {
        'fullName1': 'Alan Turing',
        'bestEmail': 'alan@ioet.com',
        'status': 'Active',
        'birthday': '06-23',
        'hireDate': '2018-11-01',
    }


def build_bamboo_integration(employees: List[dict]):
    class FakeBambooIntegration:
        employees_status = 'Active'
        employee_email_field = 'bestEmail'
        employee_birthday_field = 'birthday'
        employee_hire_field = 'hireDate'
        employee_status_field = 'status'

        @classmethod
        async def get_employees(cls):
            return employees

        @classmethod
        def get_employees_with_birthday(cls, employees_list: List[dict]):
            return (
                employee
                for employee in employees_list
                if employee.get(cls.employee_birthday_field)
            )

        @classmethod
        def get_employees_with_anniversary(cls, employees_list: List[dict]):
            return (
                employee
                for employee in employees_list
                if employee.get(cls.employee_hire_field)
            )

        @classmethod
        def get_employees_email(cls, employees_list):
            return (employee.get(cls.employee_email_field) for employee in employees_list)

        get_holidays = AsyncMock(return_value=[])

    return FakeBambooIntegration


@pytest.fixture
def slack_api_integration():
    class FakeSlackApiIntegration:
        email_to_id = {
            'ada@ioet.com': 'U_ADA',
            'grace@ioet.com': 'U_GRACE',
            'alan@ioet.com': 'U_ALAN',
        }

        @classmethod
        async def get_members_id_by_email(cls, members_email):
            return [cls.email_to_id[email] for email in members_email]

    return FakeSlackApiIntegration


@pytest.fixture
def slack_message_integration():
    class FakeSlackMessageIntegration:
        send_message = AsyncMock()
        send_raw_message = AsyncMock()

    FakeSlackMessageIntegration.send_message.reset_mock()
    FakeSlackMessageIntegration.send_raw_message.reset_mock()
    return FakeSlackMessageIntegration


@pytest.fixture
def gif_integration():
    class FakeGifIntegration:
        get_random_gif = AsyncMock(
            return_value={
                'url': 'https://example.com/gif.gif',
                'description': 'party gif',
            }
        )

    FakeGifIntegration.get_random_gif.reset_mock()
    return FakeGifIntegration


@pytest.fixture
def bedrock_integration():
    class FakeBedrockIntegration:
        generate_birthday_message = AsyncMock(
            side_effect=lambda name, mention: f'Bedrock birthday for {name} {mention}'
        )
        generate_message = AsyncMock(
            side_effect=lambda occasion, name, mention, anniversary_years=None: (
                f'Bedrock {occasion} for {name} ({anniversary_years}y) {mention}'
            )
        )
        generate_holiday_message = AsyncMock(
            side_effect=lambda holidays: (
                '<!here>\n' + '\n'.join(
                    f'- {holiday["name"]} on {holiday["start"]}' for holiday in holidays
                )
            )
        )
        _ensure_gender_agnostic_gif = AsyncMock(return_value=True)

    FakeBedrockIntegration.generate_birthday_message.reset_mock()
    FakeBedrockIntegration.generate_message.reset_mock()
    FakeBedrockIntegration.generate_holiday_message.reset_mock()
    FakeBedrockIntegration._ensure_gender_agnostic_gif.reset_mock()
    return FakeBedrockIntegration
