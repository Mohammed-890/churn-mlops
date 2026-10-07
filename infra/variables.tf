variable "region" {
  type    = string
  default = "eu-west-2"
}
variable "name" {
  type    = string
  default = "churnops"
}
variable "image_uri" {
  type        = string
  description = "Existing ECR image URI, preferably an immutable sha256 digest; required before creating the service."
}
variable "github_repository" {
  type        = string
  description = "owner/repo; GitHub production environment must exist."
}
variable "create_github_oidc" {
  type        = bool
  default     = true
  description = "Set false if an account-wide GitHub OIDC provider already exists."
}
variable "alarm_email" {
  type    = string
  default = ""
}
