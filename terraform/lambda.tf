data "archive_file" "lambda_package" {
  type        = "zip"
  source_file = "../app/app.py"
  output_path = "${path.module}/lambda_function.zip"
}

resource "aws_lambda_function" "employee_api" {
  function_name = "${var.project_name}-${var.environment}"
  role          = aws_iam_role.lambda_role.arn

  runtime = var.lambda_runtime
  handler = "app.lambda_handler"

  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.employees.name
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy
  ]

  tags = {
    Name        = "${var.project_name}-lambda"
    Environment = var.environment
  }
}
