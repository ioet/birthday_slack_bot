import asyncio
import http
import logging

from src.controllers.anniversary_message import AnniversaryMessageController
from src.controllers.birthday_message import BirthdayMessageController
from src.controllers.employee_controller import EmployeeController
from src.data.wishes import ANNIVERSARY_WISH_TEMPLATES, BIRTHDAY_WISH_TEMPLATES
from src.integrations.bamboo import BambooIntegration
from src.integrations.slack_api import SlackApiIntegration
from src.integrations.slack_message import SlackMessageIntegration
from src.integrations.tenor_gif import TenorGifIntegration

logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def main(event, context):
    try:

        EmployeeManager = EmployeeController(BambooIntegration)

        await BirthdayMessageController.send(
            EmployeeManager,
            SlackApiIntegration,
            SlackMessageIntegration,
            TenorGifIntegration,
            BIRTHDAY_WISH_TEMPLATES
        )

        await AnniversaryMessageController.send(
            EmployeeManager,
            SlackApiIntegration,
            SlackMessageIntegration,
            TenorGifIntegration,
            ANNIVERSARY_WISH_TEMPLATES
        )

        return {
            'status_code': http.HTTPStatus.OK,
            'message': 'Wishes successfully sent',
        }

    except Exception as error:
        logger.error(error)
        raise error


def handler(event, context):
    asyncio.run(main(event, context))
