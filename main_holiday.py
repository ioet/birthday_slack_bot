import asyncio
import http
import logging

from src.controllers.holiday_message import HolidayMessageController
from src.integrations.bamboo import BambooIntegration
from src.integrations.bedrock import BedrockIntegration
from src.integrations.giphy_gif import GiphyGifIntegration
from src.integrations.slack_message import SlackMessageIntegration

logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def main(event, context):
    try:

        await HolidayMessageController.send(
            BambooIntegration,
            SlackMessageIntegration,
            GiphyGifIntegration,
            BedrockIntegration,
        )

        return {
            'status_code': http.HTTPStatus.OK,
            'message': 'Holidays successfully sent',
        }

    except Exception as error:
        logger.error(error)


def handler(event, context):
    asyncio.run(main(event, context))

