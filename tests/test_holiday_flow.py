from src.controllers.holiday_message import HolidayMessageController
from tests.conftest import build_bamboo_integration


async def test_holiday_flow_uses_bedrock_and_sends_raw_slack_message(
    slack_message_integration,
    gif_integration,
    bedrock_integration,
):
    holidays = [
        {'name': 'Company Day', 'start': '2026-09-20'},
        {'name': 'Founders Day', 'start': '2026-09-25'},
    ]
    bamboo = build_bamboo_integration([])
    bamboo.get_holidays.return_value = holidays

    await HolidayMessageController.send(
        bamboo,
        slack_message_integration,
        gif_integration,
        bedrock_integration,
    )

    bamboo.get_holidays.assert_awaited_once()
    bedrock_integration.generate_holiday_message.assert_awaited_once_with(holidays)
    gif_integration.get_random_gif.assert_awaited_once_with(
        HolidayMessageController.default_gif_keyword,
        HolidayMessageController.gif_search_limit,
    )
    slack_message_integration.send_raw_message.assert_awaited_once()
    payload = slack_message_integration.send_raw_message.await_args.args[0]
    assert payload['text'] == 'Upcoming holidays:'
    assert '<!here>' in payload['blocks'][0]['text']['text']
    assert payload['blocks'][1]['image_url'] == 'https://example.com/gif.gif'


async def test_holiday_flow_falls_back_to_static_message_when_bedrock_fails(
    slack_message_integration,
    gif_integration,
    bedrock_integration,
):
    holidays = [{'name': 'Company Day', 'start': '2026-09-20'}]
    bamboo = build_bamboo_integration([])
    bamboo.get_holidays.return_value = holidays
    bedrock_integration.generate_holiday_message.side_effect = RuntimeError('bedrock down')

    await HolidayMessageController.send(
        bamboo,
        slack_message_integration,
        gif_integration,
        bedrock_integration,
    )

    payload = slack_message_integration.send_raw_message.await_args.args[0]
    assert payload['blocks'][0]['text']['text'] == (
        '<!here> Holidays for the next 2 weeks:\n• 2026-09-20 : Company Day'
    )


async def test_holiday_flow_sends_nothing_when_no_holidays(
    slack_message_integration,
    gif_integration,
    bedrock_integration,
):
    bamboo = build_bamboo_integration([])
    bamboo.get_holidays.return_value = []

    await HolidayMessageController.send(
        bamboo,
        slack_message_integration,
        gif_integration,
        bedrock_integration,
    )

    bedrock_integration.generate_holiday_message.assert_not_awaited()
    gif_integration.get_random_gif.assert_not_awaited()
    slack_message_integration.send_raw_message.assert_not_awaited()
