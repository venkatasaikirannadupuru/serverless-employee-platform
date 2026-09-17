import json
import os
import uuid

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

table = dynamodb.Table(os.environ.get("TABLE_NAME", "employees"))
topic_arn = os.environ.get("SNS_TOPIC_ARN")


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method")
    path = event.get("rawPath") or event.get("path")

    # Health check
    if method == "GET" and path == "/health":
        return response(200, {"status": "healthy"})

    # Get all employees
    if method == "GET" and path == "/employees":
        try:
            result = table.scan()
            return response(200, result.get("Items", []))
        except ClientError as error:
            print(f"DynamoDB scan error: {error}")
            return response(500, {"message": "Failed to fetch employees"})

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

        if not employee["name"] or not employee["email"]:
            return response(
                400,
                {"message": "name and email are required"}
            )

        try:
            table.put_item(Item=employee)

            publish_notification(
                f"Employee created: {employee['name']} "
                f"({employee['employee_id']})"
            )

            return response(201, employee)

        except ClientError as error:
            print(f"DynamoDB put error: {error}")
            return response(500, {"message": "Failed to create employee"})

    # Update employee
    if method == "PUT" and path.startswith("/employees/"):
        employee_id = path.split("/")[-1]

        try:
            body = json.loads(event.get("body") or "{}")
        except json.JSONDecodeError:
            return response(400, {"message": "Invalid JSON body"})

        update_parts = []
        expression_values = {}
        expression_names = {}

        if "name" in body:
            update_parts.append("#name = :name")
            expression_names["#name"] = "name"
            expression_values[":name"] = body["name"]

        if "email" in body:
            update_parts.append("email = :email")
            expression_values[":email"] = body["email"]

        if "department" in body:
            update_parts.append("department = :department")
            expression_values[":department"] = body["department"]

        if not update_parts:
            return response(
                400,
                {"message": "No fields provided for update"}
            )

        update_params = {
            "Key": {
                "employee_id": employee_id
            },
            "UpdateExpression": "SET " + ", ".join(update_parts),
            "ExpressionAttributeValues": expression_values,
            "ReturnValues": "ALL_NEW"
        }

        if expression_names:
            update_params["ExpressionAttributeNames"] = expression_names

        try:
            result = table.update_item(**update_params)

            employee = result.get("Attributes", {})

            publish_notification(
                f"Employee updated: {employee_id}"
            )

            return response(200, employee)

        except ClientError as error:
            print(f"DynamoDB update error: {error}")
            return response(
                500,
                {"message": "Failed to update employee"}
            )

    # Delete employee
    if method == "DELETE" and path.startswith("/employees/"):
        employee_id = path.split("/")[-1]

        try:
            result = table.delete_item(
                Key={"employee_id": employee_id},
                ReturnValues="ALL_OLD"
            )

            deleted_employee = result.get("Attributes")

            if not deleted_employee:
                return response(
                    404,
                    {"message": "Employee not found"}
                )

            publish_notification(
                f"Employee deleted: {employee_id}"
            )

            return response(
                200,
                {
                    "message": "Employee deleted successfully",
                    "employee_id": employee_id
                }
            )

        except ClientError as error:
            print(f"DynamoDB delete error: {error}")
            return response(
                500,
                {"message": "Failed to delete employee"}
            )

    return response(404, {"message": "Route not found"})


def publish_notification(message):
    if not topic_arn:
        print("SNS_TOPIC_ARN is not configured")
        return

    try:
        sns.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject="Employee Management Notification"
        )
    except ClientError as error:
        print(f"SNS notification failed: {error}")


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }