terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.9.0"
    }
  }
  backend "s3" {
    bucket = "tfstate-birthday-bot-057547600142"
    key    = "terraform/state/birthday_lambda.tfstate"
    region = "us-east-1"
    encrypt = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.REGION
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
