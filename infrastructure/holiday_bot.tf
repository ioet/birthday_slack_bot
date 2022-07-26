module "holiday_lambda_container_image" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "ioet-holiday-bot"
  description   = "Informs the holidays of the ioeter each friday at 10:00 AM GTM-5"
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

  timeout      = 15
  image_uri    = var.HOLIDAY_BOT_IMAGE
  package_type = "Image"
}


resource "aws_cloudwatch_event_rule" "holiday_schedule_rule" {
  name                = "every-friday-holiday-bot"
  description         = "Trigger event on friday at 10:00AM GMT-5"
  schedule_expression = "cron(0 15 ? * FRI *)"
}


resource "aws_cloudwatch_event_target" "holiday_event_target" {
  rule      = aws_cloudwatch_event_rule.holiday_schedule_rule.name
  target_id = "schedule_lambda"
  arn       = module.holiday_lambda_container_image.lambda_function_arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_holiday_lambda" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = module.holiday_lambda_container_image.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.holiday_schedule_rule.arn
}
