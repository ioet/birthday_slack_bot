variable "region" {
    default = "us-east-1"
}

variable "aws_profile" {
  type = string
  default = "user-profile"
}

variable "shared_credentials_file" {
  type = string
  default = "~/.aws/credentials"
}

variable "tags" {
  type = map(string)
  default = {
    application = "Birthday bot"
    env = "Test"
  }
}