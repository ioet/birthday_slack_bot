from src.controllers.base import BaseController


async def test_get_gender_agnostic_gif_retries_until_true(gif_integration, bedrock_integration):
    gif_integration.get_random_gif.side_effect = [
        {'url': 'https://example.com/gendered.gif', 'description': 'man dancing'},
        {'url': 'https://example.com/ok.gif', 'description': 'party confetti'},
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
        'description': 'party confetti',
    }
    assert gif_integration.get_random_gif.await_count == 2
    assert bedrock_integration._ensure_gender_agnostic_gif.await_count == 2


async def test_get_gender_agnostic_gif_skips_check_without_message_generator(gif_integration):
    selected_gif = await BaseController.get_gender_agnostic_gif(
        gif_integration,
        None,
        'birthday',
        15,
    )

    assert selected_gif['url'] == 'https://example.com/gif.gif'
    gif_integration.get_random_gif.assert_awaited_once()
