from src.integrations.slack import SlackIntegration
from src.integrations.tenor_gif import TenorGifIntegration
from src.controllers.birthday_message import BirthdayMessageController
from src.data.wishes import BIRTHDAY_WISH_TEMPLATES


class MockIntegration:

    @staticmethod
    def get_employees():
        return [{
            'slackUsername': '',
            'birthday': ''
        }]


BirthdayMessageController.send(MockIntegration, SlackIntegration, TenorGifIntegration, BIRTHDAY_WISH_TEMPLATES)
