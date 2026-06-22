import os


class EnvManager:
    BAMBOOHR_API_TOKEN: str = os.getenv('BAMBOOHR_API_TOKEN')
    BAMBOOHR_SUBDOMAIN: str = os.getenv('BAMBOOHR_SUBDOMAIN')
    SLACK_WEBHOOK_URL_SECRET: str = os.getenv('SLACK_WEBHOOK_URL_SECRET')
    SLACK_BOT_USER_AUTH_TOKEN: str = os.getenv('SLACK_BOT_USER_AUTH_TOKEN')
    GIPHY_API_KEY: str = os.getenv('GIPHY_API_KEY')
    TENOR_API_KEY: str = os.getenv('TENOR_API_KEY')
    UTC_HOUR_OFFSET: str = os.getenv('UTC_HOUR_OFFSET')
    AWS_BEDROCK_API_KEY: str = os.getenv('AWS_BEDROCK_API_KEY')
    AWS_BEDROCK_REGION: str = os.getenv('AWS_BEDROCK_REGION', 'us-east-1')
    AWS_BEDROCK_MODEL_ID: str = os.getenv('AWS_BEDROCK_MODEL_ID', 'google.gemma-3-4b-it')
