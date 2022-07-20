from typing import List, Optional

from src.clients import RestClient
from src.config import EnvManager


class BambooIntegration:
    employees_status: str = 'Active'
    employee_email_field: str = 'bestEmail'
    employee_birthday_field: str = 'birthday'
    employee_hire_field: str = 'hireDate'
    employee_status_field: str = 'status'
    default_employee_fields: str = ('fullName1', employee_email_field, employee_status_field, employee_birthday_field, employee_hire_field)
    api_token: str = EnvManager.BAMBOOHR_API_TOKEN
    subdomain: str = EnvManager.BAMBOOHR_SUBDOMAIN
    client = RestClient(
        base_url=f'https://api.bamboohr.com/api/gateway.php/{subdomain}/v1',
        api_token=api_token,
        is_basic_auth=True
    )

    @classmethod
    async def get_employees(cls):
        response = await cls.client.post('reports/custom', payload={
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
    def get_employees_with_birthday(cls, employees: List[dict]):
        return (employee for employee in employees if employee[cls.employee_birthday_field])

    @classmethod
    def get_employees_with_anniversary(cls, employees: List[dict]):
        return (employee for employee in employees if employee[cls.employee_hire_field])

    @classmethod
    def get_employees_email(cls, employees: List[dict]):
        return (employee.get(cls.employee_email_field) for employee in employees)

    @classmethod
    async def get_holidays(cls, start: Optional[str] = None, end: Optional[str] = None) -> List[dict]:
        params = {}
        if start:
            params.update({'start': start})
        if end:
            params.update({'end': end})

        response = await cls.client.get('time_off/whos_out/', query_params=params, custom_headers={'Accept': 'application/json'})

        return [time_off for time_off in response.json() if time_off.get('type', '').lower() == 'holiday']
