import json
import os
import uuid
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("TABLE_NAME", "employees"))

def lambda_handler(event, context):
    method = event.get("httpMethod")
    path = event.get("path")

    if method == "GET" and path == "/health":
        return response(200, {"status": "healthy"})

    if method == "GET" and path == "/employees":
        result = table.scan()
        return response(200, result.get("Items", []))

    if method == "POST" and path == "/employees":
        body = json.loads(event.get("body", "{}"))

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