from unittest.mock import AsyncMock

import pytest

from src.controllers.base import BaseController
from src.integrations.bedrock import BedrockIntegration
from src.integrations.giphy_gif import GiphyGifIntegration


async def test_get_gender_agnostic_gif_retries_until_true(gif_integration, bedrock_integration):
    gif_integration.get_random_gif.side_effect = [
        {
            'url': 'https://example.com/gendered.gif',
            'preview_url': 'https://example.com/gendered-small.gif',
            'description': 'man dancing',
        },
        {
            'url': 'https://example.com/ok.gif',
            'preview_url': 'https://example.com/ok-small.gif',
            'description': 'party confetti',
        },
    ]
    bedrock_integration._ensure_gender_agnostic_gif.side_effect = [False, True]

    selected_gif = await BaseController.get_gender_agnostic_gif(
        gif_integration,
        bedrock_integration,
        'birthday',
        15,
    )

    assert selected_gif == {
        'url': 'https://example.com/ok.gif',
        'preview_url': 'https://example.com/ok-small.gif',
        'description': 'party confetti',
    }
    assert gif_integration.get_random_gif.await_count == 2
    assert bedrock_integration._ensure_gender_agnostic_gif.await_count == 2
    bedrock_integration._ensure_gender_agnostic_gif.assert_any_await(
        'man dancing',
        'https://example.com/gendered-small.gif',
    )
    bedrock_integration._ensure_gender_agnostic_gif.assert_awaited_with(
        'party confetti',
        'https://example.com/ok-small.gif',
    )


async def test_get_gender_agnostic_gif_retries_when_check_fails(gif_integration, bedrock_integration):
    gif_integration.get_random_gif.side_effect = [
        {
            'url': 'https://example.com/unchecked.gif',
            'preview_url': 'https://example.com/unchecked-small.gif',
            'description': 'mystery gif',
        },
        {
            'url': 'https://example.com/ok.gif',
            'preview_url': 'https://example.com/ok-small.gif',
            'description': 'party confetti',
        },
    ]
    bedrock_integration._ensure_gender_agnostic_gif.side_effect = [
        ValueError('Expected a boolean response from the LLM'),
        True,
    ]

    selected_gif = await BaseController.get_gender_agnostic_gif(
        gif_integration,
        bedrock_integration,
        'birthday',
        15,
    )

    assert selected_gif['url'] == 'https://example.com/ok.gif'
    assert gif_integration.get_random_gif.await_count == 2


@pytest.mark.parametrize(
    ('llm_response', 'expected'),
    [
        ('true', True),
        ('False', False),
        (' TRUE.\n', True),
        ('false!', False),
    ],
)
async def test_ensure_gender_agnostic_gif_parses_boolean_responses(monkeypatch, llm_response, expected):
    monkeypatch.setattr(BedrockIntegration, '_converse', AsyncMock(return_value=llm_response))

    assert await BedrockIntegration._ensure_gender_agnostic_gif('party confetti') is expected


@pytest.mark.parametrize('llm_response', ['yes', 'false - shows a man', ''])
async def test_ensure_gender_agnostic_gif_raises_on_unexpected_response(monkeypatch, llm_response):
    monkeypatch.setattr(BedrockIntegration, '_converse', AsyncMock(return_value=llm_response))

    with pytest.raises(ValueError):
        await BedrockIntegration._ensure_gender_agnostic_gif('party confetti')


async def test_get_gender_agnostic_gif_skips_check_without_message_generator(gif_integration):
    selected_gif = await BaseController.get_gender_agnostic_gif(
        gif_integration,
        None,
        'birthday',
        15,
    )

    assert selected_gif['url'] == 'https://example.com/gif.gif'
    gif_integration.get_random_gif.assert_awaited_once()


def test_giphy_selects_smallest_preview_and_keeps_display_size():
    images = {
        'fixed_width': {
            'url': 'https://example.com/display.gif',
            'width': '200',
            'height': '250',
            'size': '576364',
        },
        'fixed_height_small_still': {
            'url': 'https://example.com/preview-still.gif',
            'width': '80',
            'height': '100',
            'size': '8301',
        },
        'preview_webp': {
            'url': 'https://example.com/preview.webp',
            'width': '120',
            'height': '150',
            'size': '20858',
        },
    }

    display_url = GiphyGifIntegration._select_image_url(images)
    preview_url = GiphyGifIntegration._select_preview_image_url(images, fallback_url=display_url)

    assert display_url == 'https://example.com/display.gif'
    assert preview_url == 'https://example.com/preview-still.gif'
