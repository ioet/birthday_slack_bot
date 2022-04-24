from src.clients import RestClient
from src.config import EnvManager


class BambooIntegration:
    api_token: str = EnvManager.BAMBOOHR_API_TOKEN
    subdomain: str = EnvManager.BAMBOOHR_SUBDOMAIN
    client = RestClient(
        base_url=f'https://api.bamboohr.com/api/gateway.php/{subdomain}/v1',
        api_token=api_token,
        is_basic_auth=True
    )

    @classmethod
    def get_employees(cls):
        response = cls.client.post('reports/custom', payload={
                'title':  'test report',
                'fields': ['firstName', 'lastName', 'status', 'birthday']
            },
            query_params={
                'format': 'json',
                'onlyCurrent': True
            }
        )
        employees = response.json().get('employees', [])
        employees = [employee for employee in employees if employee['status'] == 'Active' and employee['birthday']]
        return employees
