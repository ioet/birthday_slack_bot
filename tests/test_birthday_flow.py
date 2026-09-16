from src.controllers.birthday_message import BirthdayMessageController
from src.controllers.employee_controller import EmployeeController
from src.data.wishes import BIRTHDAY_WISH_TEMPLATES
from tests.conftest import build_bamboo_integration


async def test_birthday_flow_uses_bedrock_and_sends_slack_message(
    birthday_employee,
    other_employee,
    slack_api_integration,
    slack_message_integration,
    gif_integration,
    bedrock_integration,
):
    employee_manager = EmployeeController(
        build_bamboo_integration([birthday_employee, other_employee])
    )

    await BirthdayMessageController.send(
        employee_manager,
        slack_api_integration,
        slack_message_integration,
        gif_integration,
        BIRTHDAY_WISH_TEMPLATES,
        bedrock_integration,
    )

    bedrock_integration.generate_birthday_message.assert_awaited_once_with(
        'Ada Lovelace',
        '<@U_ADA>',
    )
    gif_integration.get_random_gif.assert_awaited_once_with(
        BirthdayMessageController.default_gif_keyword,
        BirthdayMessageController.gif_search_limit,
    )
    slack_message_integration.send_message.assert_awaited_once_with(
        'Bedrock birthday for Ada Lovelace <@U_ADA>',
        'https://example.com/gif.gif',
        'party gif',
    )


async def test_birthday_flow_falls_back_to_template_when_bedrock_fails(
    birthday_employee,
    slack_api_integration,
    slack_message_integration,
    gif_integration,
    bedrock_integration,
):
    bedrock_integration.generate_birthday_message.side_effect = RuntimeError('bedrock down')
    employee_manager = EmployeeController(build_bamboo_integration([birthday_employee]))

    await BirthdayMessageController.send(
        employee_manager,
        slack_api_integration,
        slack_message_integration,
        gif_integration,
        ('Happy birthday {}!',),
        bedrock_integration,
    )

    slack_message_integration.send_message.assert_awaited_once()
    message = slack_message_integration.send_message.await_args.args[0]
    assert message == 'Happy birthday <@U_ADA>!'


async def test_birthday_flow_sends_nothing_when_no_birthdays_today(
    other_employee,
    slack_api_integration,
    slack_message_integration,
    gif_integration,
    bedrock_integration,
):
    employee_manager = EmployeeController(build_bamboo_integration([other_employee]))

    await BirthdayMessageController.send(
        employee_manager,
        slack_api_integration,
        slack_message_integration,
        gif_integration,
        BIRTHDAY_WISH_TEMPLATES,
        bedrock_integration,
    )

    bedrock_integration.generate_birthday_message.assert_not_awaited()
    gif_integration.get_random_gif.assert_not_awaited()
    slack_message_integration.send_message.assert_not_awaited()
