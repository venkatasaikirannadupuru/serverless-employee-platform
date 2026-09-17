resource "aws_sns_topic" "employee_notifications" {
  name = "${var.project_name}-${var.environment}-notifications"

  tags = {
    Name        = "${var.project_name}-notifications"
    Environment = var.environment
  }
}
