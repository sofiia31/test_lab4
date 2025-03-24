import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import boto3
from services.db import get_dynamodb_resource
from botocore.exceptions import NoCredentialsError
from services.config import AWS_ENDPOINT_URL, AWS_REGION

@pytest.fixture(scope="session", autouse=True)
def setup_localstack_resources():
    os.environ["AWS_ACCESS_KEY_ID"] = "test"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test"

    dynamo_client = boto3.client(
        "dynamodb",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION
    )
    
    try:
        existing_tables = dynamo_client.list_tables()["TableNames"]
        if "ShippingTable" not in existing_tables:
            dynamo_client.create_table(
                TableName="ShippingTable",
                KeySchema=[{"AttributeName": "shipping_id", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "shipping_id", "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST",
            )
    except NoCredentialsError:
        raise Exception("No AWS credentials found!")
    
@pytest.fixture
def dynamo_resource():
    # Підключення до локальної бази даних DynamoDB
    return get_dynamodb_resource()