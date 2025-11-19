# --- Импорты ---
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database
from config import DELIVERY_TYPES, CUSTOMS_FEE_PERCENT
from utils import convert_to_rub, format_price
from keyboards import (
    get_cart_keyboard,
    get_delivery_keyboard,
    get_order_confirmation_keyboard
)


# --- Инициализация роутера ---
router = Router()


# --- Просмотр корзины ---
@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message):
    """Показать корзину"""
    client = await database.get_client_by_telegram_id(message.from_user.id)
    
    if not client:
        await message.answer("Пожалуйста, сначала зарегистрируйтесь через /start")
        return
    
    cart_items = await database.get_cart_items(client.id)
    
    if not cart_items:
        await message.answer(
            "🛒 Ваша корзина пуста.\n\n"
            "Перейдите в каталог товаров, чтобы добавить что-нибудь!"
        )
        return
    
    # Получаем курсы валют
    exchange_rates = {}
    for currency in ['USD', 'EUR', 'CNY', 'JPY']:
        rate = await database.get_exchange_rate(currency)
        if rate:
            exchange_rates[currency] = rate.rate_to_rub
    
    # Формируем текст корзины
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    total = 0.0
    
    for cart_item, product in cart_items:
        price_rub = await convert_to_rub(product.price_original, product.currency, exchange_rates)
        item_total = price_rub * cart_item.quantity
        total += item_total
        
        text += (
            f"🛍️ <b>{product.name}</b>\n"
            f"   Количество: {cart_item.quantity} шт.\n"
            f"   Цена: {format_price(price_rub)} ₽\n"
            f"   Сумма: {format_price(item_total)} ₽\n\n"
        )
    
    text += f"💰 <b>Итого: {format_price(total)} ₽</b>"
    
    await message.answer(
        text,
        reply_markup=get_cart_keyboard(cart_items)
    )


# --- Удаление из корзины ---
@router.callback_query(F.data.startswith("remove_from_cart_"))
async def remove_from_cart(callback: CallbackQuery):
    """Удаление товара из корзины"""
    product_id = int(callback.data.split("_")[3])
    client = await database.get_client_by_telegram_id(callback.from_user.id)
    
    if not client:
        await callback.answer("Ошибка: клиент не найден", show_alert=True)
        return
    
    product = await database.get_product_by_id(product_id)
    await database.remove_from_cart(client.id, product_id)
    
    # Обновляем корзину
    cart_items = await database.get_cart_items(client.id)
    
    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста.\n\n"
            "Перейдите в каталог товаров, чтобы добавить что-нибудь!"
        )
        await callback.answer(f"✅ Товар '{product.name}' удален из корзины")
        return
    
    # Получаем курсы валют
    exchange_rates = {}
    for currency in ['USD', 'EUR', 'CNY', 'JPY']:
        rate = await database.get_exchange_rate(currency)
        if rate:
            exchange_rates[currency] = rate.rate_to_rub
    
    # Формируем обновленный текст корзины
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    total = 0.0
    
    for cart_item, product in cart_items:
        price_rub = await convert_to_rub(product.price_original, product.currency, exchange_rates)
        item_total = price_rub * cart_item.quantity
        total += item_total
        
        text += (
            f"🛍️ <b>{product.name}</b>\n"
            f"   Количество: {cart_item.quantity} шт.\n"
            f"   Цена: {format_price(price_rub)} ₽\n"
            f"   Сумма: {format_price(item_total)} ₽\n\n"
        )
    
    text += f"💰 <b>Итого: {format_price(total)} ₽</b>"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cart_keyboard(cart_items)
    )
    await callback.answer(f"✅ Товар удален из корзины")


# --- Очистка корзины ---
@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    """Очистка корзины"""
    client = await database.get_client_by_telegram_id(callback.from_user.id)
    
    if not client:
        await callback.answer("Ошибка: клиент не найден", show_alert=True)
        return
    
    await database.clear_cart(client.id)
    
    await callback.message.edit_text(
        "🛒 Корзина очищена!\n\n"
        "Перейдите в каталог товаров, чтобы добавить что-нибудь!"
    )
    await callback.answer("✅ Корзина очищена")


# --- Оформление заказа ---
@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, state: FSMContext):
    """Начало оформления заказа"""
    client = await database.get_client_by_telegram_id(callback.from_user.id)
    
    if not client:
        await callback.answer("Ошибка: клиент не найден", show_alert=True)
        return
    
    cart_items = await database.get_cart_items(client.id)
    
    if not cart_items:
        await callback.answer("Корзина пуста!", show_alert=True)
        return
    
    # Сохраняем корзину в состояние
    await state.update_data(cart_items=cart_items)
    
    await callback.message.edit_text(
        "📦 <b>Выберите тип доставки:</b>\n\n"
        "🐌 <b>Эконом</b> - 20-30 дней\n"
        "📦 <b>Стандарт</b> - 10-15 дней (стоимость +50%)\n"
        "🚀 <b>Экспресс</b> - 5-7 дней (стоимость +150%)",
        reply_markup=get_delivery_keyboard()
    )
    await callback.answer()


# --- Выбор доставки ---
@router.callback_query(F.data.startswith("delivery_"))
async def select_delivery(callback: CallbackQuery, state: FSMContext):
    """Выбор типа доставки"""
    delivery_type = callback.data.split("_")[1]
    client = await database.get_client_by_telegram_id(callback.from_user.id)
    
    data = await state.get_data()
    cart_items = data.get("cart_items", [])
    
    if not cart_items:
        await callback.answer("Корзина пуста!", show_alert=True)
        return
    
    # Получаем курсы валют
    exchange_rates = {}
    for currency in ['USD', 'EUR', 'CNY', 'JPY']:
        rate = await database.get_exchange_rate(currency)
        if rate:
            exchange_rates[currency] = rate.rate_to_rub
    
    # Рассчитываем стоимость
    subtotal = 0.0
    for cart_item, product in cart_items:
        price_rub = await convert_to_rub(product.price_original, product.currency, exchange_rates)
        subtotal += price_rub * cart_item.quantity
    
    # Базовая доставка (средняя по странам)
    base_delivery = 1000.0
    delivery_multiplier = DELIVERY_TYPES[delivery_type]['multiplier']
    delivery_cost = base_delivery * delivery_multiplier
    
    # Таможенный сбор
    customs_fee = subtotal * CUSTOMS_FEE_PERCENT
    
    # Итого
    total = subtotal + delivery_cost + customs_fee
    
    # Сохраняем данные заказа
    await state.update_data(
        delivery_type=delivery_type,
        subtotal=subtotal,
        delivery_cost=delivery_cost,
        customs_fee=customs_fee,
        total=total
    )
    
    # Формируем текст подтверждения
    text = (
        "📋 <b>Подтверждение заказа</b>\n\n"
        f"👤 Получатель: {client.name}\n"
        f"📱 Телефон: {client.phone}\n"
        f"📍 Адрес: {client.address}\n\n"
        "<b>Товары:</b>\n"
    )
    
    for cart_item, product in cart_items:
        price_rub = await convert_to_rub(product.price_original, product.currency, exchange_rates)
        text += f"• {product.name} x{cart_item.quantity} - {format_price(price_rub * cart_item.quantity)} ₽\n"
    
    text += (
        f"\n💰 Стоимость товаров: {format_price(subtotal)} ₽\n"
        f"📦 Доставка ({delivery_type}): {format_price(delivery_cost)} ₽\n"
        f"🛃 Таможенный сбор (15%): {format_price(customs_fee)} ₽\n\n"
        f"<b>💵 Итого к оплате: {format_price(total)} ₽</b>\n\n"
        f"⏱️ Срок доставки: {DELIVERY_TYPES[delivery_type]['days']} дней\n\n"
        "⚠️ Напоминаем: это учебный проект, реальной оплаты не требуется."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_order_confirmation_keyboard()
    )
    await callback.answer()


# --- Подтверждение заказа ---
@router.callback_query(F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и создание заказа"""
    client = await database.get_client_by_telegram_id(callback.from_user.id)
    
    data = await state.get_data()
    cart_items = data.get("cart_items", [])
    delivery_type = data.get("delivery_type")
    total = data.get("total")
    delivery_cost = data.get("delivery_cost")
    customs_fee = data.get("customs_fee")
    
    if not cart_items or not delivery_type:
        await callback.answer("Ошибка при оформлении заказа", show_alert=True)
        return
    
    # Создаем заказ
    order = await database.create_order(
        client_id=client.id,
        total_amount=total,
        delivery_cost=delivery_cost,
        customs_fee=customs_fee,
        delivery_type=delivery_type,
        cart_items=cart_items
    )
    
    # Очищаем корзину
    await database.clear_cart(client.id)
    
    # Очищаем состояние
    await state.clear()
    
    await callback.message.edit_text(
        f"✅ <b>Заказ успешно оформлен!</b>\n\n"
        f"📦 Номер отслеживания: <code>{order.tracking_number}</code>\n"
        f"💰 Сумма: {format_price(total)} ₽\n"
        f"📅 Дата заказа: {order.order_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"🚚 Тип доставки: {delivery_type}\n"
        f"📊 Статус: {order.status}\n\n"
        "Вы можете отслеживать статус заказа в разделе 'Мои заказы'."
    )
    await callback.answer("✅ Заказ оформлен!")


# --- Отмена оформления ---
@router.callback_query(F.data == "cancel_checkout")
async def cancel_checkout(callback: CallbackQuery, state: FSMContext):
    """Отмена оформления заказа"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Оформление заказа отменено.\n\n"
        "Вы можете вернуться в корзину или продолжить покупки."
    )
    await callback.answer()


# --- Возврат в корзину ---
@router.callback_query(F.data == "back_to_cart")
async def back_to_cart(callback: CallbackQuery, state: FSMContext):
    """Возврат в корзину"""
    client = await database.get_client_by_telegram_id(callback.from_user.id)
    cart_items = await database.get_cart_items(client.id)
    
    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста.\n\n"
            "Перейдите в каталог товаров, чтобы добавить что-нибудь!"
        )
        await callback.answer()
        return
    
    # Получаем курсы валют
    exchange_rates = {}
    for currency in ['USD', 'EUR', 'CNY', 'JPY']:
        rate = await database.get_exchange_rate(currency)
        if rate:
            exchange_rates[currency] = rate.rate_to_rub
    
    # Формируем текст корзины
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    total = 0.0
    
    for cart_item, product in cart_items:
        price_rub = await convert_to_rub(product.price_original, product.currency, exchange_rates)
        item_total = price_rub * cart_item.quantity
        total += item_total
        
        text += (
            f"🛍️ <b>{product.name}</b>\n"
            f"   Количество: {cart_item.quantity} шт.\n"
            f"   Цена: {format_price(price_rub)} ₽\n"
            f"   Сумма: {format_price(item_total)} ₽\n\n"
        )
    
    text += f"💰 <b>Итого: {format_price(total)} ₽</b>"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cart_keyboard(cart_items)
    )
    await callback.answer()
