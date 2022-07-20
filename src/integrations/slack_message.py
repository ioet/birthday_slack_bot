from src.clients import RestClient
from src.config import EnvManager


class SlackMessageIntegration:
    webhook_url: str = EnvManager.SLACK_WEBHOOK_URL_SECRET
    client = RestClient('https://hooks.slack.com/services/')

    @classmethod
    async def send_message(cls, text_message: str, image_url: str, image_alt_text: str = ''):
        response = await cls.client.post(cls.webhook_url, payload={
            'text': text_message,
            'blocks': [
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': text_message
                    }
                },
                {
                    'type': 'image',
                    'image_url': image_url,
                    'alt_text': image_alt_text
                }
            ]
        })
        return response

    @classmethod
    async def send_raw_message(cls, raw_message: dict):
        return await cls.client.post(cls.webhook_url, payload=raw_message)
