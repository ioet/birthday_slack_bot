import asyncio
import base64
import logging
from functools import partial
from random import choice
from typing import List, Optional
from urllib.parse import urlparse

import requests

from ..clients import RestClient
from ..config import EnvManager
from ..data.bedrock_prompts import (
    ANNIVERSARY_STYLE_HINTS,
    ANNIVERSARY_SYSTEM_PROMPT,
    BIRTHDAY_STYLE_HINTS,
    BIRTHDAY_SYSTEM_PROMPT,
    GIF_GENDER_AGNOSTIC_SYSTEM_PROMPT,
    HOLIDAY_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


class BedrockIntegration:
    model_id: str = EnvManager.AWS_BEDROCK_MODEL_ID or 'google.gemma-3-4b-it'
    region: str = EnvManager.AWS_BEDROCK_REGION or 'us-east-1'
    api_key: str = EnvManager.AWS_BEDROCK_API_KEY
    supported_image_formats = frozenset(('png', 'jpeg', 'gif', 'webp'))
    content_type_to_format = {
        'image/png': 'png',
        'image/jpeg': 'jpeg',
        'image/jpg': 'jpeg',
        'image/gif': 'gif',
        'image/webp': 'webp',
    }

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
    def _detect_image_format(cls, image_url: str, content_type: str = '') -> str:
        mime_type = (content_type or '').split(';', 1)[0].strip().lower()
        if mime_type in cls.content_type_to_format:
            return cls.content_type_to_format[mime_type]

        extension = urlparse(image_url).path.rsplit('.', 1)[-1].lower()
        if extension == 'jpg':
            extension = 'jpeg'
        if extension in cls.supported_image_formats:
            return extension
        return 'gif'

    @classmethod
    async def _download_image(cls, image_url: str) -> tuple[bytes, str]:
        partial_get = partial(requests.get, image_url, timeout=30)
        response = await asyncio.get_event_loop().run_in_executor(None, partial_get)
        if response.status_code != 200:
            raise Exception(
                f'Could not download image. Status: {response.status_code}, url: {image_url}'
            )
        image_format = cls._detect_image_format(image_url, response.headers.get('Content-Type', ''))
        return response.content, image_format

    @classmethod
    async def _converse(
        cls,
        user_prompt: str,
        system_prompt: str,
        *,
        image_bytes: Optional[bytes] = None,
        image_format: Optional[str] = None,
    ) -> str:
        if not cls.api_key:
            raise ValueError('AWS_BEDROCK_API_KEY is not configured')

        content = [{'text': user_prompt}]
        if image_bytes and image_format:
            content.insert(0, {
                'image': {
                    'format': image_format,
                    'source': {
                        'bytes': base64.b64encode(image_bytes).decode('ascii'),
                    },
                },
            })

        response = await cls._client().post(
            payload={
                'messages': [
                    {
                        'role': 'user',
                        'content': content,
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
    async def _ensure_gender_agnostic_gif(
        cls,
        gif_description: str,
        gif_url: str = '',
    ) -> bool:
        description = (gif_description or '').strip()
        image_url = (gif_url or '').strip()
        if not description and not image_url:
            return True

        image_bytes = None
        image_format = None
        if image_url:
            try:
                image_bytes, image_format = await cls._download_image(image_url)
            except Exception as error:
                logger.warning('Could not download GIF for gender check, using description only: %s', error)

        description_section = description or '(none provided)'
        user_prompt = (
            'Review this GIF/image and its description for gender-specific visuals or language '
            '(man, woman, boy, girl, guy, lady, he, she, him, her, male, female, etc.).\n\n'
            f'Description:\n{description_section}\n\n'
            'If both the image and description are gender-agnostic, return true. '
            'If either the image or description is not gender-agnostic, return false. '
            'Return only true or false.'
        )
        result = await cls._converse(
            user_prompt,
            GIF_GENDER_AGNOSTIC_SYSTEM_PROMPT,
            image_bytes=image_bytes,
            image_format=image_format,
        )
        normalized = result.strip().lower().rstrip('.!')

        if normalized not in ('true', 'false'):
            logger.warning(
                'Unexpected gender-agnostic check response: %r',
                result,
            )
            raise ValueError('Expected a boolean response from the LLM')

        return normalized == 'true'

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
