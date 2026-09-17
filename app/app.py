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

        if not employee["name"] or not employee["email"]:
            return response(
                400,
                {"message": "name and email are required"}
            )

        table.put_item(Item=employee)

        publish_notification(
            f"Employee created: {employee['name']} "
            f"({employee['employee_id']})"
        )

        return response(201, employee)

    # Update employee
    if method == "PUT" and path.startswith("/employees/"):
        employee_id = path.split("/")[-1]

        try:
            body = json.loads(event.get("body") or "{}")
        except json.JSONDecodeError:
            return response(400, {"message": "Invalid JSON body"})

        update_fields = []
        expression_values = {}

        if "name" in body:
            update_fields.append("#name = :name")
            expression_values[":name"] = body["name"]

        if "email" in body:
            update_fields.append("email = :email")
            expression_values[":email"] = body["email"]

        if "department" in body:
            update_fields.append("department = :department")
            expression_values[":department"] = body["department"]

        if not update_fields:
            return response(
                400,
                {"message": "No fields provided for update"}
            )

        try:
            result = table.update_item(
                Key={"employee_id": employee_id},
                UpdateExpression="SET " + ", ".join(update_fields),
                ExpressionAttributeNames={"#name": "name"}
                if "name" in body else None,
                ExpressionAttributeValues=expression_values,
                ReturnValues="ALL_NEW"
            )

            employee = result.get("Attributes", {})

            publish_notification(
                f"Employee updated: {employee_id}"
            )

            return response(200, employee)

        except ClientError as error:
            return response(
                500,
                {"message": error.response["Error"]["Message"]}
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
            return response(
                500,
                {"message": error.response["Error"]["Message"]}
            )

    return response(404, {"message": "Route not found"})


def publish_notification(message):
    if not topic_arn:
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