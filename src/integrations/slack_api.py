import asyncio
from typing import List

from src.clients import RestClient
from src.config import EnvManager


class SlackApiIntegration:
    api_token = EnvManager.SLACK_BOT_USER_AUTH_TOKEN
    limit = 190
    client = RestClient(
        base_url='https://slack.com/api/',
        api_token=api_token,
        is_bearer=True
    )

    @classmethod
    async def get_members(cls):
        members = []
        exists_members = True
        query_params = {
            'limit': cls.limit
        }

        while exists_members:
            response = await cls.client.get('users.list', query_params=query_params)
            members_list = response.json()

            cls.raise_exception_for_error(members_list, cls.get_members.__name__)

            members.extend(members_list.get('members', []))
            next_cursor = members_list.get('response_metadata', {}).get('next_cursor')
            exists_members = bool(next_cursor)
            query_params['cursor'] = next_cursor

        return members

    @classmethod
    async def get_member_by_email(cls, email):
        query_params = {
            'email': email
        }

        response = await cls.client.get('users.lookupByEmail', query_params=query_params)
        member = response.json()

        cls.raise_exception_for_error(member, cls.get_member_by_email.__name__)

        return member.get('user')

    @classmethod
    async def get_members_id_by_email(cls, members_email: List[str]) -> List[str]:
        members = await asyncio.gather(*[cls.get_member_by_email(email) for email in members_email])
        return map(lambda member: member.get('id'), members)

    @classmethod
    def get_member_id_by_email(cls, member_email: str) -> str:
        return cls.get_member_by_email(member_email).get('id')

    @staticmethod
    def raise_exception_for_error(response: dict, function_name: str):
        if not response.get('ok'):
            error = response.get('error')
            raise Exception(f'Could not retrieve information on {function_name}, due the following error: {error}')
