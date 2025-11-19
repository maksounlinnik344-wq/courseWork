# --- Импорты ---
from aiogram import Router, F
from aiogram.types import Message

import database


# --- Инициализация роутера ---
router = Router()


# --- Просмотр профиля ---
@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    """Показать профиль пользователя"""
    client = await database.get_client_by_telegram_id(message.from_user.id)
    
    if not client:
        await message.answer("Пожалуйста, сначала зарегистрируйтесь через /start")
        return
    
    # Получаем статистику заказов
    orders = await database.get_client_orders(client.id)
    total_orders = len(orders)
    total_spent = sum(order.total_amount for order in orders)
    
    # Подсчитываем заказы по статусам
    active_orders = len([o for o in orders if o.status not in ['✅ Получен', '❌ Отменен']])
    completed_orders = len([o for o in orders if o.status == '✅ Получен'])
    
    text = (
        "👤 <b>Ваш профиль</b>\n\n"
        f"📛 Имя: {client.name}\n"
        f"📱 Телефон: {client.phone}\n"
        f"📍 Адрес доставки: {client.address or 'Не указан'}\n"
        f"📅 Дата регистрации: {client.registration_date.strftime('%d.%m.%Y')}\n\n"
        "<b>📊 Статистика:</b>\n"
        f"📦 Всего заказов: {total_orders}\n"
        f"🔄 Активных заказов: {active_orders}\n"
        f"✅ Завершенных заказов: {completed_orders}\n"
        f"💰 Потрачено: {total_spent:,.2f} ₽\n\n"
        "Для изменения данных профиля обратитесь к администратору."
    )
    
    await message.answer(text)
