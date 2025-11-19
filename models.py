# --- Импорты ---
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


# --- Базовая модель ---
Base = declarative_base()


# --- Модель клиента ---
class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(Text, nullable=True)  # Адрес доставки в России
    registration_date = Column(DateTime, default=datetime.now)

    orders = relationship(
        'Order',
        back_populates='client',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<Client(id={self.id}, telegram_id={self.telegram_id}, name='{self.name}')>"


# --- Модель страны ---
class Country(Base):
    __tablename__ = 'countries'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    currency = Column(String, nullable=False)  # USD, EUR, CNY, JPY
    flag_emoji = Column(String, nullable=False)
    delivery_base_cost = Column(Integer, nullable=False)  # Базовая стоимость доставки в рублях

    shops = relationship(
        'Shop',
        back_populates='country',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<Country(id={self.id}, name='{self.name}', currency='{self.currency}')>"


# --- Модель магазина ---
class Shop(Base):
    __tablename__ = 'shops'

    id = Column(Integer, primary_key=True)
    country_id = Column(Integer, ForeignKey('countries.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    website = Column(String, nullable=True)

    country = relationship('Country', back_populates='shops')
    products = relationship(
        'Product',
        back_populates='shop',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<Shop(id={self.id}, name='{self.name}')>"


# --- Модель категории ---
class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)

    products = relationship(
        'Product',
        back_populates='category',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


# --- Модель товара ---
class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey('shops.id', ondelete='CASCADE'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price_original = Column(Float, nullable=False)  # Цена в оригинальной валюте
    currency = Column(String, nullable=False)  # USD, EUR, CNY, JPY
    weight = Column(Float, nullable=True)  # Вес в кг
    photo_url = Column(String, nullable=True)  # URL фото
    photo_file_id = Column(String, nullable=True)  # Telegram file_id

    shop = relationship('Shop', back_populates='products')
    category = relationship('Category', back_populates='products')
    order_items = relationship(
        'OrderItem',
        back_populates='product',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price_original} {self.currency})>"


# --- Модель заказа ---
class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    total_amount = Column(Float, nullable=False)  # Общая сумма в рублях
    delivery_cost = Column(Float, nullable=False)  # Стоимость доставки
    customs_fee = Column(Float, nullable=False)  # Таможенный сбор
    status = Column(String, default='📦 Обработка')  # Статус заказа
    order_date = Column(DateTime, default=datetime.now)
    tracking_number = Column(String, unique=True, nullable=False)  # Номер отслеживания
    delivery_type = Column(String, nullable=False)  # эконом, стандарт, экспресс

    client = relationship('Client', back_populates='orders')
    order_items = relationship(
        'OrderItem',
        back_populates='order',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return (
            f"<Order(id={self.id}, tracking_number='{self.tracking_number}', "
            f"status='{self.status}')>"
        )


# --- Модель элемента заказа ---
class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_rub = Column(Float, nullable=False)  # Цена в рублях на момент заказа

    order = relationship('Order', back_populates='order_items')
    product = relationship('Product', back_populates='order_items')

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id})>"


# --- Модель курса валют ---
class ExchangeRate(Base):
    __tablename__ = 'exchange_rates'

    id = Column(Integer, primary_key=True)
    currency = Column(String, unique=True, nullable=False)  # USD, EUR, CNY, JPY
    rate_to_rub = Column(Float, nullable=False)  # Курс к рублю
    update_date = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<ExchangeRate(currency='{self.currency}', rate={self.rate_to_rub})>"


# --- Модель администратора ---
class Admin(Base):
    __tablename__ = 'admins'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String, nullable=False)

    def __repr__(self):
        return f"<Admin(id={self.id}, telegram_id={self.telegram_id}, name='{self.name}')>"


# --- Модель корзины ---
class CartItem(Base):
    __tablename__ = 'cart_items'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    def __repr__(self):
        return f"<CartItem(id={self.id}, client_id={self.client_id}, product_id={self.product_id})>"
