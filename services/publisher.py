import boto3
from .config import AWS_ENDPOINT_URL, AWS_REGION, SHIPPING_QUEUE

class ShippingPublisher:
    """Publisher for sending shipping messages to SQS queue."""

    def __init__(self):
        """Initialize SQS client and get queue URL."""
        self.client = boto3.client(
            "sqs",
            endpoint_url=AWS_ENDPOINT_URL,
            region_name=AWS_REGION,
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )
        try:
            # Спробувати отримати існуючу чергу
            response = self.client.get_queue_url(QueueName=SHIPPING_QUEUE)
            self.queue_url = response["QueueUrl"]
        except self.client.exceptions.QueueDoesNotExist:
            # Якщо черга не існує, створити її
            response = self.client.create_queue(QueueName=SHIPPING_QUEUE)
            self.queue_url = response["QueueUrl"]

    def send_new_shipping(self, shipping_id: str) -> str:
        """Send a new shipping ID to the SQS queue."""
        response = self.client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=shipping_id
        )
        return response['MessageId']

    def poll_shipping(self, batch_size: int = 10) -> list[str]:
        """Poll messages from the SQS queue."""
        messages = self.client.receive_message(
            QueueUrl=self.queue_url,
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=batch_size,
            WaitTimeSeconds=10
        )
        if 'Messages' not in messages:
            return []
        return [msg['Body'] for msg in messages['Messages']]