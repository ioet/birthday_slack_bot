from src.clients import RestClient
from src.config import EnvManager


class BambooIntegration:
    employees_status = 'Active'
    employee_identifier_field = 'bestEmail'
    employee_birthday_field = 'birthday'
    employee_status_field = 'status'
    default_employee_fields = ['fullName1', employee_identifier_field, employee_status_field, employee_birthday_field]
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
                'title':  'Report',
                'fields': cls.default_employee_fields
            },
            query_params={
                'format': 'json',
                'onlyCurrent': True
            }
        )
        employees = response.json().get('employees', [])
        employees = [employee for employee in employees if employee[cls.employee_status_field] == cls.employees_status]
        return employees

    @classmethod
    def get_employees_with_birthday(cls):
        employees = cls.get_employees()
        employees = [employee for employee in employees if employee[cls.employee_birthday_field]]
        return employees
