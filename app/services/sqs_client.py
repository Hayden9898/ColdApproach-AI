"""
Amazon SQS client wrapper for batch message queuing.
"""

import json
import os
from typing import Any, Dict, List


def _get_sqs_client():
    """Lazy-load boto3 SQS client."""
    import boto3

    return boto3.client(
        "sqs",
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
    )


def get_queue_url() -> str:
    return os.environ.get("SQS_QUEUE_URL", "")


def enqueue_message(queue_url: str, message_body: dict) -> Dict[str, Any]:
    """Send a JSON message to the SQS queue."""
    client = _get_sqs_client()
    response = client.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message_body),
    )
    return {"message_id": response.get("MessageId")}


def poll_messages(
    queue_url: str, max_messages: int = 1, wait_time: int = 5
) -> List[Dict[str, Any]]:
    """Long-poll SQS for messages. Returns list of messages."""
    client = _get_sqs_client()
    response = client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=max_messages,
        WaitTimeSeconds=wait_time,
    )
    return response.get("Messages", [])


def delete_message(queue_url: str, receipt_handle: str) -> None:
    """Delete a processed message from the queue."""
    client = _get_sqs_client()
    client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
