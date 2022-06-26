import http
import logging

from src.controllers.anniversary_message import AnniversaryMessageController
from src.controllers.birthday_message import BirthdayMessageController
from src.data.wishes import ANNIVERSARY_WISH_TEMPLATES, BIRTHDAY_WISH_TEMPLATES
from src.integrations.bamboo import BambooIntegration
from src.integrations.slack_api import SlackApiIntegration
from src.integrations.slack_message import SlackMessageIntegration
from src.integrations.tenor_gif import TenorGifIntegration

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    try:

        BirthdayMessageController.send(
            BambooIntegration,
            SlackApiIntegration,
            SlackMessageIntegration,
            TenorGifIntegration,
            BIRTHDAY_WISH_TEMPLATES
        )

        AnniversaryMessageController.send(
            BambooIntegration,
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
