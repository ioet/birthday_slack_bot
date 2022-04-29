import http
from src.integrations.bamboo import BambooIntegration
from src.integrations.slack_api import SlackApiIntegration
from src.integrations.slack_message import SlackMessageIntegration
from src.integrations.tenor_gif import TenorGifIntegration
from src.controllers.birthday_message import BirthdayMessageController
from src.data.wishes import BIRTHDAY_WISH_TEMPLATES


def handler(event, context):
    BirthdayMessageController.send(
        BambooIntegration,
        SlackApiIntegration,
        SlackMessageIntegration,
        TenorGifIntegration,
        BIRTHDAY_WISH_TEMPLATES
    )

    return {
        'status_code': http.HTTPStatus.OK,
        'message': 'Wishes successfully sent',
    }
