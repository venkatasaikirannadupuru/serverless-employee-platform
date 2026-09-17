resource "aws_apigatewayv2_api" "employee_api" {
  name          = "${var.project_name}-${var.environment}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["content-type"]
  }

  tags = {
    Name        = "${var.project_name}-api"
    Environment = var.environment
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id = aws_apigatewayv2_api.employee_api.id

  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.employee_api.invoke_arn
  payload_format_version = "2.0"
}

# GET /health
resource "aws_apigatewayv2_route" "health" {
  api_id    = aws_apigatewayv2_api.employee_api.id
  route_key = "GET /health"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# GET /employees
resource "aws_apigatewayv2_route" "employees_get" {
  api_id    = aws_apigatewayv2_api.employee_api.id
  route_key = "GET /employees"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# POST /employees
resource "aws_apigatewayv2_route" "employees_post" {
  api_id    = aws_apigatewayv2_api.employee_api.id
  route_key = "POST /employees"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# PUT /employees/{employee_id}
resource "aws_apigatewayv2_route" "employees_put" {
  api_id    = aws_apigatewayv2_api.employee_api.id
  route_key = "PUT /employees/{employee_id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# DELETE /employees/{employee_id}
resource "aws_apigatewayv2_route" "employees_delete" {
  api_id    = aws_apigatewayv2_api.employee_api.id
  route_key = "DELETE /employees/{employee_id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# Default stage
resource "aws_apigatewayv2_stage" "default" {
  api_id = aws_apigatewayv2_api.employee_api.id
  name   = "$default"

  auto_deploy = true
}

# Allow API Gateway to invoke Lambda
resource "aws_lambda_permission" "api_gateway" {
  statement_id = "AllowAPIGatewayInvoke"
  action       = "lambda:InvokeFunction"

  function_name = aws_lambda_function.employee_api.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.employee_api.execution_arn}/*/*"
}