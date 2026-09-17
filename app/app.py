import json
import os
import uuid
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("TABLE_NAME", "employees"))


def lambda_handler(event, context):
    # API Gateway HTTP API (payload format 2.0)
    method = event.get("requestContext", {}).get("http", {}).get("method")
    path = event.get("rawPath") or event.get("path")

    # Health check
    if method == "GET" and path == "/health":
        return response(200, {"status": "healthy"})

    # Get all employees
    if method == "GET" and path == "/employees":
        result = table.scan()
        return response(200, result.get("Items", []))

    # Create employee
    if method == "POST" and path == "/employees":
        try:
            body = json.loads(event.get("body") or "{}")
        except json.JSONDecodeError:
            return response(400, {"message": "Invalid JSON body"})

        employee = {
            "employee_id": str(uuid.uuid4()),
            "name": body.get("name"),
            "email": body.get("email"),
            "department": body.get("department")
        }

        table.put_item(Item=employee)

        return response(201, employee)

    return response(404, {"message": "Route not found"})


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }