import os


class EnvManager:
    BAMBOOHR_API_TOKEN: str = os.getenv('BAMBOOHR_API_TOKEN')
    BAMBOOHR_SUBDOMAIN: str = os.getenv('BAMBOOHR_SUBDOMAIN')
    SLACK_WEBHOOK_URL_SECRET: str = os.getenv('SLACK_WEBHOOK_URL_SECRET')
    TENOR_API_KEY: str = os.getenv('TENOR_API_KEY')
    UTC_HOUR_OFFSET: str = os.getenv('UTC_HOUR_OFFSET')
