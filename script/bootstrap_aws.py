#!/usr/bin/env python3
"""
Bootstrap AWS resources for birthday_slack_bot OIDC deployment (Phase 1).

Requires admin credentials (env vars, AWS profile, or instance role).

Install deps:
    pip install -r script/requirements-bootstrap.txt

Examples:
    # Dry run with defaults (region us-east-1, reads app secrets from .env)
    python script/bootstrap_aws.py --dry-run --secret-file .env

    # Create everything
    python script/bootstrap_aws.py --secret-file .env

    # Custom names
    python script/bootstrap_aws.py \\
        --region us-east-1 \\
        --secret-file .env \\
        --state-bucket tfstate-birthday-bot-123456789012 \\
        --secret-name birthday-slack-bot/prod
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from botocore.exceptions import ClientError


def _load_boto3():
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        print(
            'boto3 is required. Install with: pip install -r script/requirements-bootstrap.txt',
            file=sys.stderr,
        )
        raise SystemExit(1) from None
    return boto3, ClientError

GITHUB_OIDC_URL = 'token.actions.githubusercontent.com'
GITHUB_OIDC_THUMBPRINT = '6938fd4d98bab03faadb97b34396831e3780aea1'
DEFAULT_REGION = 'us-east-1'
DEFAULT_GITHUB_REPO = 'ioet/birthday_slack_bot'
DEFAULT_GITHUB_BRANCH = 'main'
DEFAULT_ROLE_NAME = 'github-actions-birthday-bot'
DEFAULT_ECR_PARTY = 'party-bot'
DEFAULT_ECR_HOLIDAY = 'holiday-bot'
DEFAULT_SECRET_NAME = 'birthday-slack-bot/prod'
DEFAULT_LOCK_TABLE = 'terraform-state-lock'
DEFAULT_PARTY_LAMBDA = 'ioet-birthday-bot'
DEFAULT_HOLIDAY_LAMBDA = 'ioet-holiday-bot'
DEFAULT_PARTY_RULE = 'every-day-party-bot'
DEFAULT_HOLIDAY_RULE = 'every-friday-holiday-bot'

REQUIRED_SECRET_KEYS = (
    'BAMBOOHR_API_TOKEN',
    'BAMBOOHR_SUBDOMAIN',
    'SLACK_WEBHOOK_URL_SECRET',
    'SLACK_BOT_USER_AUTH_TOKEN',
    'GIPHY_API_KEY',
    'UTC_HOUR_OFFSET',
)


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, _, raw_value = line.partition('=')
        key = key.strip()
        value = raw_value.strip().split('#', 1)[0].strip()
        if key:
            values[key] = value
    return values


def load_secret_payload(secret_file: Path | None, secret_json: str | None) -> dict[str, str]:
    if secret_json:
        payload = json.loads(secret_json)
        if not isinstance(payload, dict):
            raise ValueError('--secret-json must be a JSON object')
        return {key: str(payload[key]) for key in REQUIRED_SECRET_KEYS}

    if secret_file is None:
        raise ValueError('Provide --secret-file or --secret-json for Secrets Manager')

    env_values = parse_env_file(secret_file)
    missing = [key for key in REQUIRED_SECRET_KEYS if not env_values.get(key)]
    if missing:
        raise ValueError(f'Missing required secret keys in {secret_file}: {", ".join(missing)}')

    return {key: env_values[key] for key in REQUIRED_SECRET_KEYS}


def build_trust_policy(account_id: str, github_repo: str, github_branch: str) -> dict[str, Any]:
    return {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Effect': 'Allow',
                'Principal': {
                    'Federated': (
                        f'arn:aws:iam::{account_id}:oidc-provider/{GITHUB_OIDC_URL}'
                    ),
                },
                'Action': 'sts:AssumeRoleWithWebIdentity',
                'Condition': {
                    'StringEquals': {
                        f'{GITHUB_OIDC_URL}:aud': 'sts.amazonaws.com',
                    },
                    'StringLike': {
                        f'{GITHUB_OIDC_URL}:sub': (
                            f'repo:{github_repo}:ref:refs/heads/{github_branch}'
                        ),
                    },
                },
            }
        ],
    }


def build_permissions_policy(
    account_id: str,
    region: str,
    state_bucket: str,
    lock_table: str,
    secret_name: str,
    ecr_party: str,
    ecr_holiday: str,
    party_lambda: str,
    holiday_lambda: str,
    party_rule: str,
    holiday_rule: str,
) -> dict[str, Any]:
    return {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Sid': 'ECRAuth',
                'Effect': 'Allow',
                'Action': 'ecr:GetAuthorizationToken',
                'Resource': '*',
            },
            {
                'Sid': 'ECRPushPull',
                'Effect': 'Allow',
                'Action': [
                    'ecr:BatchCheckLayerAvailability',
                    'ecr:GetDownloadUrlForLayer',
                    'ecr:BatchGetImage',
                    'ecr:PutImage',
                    'ecr:InitiateLayerUpload',
                    'ecr:UploadLayerPart',
                    'ecr:CompleteLayerUpload',
                    'ecr:DescribeRepositories',
                    'ecr:DescribeImages',
                    'ecr:ListImages',
                ],
                'Resource': [
                    f'arn:aws:ecr:{region}:{account_id}:repository/{ecr_party}',
                    f'arn:aws:ecr:{region}:{account_id}:repository/{ecr_holiday}',
                ],
            },
            {
                'Sid': 'TerraformStateS3',
                'Effect': 'Allow',
                'Action': [
                    's3:ListBucket',
                    's3:GetObject',
                    's3:PutObject',
                    's3:DeleteObject',
                ],
                'Resource': [
                    f'arn:aws:s3:::{state_bucket}',
                    f'arn:aws:s3:::{state_bucket}/*',
                ],
            },
            {
                'Sid': 'TerraformStateLock',
                'Effect': 'Allow',
                'Action': [
                    'dynamodb:GetItem',
                    'dynamodb:PutItem',
                    'dynamodb:DeleteItem',
                ],
                'Resource': f'arn:aws:dynamodb:{region}:{account_id}:table/{lock_table}',
            },
            {
                'Sid': 'ReadAppSecret',
                'Effect': 'Allow',
                'Action': [
                    'secretsmanager:GetSecretValue',
                    'secretsmanager:DescribeSecret',
                ],
                'Resource': f'arn:aws:secretsmanager:{region}:{account_id}:secret:{secret_name}*',
            },
            {
                'Sid': 'LambdaManagement',
                'Effect': 'Allow',
                'Action': [
                    'lambda:CreateFunction',
                    'lambda:UpdateFunctionCode',
                    'lambda:UpdateFunctionConfiguration',
                    'lambda:DeleteFunction',
                    'lambda:GetFunction',
                    'lambda:GetFunctionConfiguration',
                    'lambda:ListVersionsByFunction',
                    'lambda:PublishVersion',
                    'lambda:AddPermission',
                    'lambda:RemovePermission',
                    'lambda:GetPolicy',
                    'lambda:TagResource',
                    'lambda:UntagResource',
                    'lambda:ListTags',
                ],
                'Resource': [
                    f'arn:aws:lambda:{region}:{account_id}:function:{party_lambda}',
                    f'arn:aws:lambda:{region}:{account_id}:function:{holiday_lambda}',
                ],
            },
            {
                'Sid': 'EventBridgeSchedules',
                'Effect': 'Allow',
                'Action': [
                    'events:PutRule',
                    'events:DeleteRule',
                    'events:DescribeRule',
                    'events:EnableRule',
                    'events:DisableRule',
                    'events:PutTargets',
                    'events:RemoveTargets',
                    'events:ListTargetsByRule',
                    'events:TagResource',
                    'events:UntagResource',
                ],
                'Resource': [
                    f'arn:aws:events:{region}:{account_id}:rule/{party_rule}',
                    f'arn:aws:events:{region}:{account_id}:rule/{holiday_rule}',
                ],
            },
            {
                'Sid': 'CloudWatchLogsForLambda',
                'Effect': 'Allow',
                'Action': [
                    'logs:CreateLogGroup',
                    'logs:CreateLogStream',
                    'logs:PutLogEvents',
                    'logs:DescribeLogGroups',
                    'logs:DeleteLogGroup',
                    'logs:PutRetentionPolicy',
                    'logs:TagResource',
                    'logs:ListTagsForResource',
                ],
                'Resource': [
                    f'arn:aws:logs:{region}:{account_id}:log-group:/aws/lambda/{party_lambda}*',
                    f'arn:aws:logs:{region}:{account_id}:log-group:/aws/lambda/{holiday_lambda}*',
                ],
            },
            {
                'Sid': 'LambdaExecutionRoles',
                'Effect': 'Allow',
                'Action': [
                    'iam:GetRole',
                    'iam:CreateRole',
                    'iam:DeleteRole',
                    'iam:UpdateRole',
                    'iam:UpdateAssumeRolePolicy',
                    'iam:PassRole',
                    'iam:AttachRolePolicy',
                    'iam:DetachRolePolicy',
                    'iam:PutRolePolicy',
                    'iam:DeleteRolePolicy',
                    'iam:GetRolePolicy',
                    'iam:ListRolePolicies',
                    'iam:ListAttachedRolePolicies',
                    'iam:TagRole',
                    'iam:UntagRole',
                ],
                'Resource': [
                    f'arn:aws:iam::{account_id}:role/{party_lambda}*',
                    f'arn:aws:iam::{account_id}:role/{holiday_lambda}*',
                ],
            },
            {
                'Sid': 'TerraformReadOnlyDiscovery',
                'Effect': 'Allow',
                'Action': [
                    'lambda:ListFunctions',
                    'events:ListRules',
                    'iam:ListRoles',
                    'logs:DescribeLogGroups',
                ],
                'Resource': '*',
            },
        ],
    }


class AwsBootstrap:
    def __init__(
        self,
        region: str,
        profile: str | None,
        dry_run: bool,
        skip_dynamodb: bool,
        skip_secret: bool,
    ) -> None:
        self.region = region
        self.dry_run = dry_run
        self.skip_dynamodb = skip_dynamodb
        self.skip_secret = skip_secret
        boto3, self._client_error = _load_boto3()
        self.session = boto3.Session(region_name=region, profile_name=profile)
        self.account_id = self.session.client('sts').get_caller_identity()['Account']
        self.created: list[str] = []
        self.existing: list[str] = []
        self.updated: list[str] = []

    def log(self, message: str) -> None:
        prefix = '[dry-run] ' if self.dry_run else ''
        print(f'{prefix}{message}')

    def mark_created(self, message: str) -> None:
        self.created.append(message)
        self.log(f'created: {message}')

    def mark_existing(self, message: str) -> None:
        self.existing.append(message)
        self.log(f'exists: {message}')

    def mark_updated(self, message: str) -> None:
        self.updated.append(message)
        self.log(f'updated: {message}')

    def ensure_s3_bucket(self, bucket_name: str) -> None:
        s3 = self.session.client('s3')
        try:
            s3.head_bucket(Bucket=bucket_name)
            self.mark_existing(f'S3 bucket {bucket_name}')
        except self._client_error as error:
            if error.response['Error']['Code'] != '404':
                raise
            if self.dry_run:
                self.mark_created(f'S3 bucket {bucket_name}')
                return

            if self.region == 'us-east-1':
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region},
                )
            self.mark_created(f'S3 bucket {bucket_name}')

        if self.dry_run:
            return

        s3.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'},
        )
        s3.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                'Rules': [
                    {
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256',
                        }
                    }
                ]
            },
        )
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True,
            },
        )
        self.mark_updated(f'S3 bucket settings {bucket_name}')

    def ensure_dynamodb_table(self, table_name: str) -> None:
        if self.skip_dynamodb:
            self.log(f'skipped: DynamoDB table {table_name}')
            return

        dynamodb = self.session.client('dynamodb')
        try:
            dynamodb.describe_table(TableName=table_name)
            self.mark_existing(f'DynamoDB table {table_name}')
            return
        except self._client_error as error:
            if error.response['Error']['Code'] != 'ResourceNotFoundException':
                raise

        if self.dry_run:
            self.mark_created(f'DynamoDB table {table_name}')
            return

        dynamodb.create_table(
            TableName=table_name,
            AttributeDefinitions=[{'AttributeName': 'LockID', 'AttributeType': 'S'}],
            KeySchema=[{'AttributeName': 'LockID', 'KeyType': 'HASH'}],
            BillingMode='PAY_PER_REQUEST',
        )
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        self.mark_created(f'DynamoDB table {table_name}')

    def ensure_ecr_repository(self, repository_name: str) -> None:
        ecr = self.session.client('ecr')
        try:
            ecr.describe_repositories(repositoryNames=[repository_name])
            self.mark_existing(f'ECR repository {repository_name}')
            return
        except self._client_error as error:
            if error.response['Error']['Code'] != 'RepositoryNotFoundException':
                raise

        if self.dry_run:
            self.mark_created(f'ECR repository {repository_name}')
            return

        ecr.create_repository(
            repositoryName=repository_name,
            imageScanningConfiguration={'scanOnPush': True},
            encryptionConfiguration={'encryptionType': 'AES256'},
        )
        self.mark_created(f'ECR repository {repository_name}')

    def ensure_secret(self, secret_name: str, secret_payload: dict[str, str]) -> None:
        if self.skip_secret:
            self.log(f'skipped: Secrets Manager secret {secret_name}')
            return

        secrets = self.session.client('secretsmanager')
        secret_string = json.dumps(secret_payload)

        try:
            secrets.describe_secret(SecretId=secret_name)
            if self.dry_run:
                self.mark_updated(f'Secrets Manager secret {secret_name}')
                return
            secrets.put_secret_value(SecretId=secret_name, SecretString=secret_string)
            self.mark_updated(f'Secrets Manager secret {secret_name}')
            return
        except self._client_error as error:
            if error.response['Error']['Code'] != 'ResourceNotFoundException':
                raise

        if self.dry_run:
            self.mark_created(f'Secrets Manager secret {secret_name}')
            return

        secrets.create_secret(
            Name=secret_name,
            Description='Birthday/holiday Slack bot credentials',
            SecretString=secret_string,
        )
        self.mark_created(f'Secrets Manager secret {secret_name}')

    def ensure_oidc_provider(self) -> str:
        iam = self.session.client('iam')
        provider_arn = f'arn:aws:iam::{self.account_id}:oidc-provider/{GITHUB_OIDC_URL}'
        providers = iam.list_open_id_connect_providers()['OpenIDConnectProviderList']
        if any(item['Arn'] == provider_arn for item in providers):
            self.mark_existing(f'OIDC provider {GITHUB_OIDC_URL}')
            return provider_arn

        if self.dry_run:
            self.mark_created(f'OIDC provider {GITHUB_OIDC_URL}')
            return provider_arn

        iam.create_open_id_connect_provider(
            Url=f'https://{GITHUB_OIDC_URL}',
            ClientIDList=['sts.amazonaws.com'],
            ThumbprintList=[GITHUB_OIDC_THUMBPRINT],
        )
        self.mark_created(f'OIDC provider {GITHUB_OIDC_URL}')
        return provider_arn

    def ensure_deploy_role(
        self,
        role_name: str,
        trust_policy: dict[str, Any],
        permissions_policy: dict[str, Any],
    ) -> str:
        iam = self.session.client('iam')
        role_arn = f'arn:aws:iam::{self.account_id}:role/{role_name}'

        try:
            iam.get_role(RoleName=role_name)
            role_exists = True
            self.mark_existing(f'IAM role {role_name}')
        except self._client_error as error:
            if error.response['Error']['Code'] != 'NoSuchEntity':
                raise
            role_exists = False

        if not role_exists:
            if self.dry_run:
                self.mark_created(f'IAM role {role_name}')
            else:
                iam.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description='GitHub Actions deploy role for birthday_slack_bot',
                )
                self.mark_created(f'IAM role {role_name}')
        elif not self.dry_run:
            iam.update_assume_role_policy(
                RoleName=role_name,
                PolicyDocument=json.dumps(trust_policy),
            )
            self.mark_updated(f'IAM role trust policy {role_name}')

        if self.dry_run:
            self.mark_updated(f'IAM inline policy birthday-bot-deploy on {role_name}')
            return role_arn

        iam.put_role_policy(
            RoleName=role_name,
            PolicyName='birthday-bot-deploy',
            PolicyDocument=json.dumps(permissions_policy),
        )
        self.mark_updated(f'IAM inline policy birthday-bot-deploy on {role_name}')
        return role_arn


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Bootstrap AWS resources for birthday_slack_bot OIDC deployment.',
    )
    parser.add_argument('--region', default=DEFAULT_REGION)
    parser.add_argument('--profile', default=None, help='AWS CLI profile name')
    parser.add_argument('--dry-run', action='store_true', help='Print actions without creating resources')
    parser.add_argument('--skip-dynamodb', action='store_true')
    parser.add_argument('--skip-secret', action='store_true', help='Skip Secrets Manager create/update')
    parser.add_argument('--state-bucket', default=None, help='Defaults to tfstate-birthday-bot-<account-id>')
    parser.add_argument('--lock-table', default=DEFAULT_LOCK_TABLE)
    parser.add_argument('--ecr-party', default=DEFAULT_ECR_PARTY)
    parser.add_argument('--ecr-holiday', default=DEFAULT_ECR_HOLIDAY)
    parser.add_argument('--secret-name', default=DEFAULT_SECRET_NAME)
    parser.add_argument('--secret-file', type=Path, default=None, help='Env-style file with app credentials')
    parser.add_argument('--secret-json', default=None, help='Inline JSON secret payload')
    parser.add_argument('--role-name', default=DEFAULT_ROLE_NAME)
    parser.add_argument('--github-repo', default=DEFAULT_GITHUB_REPO)
    parser.add_argument('--github-branch', default=DEFAULT_GITHUB_BRANCH)
    parser.add_argument('--party-lambda', default=DEFAULT_PARTY_LAMBDA)
    parser.add_argument('--holiday-lambda', default=DEFAULT_HOLIDAY_LAMBDA)
    parser.add_argument('--party-rule', default=DEFAULT_PARTY_RULE)
    parser.add_argument('--holiday-rule', default=DEFAULT_HOLIDAY_RULE)
    return parser.parse_args()


def print_summary(
    account_id: str,
    region: str,
    state_bucket: str,
    lock_table: str,
    ecr_party: str,
    ecr_holiday: str,
    secret_name: str,
    role_arn: str,
    skip_dynamodb: bool,
) -> None:
    print('\n=== Phase 2 handoff ===')
    print('GitHub secrets to set:')
    print(f'  AWS_ROLE_ARN={role_arn}')
    print(f'  TF_VAR_REGION={region}')
    print(f'  TF_VAR_SECRET_NAME={secret_name}')
    print(f'  PARTY_BOT_IMAGE={ecr_party}')
    print(f'  HOLIDAY_BOT_IMAGE={ecr_holiday}')
    print('\nUpdate infrastructure/provider.tf backend:')
    print(f'  bucket = "{state_bucket}"')
    print(f'  region = "{region}"')
    if not skip_dynamodb:
        print(f'  dynamodb_table = "{lock_table}"')
    print('\nAWS account:')
    print(f'  {account_id}')
    print(f'  ECR registry: {account_id}.dkr.ecr.{region}.amazonaws.com')


def main() -> int:
    args = parse_args()
    secret_payload: dict[str, str] | None = None

    if not args.skip_secret:
        try:
            secret_payload = load_secret_payload(args.secret_file, args.secret_json)
        except ValueError as error:
            print(f'error: {error}', file=sys.stderr)
            return 1

    bootstrap = AwsBootstrap(
        region=args.region,
        profile=args.profile,
        dry_run=args.dry_run,
        skip_dynamodb=args.skip_dynamodb,
        skip_secret=args.skip_secret,
    )

    state_bucket = args.state_bucket or f'tfstate-birthday-bot-{bootstrap.account_id}'
    trust_policy = build_trust_policy(
        bootstrap.account_id,
        args.github_repo,
        args.github_branch,
    )
    permissions_policy = build_permissions_policy(
        account_id=bootstrap.account_id,
        region=args.region,
        state_bucket=state_bucket,
        lock_table=args.lock_table,
        secret_name=args.secret_name,
        ecr_party=args.ecr_party,
        ecr_holiday=args.ecr_holiday,
        party_lambda=args.party_lambda,
        holiday_lambda=args.holiday_lambda,
        party_rule=args.party_rule,
        holiday_rule=args.holiday_rule,
    )

    print(f'AWS account: {bootstrap.account_id}')
    print(f'Region: {args.region}')
    print(f'GitHub trust: repo:{args.github_repo}:ref:refs/heads/{args.github_branch}')
    print()

    bootstrap.ensure_s3_bucket(state_bucket)
    bootstrap.ensure_dynamodb_table(args.lock_table)
    bootstrap.ensure_ecr_repository(args.ecr_party)
    bootstrap.ensure_ecr_repository(args.ecr_holiday)
    if secret_payload is not None:
        bootstrap.ensure_secret(args.secret_name, secret_payload)
    bootstrap.ensure_oidc_provider()
    role_arn = bootstrap.ensure_deploy_role(
        args.role_name,
        trust_policy,
        permissions_policy,
    )

    print('\n=== Summary ===')
    if bootstrap.created:
        print('Created:')
        for item in bootstrap.created:
            print(f'  - {item}')
    if bootstrap.updated:
        print('Updated:')
        for item in bootstrap.updated:
            print(f'  - {item}')
    if bootstrap.existing:
        print('Already existed:')
        for item in bootstrap.existing:
            print(f'  - {item}')

    print_summary(
        account_id=bootstrap.account_id,
        region=args.region,
        state_bucket=state_bucket,
        lock_table=args.lock_table,
        ecr_party=args.ecr_party,
        ecr_holiday=args.ecr_holiday,
        secret_name=args.secret_name,
        role_arn=role_arn,
        skip_dynamodb=args.skip_dynamodb,
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
