import uuid
from .repository import ShippingRepository
from .publisher import ShippingPublisher
from datetime import datetime, timezone


class ShippingService:
    SHIPPING_CREATED: str = 'created'
    SHIPPING_IN_PROGRESS: str = 'in progress'
    SHIPPING_COMPLETED: str = 'completed'
    SHIPPING_FAILED: str = 'failed'

    def __init__(self, repository, publisher):
        self.repository = repository
        self.publisher = publisher

    @staticmethod
    def list_available_shipping_type():
        return ['Нова Пошта', 'Укр Пошта', 'Meest Express', 'Самовивіз']

    def create_shipping(self, shipping_type, product_ids, order_id, due_date):
        if shipping_type not in self.list_available_shipping_type():
            raise ValueError("Shipping type is not available")
        shipping_id = str(uuid.uuid4())
        self.repository.create_shipping(shipping_type, product_ids, order_id, self.SHIPPING_CREATED, due_date)
        self.publisher.send_new_shipping(shipping_id)
        return shipping_id

    def process_shipping(self, shipping_id):
        shipping = self.repository.get_shipping(shipping_id)
        shipping_due_date = datetime.fromisoformat(shipping['due_date'])

    # If the due date has passed, mark the shipping as failed
        if shipping_due_date < datetime.now(timezone.utc):
            return self.fail_shipping(shipping_id)  # Ensure that 'fail_shipping' is called if the due date has passed.

    # If due date is in the future, mark the shipping as completed
        return self.complete_shipping(shipping_id)

    def process_shipping(self, shipping_id):
        shipping = self.repository.get_shipping(shipping_id)
        if datetime.fromisoformat(shipping['due_date']) < datetime.now(timezone.utc):
            return self.fail_shipping(shipping_id)

        return self.complete_shipping(shipping_id)


    def check_status(self, shipping_id):
        shipping = self.repository.get_shipping(shipping_id)

        return shipping['shipping_status']

    def fail_shipping(self, shipping_id):
        response = self.repository.update_shipping_status(shipping_id, self.SHIPPING_FAILED)
        return response['ResponseMetadata']

    def complete_shipping(self, shipping_id):
        response = self.repository.update_shipping_status(shipping_id, self.SHIPPING_COMPLETED)
        return response['ResponseMetadata']

