import uuid
from datetime import datetime, timezone
from .repository import ShippingRepository
from .publisher import ShippingPublisher


class ShippingService:
    """Service for managing shipping operations."""

    SHIPPING_CREATED: str = 'created'
    SHIPPING_IN_PROGRESS: str = 'in progress'
    SHIPPING_COMPLETED: str = 'completed'
    SHIPPING_FAILED: str = 'failed'

    def __init__(self, repository: ShippingRepository, publisher: ShippingPublisher):
        """Initialize ShippingService with repository and publisher."""
        self.repository = repository
        self.publisher = publisher

    @staticmethod
    def list_available_shipping_type() -> list[str]:
        """Return list of available shipping types."""
        return ['Нова Пошта', 'Укр Пошта', 'Meest Express', 'Самовивіз']

    def create_shipping(self, shipping_type: str, product_ids: list[str], order_id: str, due_date: datetime) -> str:
        """Create a new shipping record and send it to the queue."""
        if shipping_type not in self.list_available_shipping_type():
            raise ValueError("Shipping type is not available")
        # Використовуємо shipping_id, повернутий repository.create_shipping
        shipping_id = self.repository.create_shipping(shipping_type, product_ids, order_id, self.SHIPPING_CREATED, due_date)
        if not shipping_id:  # Якщо repository не повертає shipping_id, генеруємо новий
            shipping_id = str(uuid.uuid4())
        self.publisher.send_new_shipping(shipping_id)
        return shipping_id

    def process_shipping(self, shipping_id: str) -> dict:
        """Process a shipping by checking its due date and updating status."""
        shipping = self.repository.get_shipping(shipping_id)
        if datetime.fromisoformat(shipping['due_date']) < datetime.now(timezone.utc):
            return self.fail_shipping(shipping_id)
        return self.complete_shipping(shipping_id)

    def check_status(self, shipping_id: str) -> str:
        """Check the status of a shipping."""
        shipping = self.repository.get_shipping(shipping_id)
        return shipping['shipping_status']

    def fail_shipping(self, shipping_id: str) -> dict:
        """Mark a shipping as failed."""
        response = self.repository.update_shipping_status(shipping_id, self.SHIPPING_FAILED)
        return response['ResponseMetadata']

    def complete_shipping(self, shipping_id: str) -> dict:
        """Mark a shipping as completed."""
        response = self.repository.update_shipping_status(shipping_id, self.SHIPPING_COMPLETED)
        return response['ResponseMetadata']