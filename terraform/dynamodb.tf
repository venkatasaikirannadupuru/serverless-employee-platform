resource "aws_dynamodb_table" "employees" {
  name         = "${var.project_name}-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "employee_id"

  attribute {
    name = "employee_id"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-table"
    Environment = var.environment
  }
}
