import logging
from random import choice
from typing import List, Optional

from ..clients import RestClient
from ..config import EnvManager
from ..data.bedrock_prompts import (
    ANNIVERSARY_STYLE_HINTS,
    ANNIVERSARY_SYSTEM_PROMPT,
    BIRTHDAY_STYLE_HINTS,
    BIRTHDAY_SYSTEM_PROMPT,
    HOLIDAY_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


class BedrockIntegration:
    model_id: str = EnvManager.AWS_BEDROCK_MODEL_ID or 'google.gemma-3-4b-it'
    region: str = EnvManager.AWS_BEDROCK_REGION or 'us-east-1'
    api_key: str = EnvManager.AWS_BEDROCK_API_KEY

    @classmethod
    def _client(cls) -> RestClient:
        base_url = f'https://bedrock-runtime.{cls.region}.amazonaws.com/model/{cls.model_id}/converse'
        return RestClient(base_url)

    @classmethod
    def _extract_text(cls, response_body: dict) -> str:
        content = response_body.get('output', {}).get('message', {}).get('content', [])
        text_parts = [block.get('text', '') for block in content if block.get('text')]
        message = '\n'.join(part.strip() for part in text_parts if part.strip())
        if not message:
            raise ValueError('Bedrock returned an empty message')
        return message

    @classmethod
    async def _converse(cls, user_prompt: str, system_prompt: str) -> str:
        if not cls.api_key:
            raise ValueError('AWS_BEDROCK_API_KEY is not configured')

        response = await cls._client().post(
            payload={
                'messages': [
                    {
                        'role': 'user',
                        'content': [{'text': user_prompt}],
                    }
                ],
                'system': [{'text': system_prompt}],
                'inferenceConfig': {
                    'maxTokens': 256,
                    'temperature': 0.8,
                },
            },
            custom_headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {cls.api_key}',
            },
        )

        if response.status_code != 200:
            raise Exception(
                f'Bedrock request failed. Status: {response.status_code}, response: {response.text}'
            )

        return cls._extract_text(response.json())

    @classmethod
    def _ensure_slack_mention(cls, message: str, slack_mention: str) -> str:
        if slack_mention in message:
            return message.strip()
        return f'{slack_mention}\n{message.strip()}'

    @classmethod
    def _ensure_here_mention(cls, message: str) -> str:
        if '<!here>' in message:
            return message.strip()
        return f'<!here>\n{message.strip()}'

    @classmethod
    async def generate_birthday_message(cls, employee_name: str, slack_mention: str) -> str:
        style_hint = choice(BIRTHDAY_STYLE_HINTS)
        user_prompt = (
            f'Write a unique birthday message for {employee_name}.\n'
            f'Style: {style_hint}\n'
            f'Include this exact Slack mention once: {slack_mention}\n'
            'Make it feel different from a standard greeting card.'
        )
        message = await cls._converse(user_prompt, BIRTHDAY_SYSTEM_PROMPT)
        return cls._ensure_slack_mention(message, slack_mention)

    @classmethod
    async def generate_message(
        cls,
        occasion: str,
        employee_name: str,
        slack_mention: str,
        anniversary_years: Optional[int] = None,
    ) -> str:
        if occasion == 'birthday':
            return await cls.generate_birthday_message(employee_name, slack_mention)

        years_text = f'{anniversary_years} year(s)' if anniversary_years is not None else 'their time'
        style_hint = choice(ANNIVERSARY_STYLE_HINTS)
        user_prompt = (
            f'Write a unique work anniversary message for {employee_name}, '
            f'celebrating {years_text} at ioet.\n'
            f'Style: {style_hint}\n'
            f'Include this exact Slack mention once: {slack_mention}'
        )
        message = await cls._converse(user_prompt, ANNIVERSARY_SYSTEM_PROMPT)
        return cls._ensure_slack_mention(message, slack_mention)

    @classmethod
    async def generate_holiday_message(cls, holidays: List[dict]) -> str:
        holidays_text = '\n'.join(
            f'- {holiday.get("name", "Holiday")} on {holiday.get("start", "TBD")}'
            for holiday in holidays
        )
        user_prompt = (
            'Write a Slack message announcing these upcoming company holidays '
            'for the next two weeks:\n'
            f'{holidays_text}\n'
            'Start with <!here>.'
        )
        message = await cls._converse(user_prompt, HOLIDAY_SYSTEM_PROMPT)
        return cls._ensure_here_mention(message)
