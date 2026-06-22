variable "REGION" {
  description = "Aws region"
  type        = string
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

variable "AWS_BEDROCK_REGION" {
  description = "AWS region for Bedrock Runtime (fallback when not set in Secrets Manager)"
  type        = string
  default     = "us-east-1"
}

variable "AWS_BEDROCK_MODEL_ID" {
  description = "Bedrock model ID for birthday message generation (fallback when not set in Secrets Manager)"
  type        = string
  default     = "google.gemma-3-4b-it"
}
