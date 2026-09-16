from src.controllers.anniversary_message import AnniversaryMessageController
from src.controllers.employee_controller import EmployeeController
from src.data.wishes import ANNIVERSARY_WISH_TEMPLATES
from tests.conftest import build_bamboo_integration


async def test_anniversary_flow_uses_bedrock_and_sends_slack_message(
    anniversary_employee,
    other_employee,
    slack_api_integration,
    slack_message_integration,
    gif_integration,
    bedrock_integration,
):
    employee_manager = EmployeeController(
        build_bamboo_integration([anniversary_employee, other_employee])
    )

    await AnniversaryMessageController.send(
        employee_manager,
        slack_api_integration,
        slack_message_integration,
        gif_integration,
        ANNIVERSARY_WISH_TEMPLATES,
        bedrock_integration,
    )

    bedrock_integration.generate_message.assert_awaited_once_with(
        'anniversary',
        'Grace Hopper',
        '<@U_GRACE>',
        anniversary_years=3,
    )
    gif_integration.get_random_gif.assert_awaited_once_with(
        AnniversaryMessageController.default_gif_keyword,
        AnniversaryMessageController.gif_search_limit,
    )
    slack_message_integration.send_message.assert_awaited_once_with(
        'Bedrock anniversary for Grace Hopper (3y) <@U_GRACE>',
        'https://example.com/gif.gif',
        'party gif',
    )


async def test_anniversary_flow_falls_back_to_template_when_bedrock_fails(
    anniversary_employee,
    slack_api_integration,
    slack_message_integration,
    gif_integration,
    bedrock_integration,
):
    bedrock_integration.generate_message.side_effect = RuntimeError('bedrock down')
    employee_manager = EmployeeController(build_bamboo_integration([anniversary_employee]))

    await AnniversaryMessageController.send(
        employee_manager,
        slack_api_integration,
        slack_message_integration,
        gif_integration,
        (
            'Happy work anniversary {username} for {anniversary_years} year(s)!',
        ),
        bedrock_integration,
    )

    slack_message_integration.send_message.assert_awaited_once()
    message = slack_message_integration.send_message.await_args.args[0]
    assert message == 'Happy work anniversary <@U_GRACE> for 3 year(s)!'


async def test_anniversary_flow_sends_nothing_when_no_anniversaries_today(
    other_employee,
    slack_api_integration,
    slack_message_integration,
    gif_integration,
    bedrock_integration,
):
    employee_manager = EmployeeController(build_bamboo_integration([other_employee]))

    await AnniversaryMessageController.send(
        employee_manager,
        slack_api_integration,
        slack_message_integration,
        gif_integration,
        ANNIVERSARY_WISH_TEMPLATES,
        bedrock_integration,
    )

    bedrock_integration.generate_message.assert_not_awaited()
    gif_integration.get_random_gif.assert_not_awaited()
    slack_message_integration.send_message.assert_not_awaited()
