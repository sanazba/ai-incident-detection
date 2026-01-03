terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "AI-Incident-Detection"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}

# Kubernetes provider
provider "kubernetes" {
  config_path = "~/.kube/config"
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}