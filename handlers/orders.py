# --- Импорты ---
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

import database
from utils import format_price
from keyboards import (
    get_orders_keyboard,
    get_order_keyboard
)


# --- Инициализация роутера ---
router = Router()


# --- Просмотр заказов ---
@router.message(F.text == "📦 Мои заказы")
async def show_orders(message: Message):
    """Показать список заказов"""
    client = await database.get_client_by_telegram_id(message.from_user.id)
    
    if not client:
        await message.answer("Пожалуйста, сначала зарегистрируйтесь через /start")
        return
    
    orders = await database.get_client_orders(client.id)
    
    if not orders:
        await message.answer(
            "📦 У вас пока нет заказов.\n\n"
            "Перейдите в каталог товаров, чтобы сделать первый заказ!"
        )
        return
    
    await message.answer(
        f"📦 <b>Ваши заказы ({len(orders)}):</b>\n\n"
        "Выберите заказ для просмотра деталей:",
        reply_markup=get_orders_keyboard(orders)
    )


# --- Просмотр деталей заказа ---
@router.callback_query(F.data.startswith("order_"))
async def show_order_details(callback: CallbackQuery):
    """Показать детали заказа"""
    order_id = int(callback.data.split("_")[1])
    order = await database.get_order_by_id(order_id)
    
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    # Получаем товары заказа
    order_items = await database.get_order_items(order.id)
    
    # Формируем текст
    text = (
        f"📦 <b>Заказ #{order.tracking_number}</b>\n\n"
        f"📅 Дата: {order.order_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"📊 Статус: {order.status}\n"
        f"🚚 Тип доставки: {order.delivery_type}\n\n"
        "<b>Товары:</b>\n"
    )
    
    for order_item, product in order_items:
        text += f"• {product.name} x{order_item.quantity} - {format_price(order_item.price_rub * order_item.quantity)} ₽\n"
    
    text += (
        f"\n💰 Стоимость товаров: {format_price(order.total_amount - order.delivery_cost - order.customs_fee)} ₽\n"
        f"📦 Доставка: {format_price(order.delivery_cost)} ₽\n"
        f"🛃 Таможенный сбор: {format_price(order.customs_fee)} ₽\n\n"
        f"<b>💵 Итого: {format_price(order.total_amount)} ₽</b>"
    )
    
    # Проверяем, можно ли отменить заказ
    can_cancel = order.status == '📦 Обработка'
    
    await callback.message.edit_text(
        text,
        reply_markup=get_order_keyboard(order.id, can_cancel=can_cancel)
    )
    await callback.answer()


# --- Отмена заказа ---
@router.callback_query(F.data.startswith("cancel_order_"))
async def cancel_order(callback: CallbackQuery):
    """Отмена заказа"""
    order_id = int(callback.data.split("_")[2])
    order = await database.get_order_by_id(order_id)
    
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    if order.status != '📦 Обработка':
        await callback.answer(
            "Заказ можно отменить только в статусе 'Обработка'",
            show_alert=True
        )
        return
    
    await database.cancel_order(order.id)
    
    await callback.answer("✅ Заказ отменен", show_alert=True)
    
    # Обновляем информацию о заказе
    order = await database.get_order_by_id(order_id)
    order_items = await database.get_order_items(order.id)
    
    text = (
        f"📦 <b>Заказ #{order.tracking_number}</b>\n\n"
        f"📅 Дата: {order.order_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"📊 Статус: {order.status}\n"
        f"🚚 Тип доставки: {order.delivery_type}\n\n"
        "<b>Товары:</b>\n"
    )
    
    for order_item, product in order_items:
        text += f"• {product.name} x{order_item.quantity} - {format_price(order_item.price_rub * order_item.quantity)} ₽\n"
    
    text += (
        f"\n💰 Стоимость товаров: {format_price(order.total_amount - order.delivery_cost - order.customs_fee)} ₽\n"
        f"📦 Доставка: {format_price(order.delivery_cost)} ₽\n"
        f"🛃 Таможенный сбор: {format_price(order.customs_fee)} ₽\n\n"
        f"<b>💵 Итого: {format_price(order.total_amount)} ₽</b>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_order_keyboard(order.id, can_cancel=False)
    )


# --- Возврат к списку заказов ---
@router.callback_query(F.data == "back_to_orders")
async def back_to_orders(callback: CallbackQuery):
    """Возврат к списку заказов"""
    client = await database.get_client_by_telegram_id(callback.from_user.id)
    orders = await database.get_client_orders(client.id)
    
    if not orders:
        await callback.message.edit_text(
            "📦 У вас пока нет заказов.\n\n"
            "Перейдите в каталог товаров, чтобы сделать первый заказ!"
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        f"📦 <b>Ваши заказы ({len(orders)}):</b>\n\n"
        "Выберите заказ для просмотра деталей:",
        reply_markup=get_orders_keyboard(orders)
    )
    await callback.answer()
