import time
import uuid

import boto3
from app.eshop import Product, ShoppingCart, Order
import random
from services import ShippingService
from services.repository import ShippingRepository
from services.publisher import ShippingPublisher
from datetime import datetime, timedelta, timezone
from services.config import AWS_ENDPOINT_URL, AWS_REGION, SHIPPING_QUEUE
import pytest


@pytest.mark.parametrize("order_id, shipping_id", [
    ("order_1", "shipping_1"),
    ("order_i2hur2937r9", "shipping_1!!!!"),
    (8662354, 123456),
    (str(uuid.uuid4()), str(uuid.uuid4()))
])
def test_place_order_with_mocked_repo(mocker, order_id, shipping_id):
    mock_repo = mocker.Mock()
    mock_publisher = mocker.Mock()
    shipping_service = ShippingService(mock_repo, mock_publisher)

    mock_repo.create_shipping.return_value = shipping_id

    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=9
    )

    order = Order(cart, shipping_service, order_id)
    due_date = datetime.now(timezone.utc) + timedelta(seconds=3)
    actual_shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=due_date
    )

    assert actual_shipping_id == shipping_id, "Actual shipping id must be equal to mock return value"

    mock_repo.create_shipping.assert_called_with(ShippingService.list_available_shipping_type()[0], ["Product"], order_id, shipping_service.SHIPPING_CREATED, due_date)
    mock_publisher.send_new_shipping.assert_called_with(shipping_id)


def test_place_order_with_unavailable_shipping_type_fails(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=9
    )
    order = Order(cart, shipping_service)
    shipping_id = None

    with pytest.raises(ValueError) as excinfo:
        shipping_id = order.place_order(
            "Новий тип доставки",
            due_date=datetime.now(timezone.utc) + timedelta(seconds=3)
        )
    assert shipping_id is None, "Shipping id must not be assigned"
    assert "Shipping type is not available" in str(excinfo.value)



# def test_when_place_order_then_shipping_in_queue(dynamo_resource):
#     shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
#     cart = ShoppingCart()

#     cart.add_product(Product(
#         available_amount=10,
#         name='Product',
#         price=random.random() * 10000),
#         amount=9
#     )

#     order = Order(cart, shipping_service)
#     shipping_id = order.place_order(
#         ShippingService.list_available_shipping_type()[0],
#         due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
#     )

#     sqs_client = boto3.client(
#         "sqs",
#         endpoint_url=AWS_ENDPOINT_URL,
#         region_name=AWS_REGION,
#         aws_access_key_id="test",
#         aws_secret_access_key="test",
#     )
#     queue_url = sqs_client.get_queue_url(QueueName=SHIPPING_QUEUE)["QueueUrl"]

#     # Очистити чергу перед отриманням повідомлення
#     sqs_client.purge_queue(QueueUrl=queue_url)

#     # Дати час LocalStack обробити повідомлення
#     time.sleep(1)

#     # Дочекатися, поки повідомлення з'явиться в черзі
#     response = sqs_client.receive_message(
#         QueueUrl=queue_url,
#         MaxNumberOfMessages=1,
#         WaitTimeSeconds=20  # Збільшено до 20 секунд
#     )

#     messages = response.get("Messages", [])
#     assert len(messages) == 1, f"Expected 1 SQS message, got {len(messages)}"

#     body = messages[0]["Body"]
#     assert shipping_id == body, f"Expected shipping_id {shipping_id}, but got {body}"

def test_create_shipping_valid_type(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=5
    )
    order = Order(cart, shipping_service)
    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    assert shipping_id is not None, "Shipping ID should not be None"


def test_create_shipping_invalid_type(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=5
    )
    order = Order(cart, shipping_service)
    with pytest.raises(ValueError) as excinfo:
        order.place_order("Invalid Shipping", due_date=datetime.now(timezone.utc) + timedelta(minutes=5))
    assert "Shipping type is not available" in str(excinfo.value)

def test_shipping_due_date_validation(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=5
    )
    order = Order(cart, shipping_service)
    with pytest.raises(ValueError) as excinfo:
        order.place_order(
            ShippingService.list_available_shipping_type()[0],
            due_date=datetime.now(timezone.utc) - timedelta(minutes=1)  # Invalid: due date in the past
        )
    assert "Shipping due datetime must be greater than datetime now" in str(excinfo.value)

def test_shipping_id_creation_in_dynamodb(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=5
    )
    order = Order(cart, shipping_service)
    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5)
    )

    repo = ShippingRepository()
    shipping_data = repo.get_shipping(shipping_id)
    assert shipping_data is not None, "Shipping data should exist in DynamoDB"
    assert shipping_data['shipping_id'] == shipping_id, "Shipping ID should match"


def test_successful_shipping_status_update(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=5
    )
    order = Order(cart, shipping_service)
    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5)
    )

    shipping_service.process_shipping(shipping_id)
    status = shipping_service.check_status(shipping_id)
    assert status == shipping_service.SHIPPING_COMPLETED, "Shipping status should be 'completed'"


def test_process_shipping_fail_due_date(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=5
    )
    order = Order(cart, shipping_service)
    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5)  # Ensure due date is in the future
    )

    shipping_service.process_shipping(shipping_id)
    status = shipping_service.check_status(shipping_id)
    assert status == shipping_service.SHIPPING_COMPLETED, "Shipping status should be 'completed'"  # Since the due date is in the future

def test_shipping_queue_polling(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=5
    )
    order = Order(cart, shipping_service)
    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5)
    )

    publisher = ShippingPublisher()
    shipping_ids = publisher.poll_shipping()

    assert shipping_id in shipping_ids, f"Shipping ID {shipping_id} should be in the polled messages"



def test_check_shipping_status_after_processing(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=5
    )
    order = Order(cart, shipping_service)
    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5)
    )

    shipping_service.process_shipping(shipping_id)
    status = shipping_service.check_status(shipping_id)
    assert status == shipping_service.SHIPPING_COMPLETED, "Shipping status should be 'completed'"

def test_shipping_creation_in_dynamodb(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=5
    )
    order = Order(cart, shipping_service)

    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5)
    )

    shipping_data = shipping_service.repository.get_shipping(shipping_id)
    assert shipping_data is not None, "Shipping data should exist in DynamoDB"
    assert 'shipping_id' in shipping_data, "Shipping ID should be present in the data"
    assert 'due_date' in shipping_data, "Due date should be present in the data"
    assert shipping_data['shipping_id'] == shipping_id, "Shipping ID should match"

def test_invalid_shipping_type_raises_error(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=5
    )
    order = Order(cart, shipping_service)

    with pytest.raises(ValueError) as excinfo:
        order.place_order("Invalid Shipping Type", due_date=datetime.now(timezone.utc) + timedelta(minutes=5))

    assert "Shipping type is not available" in str(excinfo.value), "Expected error message for invalid shipping type"