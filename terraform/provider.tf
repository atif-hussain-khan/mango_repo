#=#=#=#=#=#=#=#=#=#=#=#=# Provider

provider "aws" {
  region = "eu-west-2"
  default_tags {
    tags = {
      Client  = "Totesys"
      Owner   = "VariousArtists"
    }
  }
}

terraform {
  backend "s3" {
    bucket = "terraform-state-va-052023"
    key    = "terraform.tfstate"
    region = "eu-west-2"
  }
}