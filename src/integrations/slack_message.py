import asyncio
from functools import partial

import requests

from src.config import EnvManager


class SlackMessageIntegration:
    webhook_url: str = EnvManager.SLACK_WEBHOOK_URL_SECRET

    @classmethod
    async def _post(cls, payload: dict) -> requests.Response:
        partial_post = partial(requests.post, cls.webhook_url, json=payload)
        response = await asyncio.get_event_loop().run_in_executor(None, partial_post)
        if response.status_code != 200 or response.text != 'ok':
            raise Exception(
                f'Could not send Slack message. Status: {response.status_code}, response: {response.text}'
            )
        return response

    @classmethod
    async def send_message(cls, text_message: str, image_url: str, image_alt_text: str = ''):
        return await cls._post({
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

    @classmethod
    async def send_raw_message(cls, raw_message: dict):
        return await cls._post(raw_message)
