from src.integrations.bamboo import BambooIntegration
from src.integrations.slack import SlackIntegration
from src.integrations.tenor_gif import TenorGifIntegration
from src.controllers.birthday_message import BirthdayMessageController
from src.data.wishes import BIRTHDAY_WISH_TEMPLATES
import sys

#BirthdayMessageController.send(BambooIntegration, SlackIntegration, TenorGifIntegration, BIRTHDAY_WISH_TEMPLATES)

sys.path.insert(0, 'package/')

def lambda_handler(event, context):
    BirthdayMessageController.send(BambooIntegration, SlackIntegration, TenorGifIntegration, BIRTHDAY_WISH_TEMPLATES)
    return {"Message": "ok"}

