# --- Импорты ---
from typing import Optional, List
from datetime import datetime
import random
import string

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, delete, update, func

from models import (
    Base, Client, Country, Shop, Category, Product, Order, OrderItem,
    ExchangeRate, Admin, CartItem
)
from config import DATABASE_URL


# --- Подключение к базе данных ---
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# --- Инициализация базы данных ---
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# --- Утилиты ---
async def get_one(session: AsyncSession, stmt) -> Optional[object]:
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def generate_tracking_number() -> str:
    """Генерация уникального номера отслеживания"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))


# --- Методы: Клиенты ---
async def get_client_by_telegram_id(telegram_id: int) -> Optional[Client]:
    async with async_session() as session:
        return await get_one(session, select(Client).where(Client.telegram_id == telegram_id))


async def get_client_by_id(client_id: int) -> Optional[Client]:
    async with async_session() as session:
        return await get_one(session, select(Client).where(Client.id == client_id))


async def create_client(telegram_id: int, name: str, phone: str, address: str = None) -> Client:
    async with async_session() as session:
        client = Client(telegram_id=telegram_id, name=name, phone=phone, address=address)
        session.add(client)
        await session.commit()
        await session.refresh(client)
        return client


async def update_client_address(client_id: int, address: str) -> None:
    async with async_session() as session:
        await session.execute(
            update(Client).where(Client.id == client_id).values(address=address)
        )
        await session.commit()


async def get_all_clients() -> List[Client]:
    async with async_session() as session:
        result = await session.execute(select(Client))
        return result.scalars().all()


# --- Методы: Страны ---
async def get_all_countries() -> List[Country]:
    async with async_session() as session:
        result = await session.execute(select(Country))
        return result.scalars().all()


async def get_country_by_id(country_id: int) -> Optional[Country]:
    async with async_session() as session:
        return await get_one(session, select(Country).where(Country.id == country_id))


async def add_country(name: str, currency: str, flag_emoji: str, delivery_base_cost: int) -> Country:
    async with async_session() as session:
        country = Country(
            name=name,
            currency=currency,
            flag_emoji=flag_emoji,
            delivery_base_cost=delivery_base_cost
        )
        session.add(country)
        await session.commit()
        await session.refresh(country)
        return country


# --- Методы: Магазины ---
async def get_shops_by_country(country_id: int) -> List[Shop]:
    async with async_session() as session:
        result = await session.execute(select(Shop).where(Shop.country_id == country_id))
        return result.scalars().all()


async def get_shop_by_id(shop_id: int) -> Optional[Shop]:
    async with async_session() as session:
        return await get_one(session, select(Shop).where(Shop.id == shop_id))


async def add_shop(country_id: int, name: str, description: str = None, website: str = None) -> Shop:
    async with async_session() as session:
        shop = Shop(
            country_id=country_id,
            name=name,
            description=description,
            website=website
        )
        session.add(shop)
        await session.commit()
        await session.refresh(shop)
        return shop


# --- Методы: Категории ---
async def get_all_categories() -> List[Category]:
    async with async_session() as session:
        result = await session.execute(select(Category))
        return result.scalars().all()


async def get_category_by_id(category_id: int) -> Optional[Category]:
    async with async_session() as session:
        return await get_one(session, select(Category).where(Category.id == category_id))


async def add_category(name: str, description: str = None) -> Category:
    async with async_session() as session:
        category = Category(name=name, description=description)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category


# --- Методы: Товары ---
async def get_products_by_shop(shop_id: int) -> List[Product]:
    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.shop_id == shop_id))
        return result.scalars().all()


async def get_products_by_category(category_id: int) -> List[Product]:
    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.category_id == category_id))
        return result.scalars().all()


async def get_product_by_id(product_id: int) -> Optional[Product]:
    async with async_session() as session:
        return await get_one(session, select(Product).where(Product.id == product_id))


async def add_product(
    shop_id: int,
    category_id: int,
    name: str,
    description: str,
    price_original: float,
    currency: str,
    weight: float = None,
    photo_url: str = None,
    photo_file_id: str = None
) -> Product:
    async with async_session() as session:
        product = Product(
            shop_id=shop_id,
            category_id=category_id,
            name=name,
            description=description,
            price_original=price_original,
            currency=currency,
            weight=weight,
            photo_url=photo_url,
            photo_file_id=photo_file_id
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product


async def update_product(
    product_id: int,
    name: str = None,
    description: str = None,
    price_original: float = None,
    photo_file_id: str = None
) -> None:
    update_data = {}
    if name:
        update_data["name"] = name
    if description:
        update_data["description"] = description
    if price_original is not None:
        update_data["price_original"] = price_original
    if photo_file_id:
        update_data["photo_file_id"] = photo_file_id

    if update_data:
        async with async_session() as session:
            await session.execute(
                update(Product).where(Product.id == product_id).values(**update_data)
            )
            await session.commit()


async def delete_product(product_id: int) -> None:
    async with async_session() as session:
        await session.execute(delete(Product).where(Product.id == product_id))
        await session.commit()


# --- Методы: Курсы валют ---
async def get_exchange_rate(currency: str) -> Optional[ExchangeRate]:
    async with async_session() as session:
        return await get_one(session, select(ExchangeRate).where(ExchangeRate.currency == currency))


async def set_exchange_rate(currency: str, rate_to_rub: float) -> ExchangeRate:
    async with async_session() as session:
        rate = await get_one(session, select(ExchangeRate).where(ExchangeRate.currency == currency))
        if rate:
            await session.execute(
                update(ExchangeRate)
                .where(ExchangeRate.currency == currency)
                .values(rate_to_rub=rate_to_rub, update_date=datetime.now())
            )
            await session.commit()
            return await get_one(session, select(ExchangeRate).where(ExchangeRate.currency == currency))
        else:
            new_rate = ExchangeRate(currency=currency, rate_to_rub=rate_to_rub)
            session.add(new_rate)
            await session.commit()
            await session.refresh(new_rate)
            return new_rate


# --- Методы: Корзина ---
async def get_cart_items(client_id: int) -> List[tuple]:
    """Возвращает список кортежей (CartItem, Product)"""
    async with async_session() as session:
        result = await session.execute(
            select(CartItem, Product)
            .join(Product, CartItem.product_id == Product.id)
            .where(CartItem.client_id == client_id)
        )
        return result.all()


async def add_to_cart(client_id: int, product_id: int, quantity: int = 1) -> CartItem:
    async with async_session() as session:
        # Проверяем, есть ли уже товар в корзине
        cart_item = await get_one(
            session,
            select(CartItem).where(
                CartItem.client_id == client_id,
                CartItem.product_id == product_id
            )
        )
        if cart_item:
            # Увеличиваем количество
            await session.execute(
                update(CartItem)
                .where(CartItem.id == cart_item.id)
                .values(quantity=cart_item.quantity + quantity)
            )
        else:
            # Добавляем новый товар
            cart_item = CartItem(client_id=client_id, product_id=product_id, quantity=quantity)
            session.add(cart_item)
        await session.commit()
        return cart_item


async def remove_from_cart(client_id: int, product_id: int) -> None:
    async with async_session() as session:
        await session.execute(
            delete(CartItem).where(
                CartItem.client_id == client_id,
                CartItem.product_id == product_id
            )
        )
        await session.commit()


async def clear_cart(client_id: int) -> None:
    async with async_session() as session:
        await session.execute(delete(CartItem).where(CartItem.client_id == client_id))
        await session.commit()


# --- Методы: Заказы ---
async def create_order(
    client_id: int,
    total_amount: float,
    delivery_cost: float,
    customs_fee: float,
    delivery_type: str,
    cart_items: List[tuple]
) -> Order:
    async with async_session() as session:
        tracking_number = generate_tracking_number()
        order = Order(
            client_id=client_id,
            total_amount=total_amount,
            delivery_cost=delivery_cost,
            customs_fee=customs_fee,
            delivery_type=delivery_type,
            tracking_number=tracking_number
        )
        session.add(order)
        await session.flush()

        # Добавляем товары в заказ
        for cart_item, product in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=cart_item.quantity,
                price_rub=product.price_original  # Здесь должна быть цена в рублях
            )
            session.add(order_item)

        await session.commit()
        await session.refresh(order)
        return order


async def get_client_orders(client_id: int) -> List[Order]:
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .where(Order.client_id == client_id)
            .order_by(Order.order_date.desc())
        )
        return result.scalars().all()


async def get_order_by_id(order_id: int) -> Optional[Order]:
    async with async_session() as session:
        return await get_one(session, select(Order).where(Order.id == order_id))


async def get_order_items(order_id: int) -> List[tuple]:
    """Возвращает список кортежей (OrderItem, Product)"""
    async with async_session() as session:
        result = await session.execute(
            select(OrderItem, Product)
            .join(Product, OrderItem.product_id == Product.id)
            .where(OrderItem.order_id == order_id)
        )
        return result.all()


async def update_order_status(order_id: int, status: str) -> None:
    async with async_session() as session:
        await session.execute(
            update(Order).where(Order.id == order_id).values(status=status)
        )
        await session.commit()


async def cancel_order(order_id: int) -> None:
    await update_order_status(order_id, '❌ Отменен')


async def get_all_orders() -> List[Order]:
    async with async_session() as session:
        result = await session.execute(select(Order).order_by(Order.order_date.desc()))
        return result.scalars().all()


# --- Методы: Администраторы ---
async def is_admin(telegram_id: int) -> bool:
    async with async_session() as session:
        admin = await get_one(session, select(Admin).where(Admin.telegram_id == telegram_id))
        return admin is not None


async def add_admin(telegram_id: int, name: str) -> Admin:
    async with async_session() as session:
        admin = Admin(telegram_id=telegram_id, name=name)
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        return admin


# --- Закрытие соединения ---
async def close_db():
    await engine.dispose()

# --- Методы: Товары (дополнительные функции) ---

async def get_all_products() -> List[Product]:
    """Получить все товары"""
    async with async_session() as session:
        result = await session.execute(select(Product).order_by(Product.id.desc()))
        return result.scalars().all()


async def get_products_by_shop_and_category(shop_id: int, category_id: int) -> List[Product]:
    """Получить товары по магазину и категории"""
    async with async_session() as session:
        result = await session.execute(
            select(Product)
            .where(Product.shop_id == shop_id, Product.category_id == category_id)
            .order_by(Product.id.desc())
        )
        return result.scalars().all()