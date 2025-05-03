"""
Eshop module containing classes for managing products, shopping cart, orders, and shipments.
"""

from typing import Dict
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from services import ShippingService  # Переконайтеся, що модуль services доступний


class Product:
    """Class representing a product in the e-shop."""

    def __init__(self, name: str, price: float, available_amount: int):
        """Initialize a Product instance."""
        if name is None:
            raise ValueError("Product name cannot be None")
        self.name = name
        self.price = price
        self.available_amount = available_amount

    def is_available(self, requested_amount: int) -> bool:
        """Check if the requested amount of product is available."""
        return self.available_amount >= requested_amount

    def buy(self, requested_amount: int) -> None:
        """Reduce available amount after purchase."""
        if requested_amount > self.available_amount:
            raise ValueError("Not enough stock available")
        self.available_amount -= requested_amount

    def __eq__(self, other: 'Product') -> bool:
        """Check if two products are equal based on name."""
        return self.name == other.name

    def __ne__(self, other: 'Product') -> bool:
        """Check if two products are not equal based on name."""
        return self.name != other.name

    def __hash__(self) -> int:
        """Generate hash based on product name."""
        return hash(self.name)

    def __str__(self) -> str:
        """Return string representation of the product."""
        return self.name


class ShoppingCart:
    """Class representing a shopping cart with products and their quantities."""

    def __init__(self):
        """Initialize an empty shopping cart."""
        self.products: Dict[Product, int] = {}

    def contains_product(self, product: Product) -> bool:
        """Check if the product is in the cart."""
        return product in self.products

    def calculate_total(self) -> float:
        """Calculate the total price of products in the cart."""
        return sum(p.price * count for p, count in self.products.items())

    def add_product(self, product: Product, amount: int) -> None:
        """Add a product to the cart with specified amount."""
        if not product.is_available(amount):
            msg = f"Product {product} has only {product.available_amount} items"
            raise ValueError(msg)
        self.products[product] = amount

    def remove_product(self, product: Product) -> None:
        """Remove a product from the cart."""
        if product in self.products:
            del self.products[product]

    def submit_cart_order(self) -> list[str]:
        """Submit the cart order and clear the cart."""
        product_ids = []
        for product, count in self.products.items():
            product.buy(count)
            product_ids.append(str(product))
        self.products.clear()
        return product_ids


@dataclass
class Order:
    """Class representing an order in the e-shop."""

    cart: ShoppingCart
    shipping_service: ShippingService
    order_id: str = str(uuid.uuid4())

    def place_order(self, shipping_type: str, due_date: datetime = None) -> str:
        """Place an order with the specified shipping type and due date."""
        if not due_date:
            due_date = datetime.now(timezone.utc) + timedelta(seconds=3)
        product_ids = self.cart.submit_cart_order()
        print(due_date)
        return self.shipping_service.create_shipping(
            shipping_type, product_ids, self.order_id, due_date
        )


@dataclass
class Shipment:
    """Class representing a shipment in the e-shop."""

    shipping_id: str
    shipping_service: ShippingService

    def check_shipping_status(self) -> str:
        """Check the status of the shipment."""
        return self.shipping_service.check_status(self.shipping_id)