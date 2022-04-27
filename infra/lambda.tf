resource "null_resource" "birthday_bot_lambda_buildstep" {
  triggers {
    handler      = "${base64sha256(file("birthday_bot_lambda/handler.py"))}"
    requirements = "${base64sha256(file("birthday_bot_lambda/requirements.txt"))}"
    build        = "${base64sha256(file("birthday_bot_lambda/build.sh"))}"
  }

  provisioner "local-exec" {
    command = "${path.module}/birthday_bot_lambda/build.sh"
  }
}

data "archive_file" "birthday_bot_lambda" {
  source_dir  = "${path.module}/birthday_bot_lambda/"
  output_path = "${path.module}/birthday_bot_lambda.zip"
  type        = "zip"

  depends_on = ["null_resource.birthday_bot_lambda_buildstep"]
}

resource "aws_lambda_function" "birthday_bot_lambda" {
  function_name    = "birthday_bot_lambda"
  handler          = "handler.lambda_handler"
  role             = "${aws_iam_role.my_lambda_function_role.arn}"
  runtime          = "python3.8"
  timeout          = 60
  filename         = "${data.archive_file.birthday_bot_lambda.output_path}"
  source_code_hash = "${data.archive_file.birthday_bot_lambda.output_base64sha256}"
}