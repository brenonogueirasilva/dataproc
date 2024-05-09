variable "project_id" {
  type = string
  default = "enduring-branch-413218"
}

variable "region" {
  type = string
  default = "us-central1"
}

variable "service_account_email" {
  type = string
  default = "conta-geral@enduring-branch-413218.iam.gserviceaccount.com"
}

variable "user" {
  type    = string
  default = "conta-geral"
}

variable "email" {
  type    = string
  default = "conta-geral@enduring-branch-413218.iam.gserviceaccount.com"
}

variable "privatekeypath" {
  type    = string
  default = "./gcp-key"
}

variable "publickeypath" {
  type    = string
  default = "./gcp-key.pub"
}