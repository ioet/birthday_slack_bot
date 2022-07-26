import asyncio
import http
import logging

from src.controllers.holiday_message import HolidayMessageController
from src.integrations.bamboo import BambooIntegration
from src.integrations.slack_message import SlackMessageIntegration
from src.integrations.tenor_gif import TenorGifIntegration

logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def main(event, context):
    try:

        await HolidayMessageController.send(
            BambooIntegration,
            SlackMessageIntegration,
            TenorGifIntegration
        )

        return {
            'status_code': http.HTTPStatus.OK,
            'message': 'Holidays successfully sent',
        }

    except Exception as error:
        logger.error(error)


def handler(event, context):
    asyncio.run(main(event, context))

