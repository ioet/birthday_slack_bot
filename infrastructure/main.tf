terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.9.0"
    }
  }
  backend "s3" {
    bucket = "tfstate-bucket-ioet-birthday-bot"
    key    = "terraform/state/birthday_lambda.tfstate"
    region = "us-east-1"
    encrypt = true
  }
}

provider "aws" {
  region     = var.REGION
  access_key = var.ACCESS_KEY
  secret_key = var.SECRET_KEY
}


data "aws_secretsmanager_secret" "secret" {
  name = var.SECRET_NAME
}

data "aws_secretsmanager_secret_version" "creds" {
  secret_id = data.aws_secretsmanager_secret.secret.id
}

locals {
  secret = jsondecode(
    data.aws_secretsmanager_secret_version.creds.secret_string
  )
}


module "lambda_function_container_image" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "ioet-birthday-bot"
  description   = "Birthday-bot sends wishes each day at 9:00 AM"
  maximum_retry_attempts = 0

  create_package = false

  environment_variables = {
    BAMBOOHR_API_TOKEN        = local.secret.BAMBOOHR_API_TOKEN
    BAMBOOHR_SUBDOMAIN        = local.secret.BAMBOOHR_SUBDOMAIN
    SLACK_WEBHOOK_URL_SECRET  = local.secret.SLACK_WEBHOOK_URL_SECRET
    SLACK_BOT_USER_AUTH_TOKEN = local.secret.SLACK_BOT_USER_AUTH_TOKEN
    TENOR_API_KEY             = local.secret.TENOR_API_KEY
    UTC_HOUR_OFFSET           = local.secret.UTC_HOUR_OFFSET
  }

  image_uri    = var.DOCKER_IMAGE
  package_type = "Image"
}


resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "every-day"
  description         = "Trigger event every day at 9:00AM GMT-5"
  schedule_expression = "cron(0 14 * * ? *)"
}


resource "aws_cloudwatch_event_target" "check_schedule" {
  rule      = aws_cloudwatch_event_rule.schedule.name
  target_id = "schedule_lambda"
  arn       = module.lambda_function_container_image.lambda_function_arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_lambda" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_function_container_image.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule.arn
}
