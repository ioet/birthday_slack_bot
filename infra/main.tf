terraform{
    required_providers {
        aws = {
            source = "hashicorp/aws"
            version = "3.54.0"
        }
    }
}

provider "aws" {
  region = var.region
  profile = var.aws_profile
  shared_credentials_files = var.shared_credentials_file
  default_tags {
    tags = var.tags
  }
}