import os


class EnvManager:
    BAMBOOHR_API_TOKEN: str = os.getenv('BAMBOOHR_API_TOKEN')
    SLACK_WEBHOOK_URL_SECRET: str = os.getenv('SLACK_WEBHOOK_URL_SECRET')
    TENOR_API_KEY: str = os.getenv('TENOR_API_KEY')
