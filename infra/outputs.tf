output "url" {
  value = "http://${aws_lb.api.dns_name}"
}
output "repository_url" {
  value = aws_ecr_repository.api.repository_url
}
output "github_role_arn" {
  value = aws_iam_role.deploy.arn
}
output "cluster" {
  value = aws_ecs_cluster.main.name
}
output "service" {
  value = aws_ecs_service.api.name
}
