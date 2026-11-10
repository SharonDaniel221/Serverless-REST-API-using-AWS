
import json
import os
import boto3
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["ORDERS_TABLE"])


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps(body, default=str)
    }


def lambda_handler(event, context):
    try:
        method = event.get("httpMethod")
        path_parameters = event.get("pathParameters") or {}
        order_id = path_parameters.get("orderId")

        if method == "OPTIONS":
            return response(200, {"message": "CORS preflight successful"})

        # CREATE
        if method == "POST":
            data = json.loads(event.get("body") or "{}")

            if not data.get("orderId"):
                return response(400, {"error": "orderId is required"})

            table.put_item(Item=data)

            return response(201, {
                "message": "Order created successfully",
                "order": data
            })

        # READ ALL
        elif method == "GET" and not order_id:
            result = table.scan()

            return response(200, {
                "orders": result.get("Items", [])
            })

        # READ ONE
        elif method == "GET" and order_id:
            result = table.get_item(
                Key={"orderId": order_id}
            )

            item = result.get("Item")

            if not item:
                return response(404, {"error": "Order not found"})

            return response(200, {"order": item})

        # UPDATE
        elif method == "PUT":
            if not order_id:
                return response(400, {"error": "orderId is required"})

            data = json.loads(event.get("body") or "{}")

            if not data:
                return response(400, {"error": "Update data is required"})

            update_fields = {
                key: value for key, value in data.items()
                if key != "orderId"
            }

            if not update_fields:
                return response(400, {"error": "No fields to update"})

            update_expression = "SET " + ", ".join(
                f"#{key} = :{key}" for key in update_fields
            )

            result = table.update_item(
                Key={"orderId": order_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames={
                    f"#{key}": key for key in update_fields
                },
                ExpressionAttributeValues={
                    f":{key}": value for key, value in update_fields.items()
                },
                ReturnValues="ALL_NEW"
            )

            return response(200, {
                "message": "Order updated successfully",
                "order": result.get("Attributes")
            })

        # DELETE
        elif method == "DELETE":
            if not order_id:
                return response(400, {"error": "orderId is required"})

            table.delete_item(
                Key={"orderId": order_id}
            )

            return response(200, {
                "message": "Order deleted successfully"
            })

        else:
            return response(405, {"error": "Method not allowed"})

    except Exception as error:
        print("Error:", str(error))
        return response(500, {"error": "Internal server error"})
