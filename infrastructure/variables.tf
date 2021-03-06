variable "REGION" {
  description = "Aws region"
  type        = string
}
variable "ACCESS_KEY" {
  description = "Aws access key"
  type        = string
  sensitive   = true
}
variable "SECRET_KEY" {
  description = "Aws secret key"
  type        = string
  sensitive   = true
}
variable "PARTY_BOT_IMAGE" {
  description = "Party bot docker image for the lambda that is stored in ECR"
  type        = string
  sensitive   = true
}
variable "HOLIDAY_BOT_IMAGE" {
  description = "Holiday bot docker image for the lambda that is stored in ECR"
  type        = string
  sensitive   = true
}
variable "SECRET_NAME" {
  description = "Name of the secret to be consulted from aws secret manager"
  type        = string
  sensitive   = true
}
