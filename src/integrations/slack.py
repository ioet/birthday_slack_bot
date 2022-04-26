from typing import List

from src.clients import RestClient
from src.config import EnvManager


class SlackIntegration:
    api_token = EnvManager.SLACK_BOT_USER_AUTH_TOKEN
    limit = 190
    client = RestClient(
        base_url='https://slack.com/api/',
        api_token=api_token,
        is_bearer=True
    )

    @classmethod
    def get_members(cls):
        employees = []
        exists_employees = True
        query_params = {
            'limit': cls.limit
        }

        while exists_employees:
            response = cls.client.get('users.list', query_params=query_params)

            if response.status_code != 200:
                return

            response = response.json()
            employees += response.get('members', [])
            next_cursor = response.get('response_metadata', {}).get('next_cursor', '')
            exists_employees = bool(next_cursor)
            query_params['cursor'] = next_cursor

        return employees

    @classmethod
    def get_member_by_email(cls, email):
        query_params = {
            'email': email
        }

        response = cls.client.get('users.lookupByEmail', query_params=query_params)

        if response.status_code != 200:
            return

        member = response.json().get('user')
        return member

    @classmethod
    def get_members_id_by_email(cls, members_email: List[str]) -> List[str]:
        return [cls.get_member_by_email(email).get('id') for email in members_email]

