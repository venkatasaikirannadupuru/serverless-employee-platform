output "api_endpoint" {
  description = "API Gateway endpoint"
  value       = aws_apigatewayv2_api.employee_api.api_endpoint
}

output "dynamodb_table_name" {
  description = "DynamoDB employee table"
  value       = aws_dynamodb_table.employees.name
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.employee_api.function_name
}

output "sns_topic_arn" {
  description = "SNS notification topic ARN"
  value       = aws_sns_topic.employee_notifications.arn
}

output "cloudwatch_log_group" {
  description = "Lambda CloudWatch log group"
  value       = aws_cloudwatch_log_group.lambda.name
}
