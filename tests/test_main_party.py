import http

import main_party
from src.controllers.employee_controller import EmployeeController
from tests.conftest import build_bamboo_integration


async def test_main_party_sends_birthday_and_anniversary_with_mocked_integrations(
    birthday_employee,
    anniversary_employee,
    other_employee,
    slack_api_integration,
    slack_message_integration,
    gif_integration,
    bedrock_integration,
    monkeypatch,
):
    bamboo = build_bamboo_integration(
        [birthday_employee, anniversary_employee, other_employee]
    )

    monkeypatch.setattr(main_party, 'BambooIntegration', bamboo)
    monkeypatch.setattr(main_party, 'SlackApiIntegration', slack_api_integration)
    monkeypatch.setattr(main_party, 'SlackMessageIntegration', slack_message_integration)
    monkeypatch.setattr(main_party, 'GiphyGifIntegration', gif_integration)
    monkeypatch.setattr(main_party, 'BedrockIntegration', bedrock_integration)
    monkeypatch.setattr(main_party, 'EmployeeController', EmployeeController)

    result = await main_party.main(None, None)

    assert result == {
        'status_code': http.HTTPStatus.OK,
        'message': 'Wishes successfully sent',
    }
    bedrock_integration.generate_birthday_message.assert_awaited_once()
    bedrock_integration.generate_message.assert_awaited_once()
    assert slack_message_integration.send_message.await_count == 2
    assert gif_integration.get_random_gif.await_count == 2
