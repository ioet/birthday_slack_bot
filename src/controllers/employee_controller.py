from typing import List


class EmployeeController:

    def __init__(self, hr_integration) -> None:
        self.integration = hr_integration
        self.employees = None

    async def fetch_employees(self):
        if not self.employees:
            self.employees = await self.integration.get_employees()
        return self.employees

    async def get_employees_with_anniversary(self) -> List[dict]:
        employees = await self.fetch_employees()
        return self.integration.get_employees_with_anniversary(employees)

    async def get_employees_with_birthday(self) -> List[dict]:
        employees = await self.fetch_employees()
        return self.integration.get_employees_with_birthday(employees)
