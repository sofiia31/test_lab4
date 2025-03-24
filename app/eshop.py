from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import uuid
from typing import Dict
from services import ShippingService


# Модуль для опису продуктів, кошика та замовлень
class Product:
    """Клас, що описує товар для інтернет-магазину."""

    def __init__(self, name, price, available_amount):
        """
        Ініціалізація продукту.

        :param name: Назва продукту
        :param price: Ціна продукту
        :param available_amount: Кількість товару на складі
        :raises ValueError: Якщо назва продукту None
        """
        if name is None:
            raise ValueError("Product name cannot be None")
        self.name = name
        self.price = price
        self.available_amount = available_amount

    def is_available(self, requested_amount):
        """Перевіряє, чи доступна потрібна кількість товару."""
        return self.available_amount >= requested_amount

    def buy(self, requested_amount):
        """
        Купує необхідну кількість товару.

        :param requested_amount: Кількість товару для покупки
        :raises ValueError: Якщо товару не вистачає на складі
        """
        if requested_amount > self.available_amount:
            raise ValueError("Not enough stock available")
        self.available_amount -= requested_amount

    def __eq__(self, other):
        """Перевіряє рівність продуктів за назвою."""
        return self.name == other.name

    def __ne__(self, other):
        """Перевіряє нерівність продуктів за назвою."""
        return self.name != other.name

    def __hash__(self):
        """Обчислює хеш продукту на основі його назви."""
        return hash(self.name)

    def __str__(self):
        """Повертає назву продукту як рядок."""
        return self.name


class ShoppingCart:
    """Клас, що описує кошик покупок."""

    products: Dict[Product, int]

    def __init__(self):
        """Ініціалізація кошика покупок."""
        self.products = {}

    def contains_product(self, product):
        """Перевіряє, чи містить кошик даний продукт."""
        return product in self.products

    def calculate_total(self):
        """Обчислює загальну суму вартості продуктів у кошику."""
        return sum(p.price * count for p, count in self.products.items())

    def add_product(self, product: Product, amount: int):
        """
        Додає продукт до кошика.

        :param product: Продукт, що додається
        :param amount: Кількість продукту
        :raises ValueError: Якщо кількість продукту перевищує наявну
        """
        if not product.is_available(amount):
            raise ValueError(f"Product {product} has only {product.available_amount} items")
        self.products[product] = amount

    def remove_product(self, product):
        """Видаляє продукт з кошика."""
        if product in self.products:
            del self.products[product]

    def submit_cart_order(self):
        """
        Підтверджує замовлення і купує товари з кошика.

        Повертає список ідентифікаторів продуктів у замовленні.
        """
        product_ids = []
        for product, count in self.products.items():
            product.buy(count)
            product_ids.append(str(product))
        self.products.clear()

        return product_ids


@dataclass
class Order:
    """Клас, що описує замовлення."""

    cart: ShoppingCart
    shipping_service: ShippingService
    order_id: str = str(uuid.uuid4())

    def place_order(self, shipping_type, due_date: datetime = None):
        """
        Створює замовлення та обробляє його.

        :param shipping_type: Тип доставки
        :param due_date: Дата доставки (за замовчуванням поточна дата + 3 секунди)
        :returns: Ідентифікатор доставки
        """
        if not due_date:
            due_date = datetime.now(timezone.utc) + timedelta(seconds=3)
        product_ids = self.cart.submit_cart_order()
        return self.shipping_service.create_shipping(
            shipping_type,
            product_ids,
            self.order_id,
            due_date
        )


@dataclass()
class Shipment:
    """Клас, що описує доставку замовлення."""

    shipping_id: str
    shipping_service: ShippingService

    def check_shipping_status(self):
        """Перевіряє статус доставки за ідентифікатором."""
        return self.shipping_service.check_status(self.shipping_id)