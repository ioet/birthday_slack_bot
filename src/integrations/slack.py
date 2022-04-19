from ..clients.rest import RestClient
from ..config import EnvManager


class SlackIntegration:
    client = RestClient('https://hooks.slack.com/services/')
    webhook_url: str = EnvManager.SLACK_WEBHOOK_URL_SECRET

    @classmethod
    def send_message(cls, text_message: str, image_url: str, image_alt_text: str = ''):
        response = cls.client.post(cls.webhook_url, payload={
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
