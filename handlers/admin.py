# --- Импорты ---
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

import database
from config import ADMIN_IDS
from utils import AdminStates, format_price
from keyboards import (
    get_admin_menu,
    get_main_menu,
    get_admin_orders_keyboard,
    get_admin_order_keyboard,
    get_status_keyboard,
    get_products_management_keyboard,
    get_cancel_keyboard
)

# --- Инициализация роутера ---
router = Router()


# --- Проверка админских прав ---
def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user_id in ADMIN_IDS


# --- Команда /admin для быстрого доступа ---
@router.message(Command("admin"))
async def admin_command(message: Message):
    """Быстрый доступ к админ-панели через команду"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав доступа к админ-панели.")
        return

    await message.answer(
        "🔑 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu()
    )


# --- Вход в админ-панель ---
@router.message(F.text == "🔑 Админ-панель")
async def admin_panel(message: Message):
    """Вход в админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав доступа к админ-панели.")
        return

    await message.answer(
        "🔑 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu()
    )


# --- Возврат в главное меню ---
@router.message(F.text == "🔙 Назад в меню")
async def back_to_main_menu(message: Message):
    """Возврат в главное меню"""
    is_admin_user = is_admin(message.from_user.id)
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_menu(is_admin=is_admin_user)
    )


# --- Просмотр всех заказов ---
@router.message(F.text == "📊 Все заказы")
async def show_all_orders(message: Message):
    """Показать все заказы"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав доступа.")
        return

    orders = await database.get_all_orders()

    if not orders:
        await message.answer("📦 Заказов пока нет.")
        return

    await message.answer(
        f"📊 <b>Все заказы ({len(orders)}):</b>\n\n"
        "Выберите заказ для просмотра и управления:",
        reply_markup=get_admin_orders_keyboard(orders)
    )


# --- Управление товарами (главное меню) ---
@router.message(F.text == "📦 Управление товарами")
async def manage_products(message: Message):
    """Главное меню управления товарами"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав доступа.")
        return

    await message.answer(
        "📦 <b>Управление товарами</b>\n\n"
        "Выберите действие:",
        reply_markup=get_products_management_keyboard()
    )


# --- Просмотр всех товаров ---
@router.callback_query(F.data == "view_products")
async def view_all_products(callback: CallbackQuery):
    """Показать все товары"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return

    products = await database.get_all_products()

    if not products:
        await callback.message.edit_text(
            "📦 Товаров пока нет.\n\n"
            "Хотите добавить первый товар?",
            reply_markup=get_products_management_keyboard()
        )
        return

    text = "📦 <b>Все товары:</b>\n\n"
    for product in products:
        shop = await database.get_shop_by_id(product.shop_id)
        category = await database.get_category_by_id(product.category_id)
        text += f"🆔 {product.id}. {product.name}\n"
        text += f"   💰 {product.price_original} {product.currency}\n"
        text += f"   🏪 {shop.name if shop else 'N/A'}\n"
        text += f"   📁 {category.name if category else 'N/A'}\n\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_products_management_keyboard()
    )
    await callback.answer()


# --- Начало добавления товара ---
@router.callback_query(F.data == "add_product")
async def start_adding_product(callback: CallbackQuery, state: FSMContext):
    """Начало добавления товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return

    shops = []
    countries = await database.get_all_countries()
    for country in countries:
        country_shops = await database.get_shops_by_country(country.id)
        shops.extend(country_shops)

    if not shops:
        await callback.message.edit_text(
            "❌ Сначала нужно создать страны и магазины.\n"
            "Обратитесь к разработчику для инициализации базы данных.",
            reply_markup=get_products_management_keyboard()
        )
        return

    text = "📦 <b>Добавление товара</b>\n\n<b>Доступные магазины:</b>\n"
    for shop in shops:
        text += f"{shop.id}. {shop.name}\n"

    text += "\nВведите номер магазина из списка или нажмите 'Отмена' для возврата к прошлому меню:"

    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.adding_product_shop)
    await callback.answer()


# --- Удаление товара ---
@router.callback_query(F.data == "delete_product")
async def start_deleting_product(callback: CallbackQuery, state: FSMContext):
    """Начало удаления товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return

    products = await database.get_all_products()

    if not products:
        await callback.message.edit_text(
            "❌ Товаров для удаления нет.",
            reply_markup=get_products_management_keyboard()
        )
        return

    text = "🗑️ <b>Удаление товара</b>\n\n<b>Доступные товары:</b>\n"
    for product in products:
        text += f"{product.id}. {product.name}\n"

    text += "\nВведите номер товара из списка для удаления или нажмите 'Отмена' для возврата к прошлому меню:"

    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.deleting_product)
    await callback.answer()


# --- Обработка удаления товара ---
@router.message(AdminStates.deleting_product)
async def process_delete_product(message: Message, state: FSMContext):
    """Обработка удаления товара"""
    if message.text.strip().lower() == 'отмена':
        await message.answer(
            "❌ Удаление отменено.",
            reply_markup=get_products_management_keyboard()
        )
        await state.clear()
        return

    try:
        product_id = int(message.text.strip())
        product = await database.get_product_by_id(product_id)

        if not product:
            await message.answer(
                "❌ Товар не найден. Попробуйте снова или нажмите 'Отмена':",
                reply_markup=get_cancel_keyboard()
            )
            return

        # Удаляем товар
        await database.delete_product(product_id)

        await message.answer(
            f"✅ Товар '{product.name}' успешно удален!",
            reply_markup=get_products_management_keyboard()
        )
        await state.clear()

    except ValueError:
        await message.answer(
            "❌ Введите корректный номер товара (число) или 'Отмена' для возврата к прошлому меню:",
            reply_markup=get_cancel_keyboard()
        )


# --- Ввод ID магазина (с возможностью отмены) ---
@router.message(AdminStates.adding_product_shop)
async def process_product_shop(message: Message, state: FSMContext):
    """Обработка ввода ID магазина с возможностью отмены"""
    if message.text.strip().lower() == 'отмена':
        await message.answer(
            "❌ Добавление товара отменено.",
            reply_markup=get_products_management_keyboard()
        )
        await state.clear()
        return

    try:
        shop_id = int(message.text.strip())
        shop = await database.get_shop_by_id(shop_id)

        if not shop:
            await message.answer(
                "❌ Магазин не найден. Попробуйте снова или нажмите 'Отмена':",
                reply_markup=get_cancel_keyboard()
            )
            return

        await state.update_data(shop_id=shop_id)

        categories = await database.get_all_categories()
        text = "<b>Доступные категории:</b>\n"
        for category in categories:
            text += f"{category.id}. {category.name}\n"

        text += "\nВведите номер категории из списка или нажмите 'Отмена' для возврата к прошлому меню:"

        await message.answer(
            text,
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(AdminStates.adding_product_category)

    except ValueError:
        await message.answer(
            "❌ Введите корректный номер магазина (число) или 'Отмена' для возврата к прошлому меню:",
            reply_markup=get_cancel_keyboard()
        )


# --- Ввод ID категории (с возможностью отмены) ---
@router.message(AdminStates.adding_product_category)
async def process_product_category(message: Message, state: FSMContext):
    """Обработка ввода ID категории с возможностью отмены"""
    if message.text.strip().lower() == 'отмена':
        await message.answer(
            "❌ Добавление товара отменено.",
            reply_markup=get_products_management_keyboard()
        )
        await state.clear()
        return

    try:
        category_id = int(message.text.strip())
        category = await database.get_category_by_id(category_id)

        if not category:
            await message.answer(
                "❌ Категория не найдена. Попробуйте снова или нажмите 'Отмена':",
                reply_markup=get_cancel_keyboard()
            )
            return

        await state.update_data(category_id=category_id)
        await message.answer(
            "Введите название товара или нажмите 'Отмена' для возврата к прошлому меню:",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(AdminStates.adding_product_name)

    except ValueError:
        await message.answer(
            "❌ Введите корректный номер категории (число) или 'Отмена':",
            reply_markup=get_cancel_keyboard()
        )


# --- Ввод названия ---
@router.message(AdminStates.adding_product_name)
async def process_product_name(message: Message, state: FSMContext):
    """Обработка ввода названия товара"""
    if message.text.strip().lower() == 'отмена':
        await message.answer(
            "❌ Добавление товара отменено.",
            reply_markup=get_products_management_keyboard()
        )
        await state.clear()
        return

    name = message.text.strip()
    await state.update_data(product_name=name)
    await message.answer(
        "Введите описание товара или нажмите 'Отмена' для возврата к прошлому меню:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.adding_product_description)


# --- Ввод описания ---
@router.message(AdminStates.adding_product_description)
async def process_product_description(message: Message, state: FSMContext):
    """Обработка ввода описания товара"""
    if message.text.strip().lower() == 'отмена':
        await message.answer(
            "❌ Добавление товара отменено.",
            reply_markup=get_products_management_keyboard()
        )
        await state.clear()
        return

    description = message.text.strip()
    await state.update_data(product_description=description)

    # ТЕПЕРЬ СПРАШИВАЕМ ВАЛЮТУ ПЕРЕД ЦЕНОЙ - ЭТО ГЛАВНОЕ ИЗМЕНЕНИЕ!
    await message.answer(
        "Выберите валюту цены товара:\n"
        "USD - Доллар США\n"
        "EUR - Евро\n"
        "CNY - Китайский юань\n"
        "JPY - Японская йена\n\n"
        "Введите код валюты (USD, EUR, CNY, JPY) или нажмите 'Отмена':",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.adding_product_currency)


# --- Ввод валюты ---
@router.message(AdminStates.adding_product_currency)
async def process_product_currency(message: Message, state: FSMContext):
    """Обработка ввода валюты"""
    if message.text.strip().lower() == 'отмена':
        await message.answer(
            "❌ Добавление товара отменено.",
            reply_markup=get_products_management_keyboard()
        )
        await state.clear()
        return

    currency = message.text.strip().upper()
    if currency not in ['USD', 'EUR', 'CNY', 'JPY']:
        await message.answer(
            "❌ Неверная валюта. Введите один из кодов: USD, EUR, CNY, JPY\n"
            "Или нажмите 'Отмена':",
            reply_markup=get_cancel_keyboard()
        )
        return

    await state.update_data(product_currency=currency)

    # ТЕПЕРЬ, КОГДА ВАЛЮТА ИЗВЕСТНА, ЗАПРАШИВАЕМ ЦЕНУ
    await message.answer(
        f"Введите цену товара в {currency} (число):\n\n"
        "Пример: 99.99\n"
        "Или нажмите 'Отмена':",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.adding_product_price)


# --- Ввод цены ---
@router.message(AdminStates.adding_product_price)
async def process_product_price(message: Message, state: FSMContext):
    """Обработка ввода цены товара"""
    if message.text.strip().lower() == 'отмена':
        await message.answer(
            "❌ Добавление товара отменено.",
            reply_markup=get_products_management_keyboard()
        )
        await state.clear()
        return

    try:
        price = float(message.text.strip())
        if price <= 0:
            await message.answer(
                "❌ Цена должна быть положительным числом. Попробуйте снова или нажмите 'Отмена':",
                reply_markup=get_cancel_keyboard()
            )
            return

        await state.update_data(product_price=price)

        # Получаем валюту из состояния для информативного сообщения
        data = await state.get_data()
        currency = data.get('product_currency', '')

        await message.answer(
            f"Введите вес товара в кг (число):\n\n"
            f"Пример: 0.5\n"
            f"Или введите 0, если вес не применим\n\n"
            f"💡 <i>Текущие данные:</i>\n"
            f"💰 Цена: {price} {currency}\n\n"
            f"Или нажмите 'Отмена':",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(AdminStates.adding_product_weight)

    except ValueError:
        await message.answer(
            "❌ Введите корректную цену (число). Пример: 99.99\n"
            "Или нажмите 'Отмена':",
            reply_markup=get_cancel_keyboard()
        )


# --- Ввод веса ---
@router.message(AdminStates.adding_product_weight)
async def process_product_weight(message: Message, state: FSMContext):
    """Обработка ввода веса товара"""
    if message.text.strip().lower() == 'отмена':
        await message.answer(
            "❌ Добавление товара отменено.",
            reply_markup=get_products_management_keyboard()
        )
        await state.clear()
        return

    try:
        weight = float(message.text.strip())
        await state.update_data(product_weight=weight if weight > 0 else None)

        # Показываем сводку данных перед сохранением
        data = await state.get_data()

        shop = await database.get_shop_by_id(data['shop_id'])
        category = await database.get_category_by_id(data['category_id'])

        summary_text = (
            "📋 <b>Проверьте данные товара:</b>\n\n"
            f"🏪 <b>Магазин:</b> {shop.name if shop else 'N/A'}\n"
            f"📁 <b>Категория:</b> {category.name if category else 'N/A'}\n"
            f"📝 <b>Название:</b> {data['product_name']}\n"
            f"📄 <b>Описание:</b> {data['product_description']}\n"
            f"💰 <b>Цена:</b> {data['product_price']} {data['product_currency']}\n"
            f"⚖️ <b>Вес:</b> {data.get('product_weight', 'не указан')} кг\n\n"
            "Всё верно? Отправьте фото товара или напишите 'пропустить' для сохранения без фото:"
        )

        await message.answer(summary_text, reply_markup=get_cancel_keyboard())
        await state.set_state(AdminStates.adding_product_photo)

    except ValueError:
        await message.answer(
            "❌ Введите корректный вес (число). Пример: 0.5\n"
            "Или нажмите 'Отмена':",
            reply_markup=get_cancel_keyboard()
        )


# --- Ввод фото ---
@router.message(AdminStates.adding_product_photo, F.photo)
async def process_product_photo(message: Message, state: FSMContext):
    """Обработка фото товара"""
    photo_file_id = message.photo[-1].file_id
    await state.update_data(product_photo_file_id=photo_file_id)
    await save_product(message, state)


@router.message(AdminStates.adding_product_photo, F.text)
async def process_product_no_photo(message: Message, state: FSMContext):
    """Обработка пропуска фото"""
    if message.text.strip().lower() == 'пропустить':
        await state.update_data(product_photo_file_id=None)
        await save_product(message, state)
    elif message.text.strip().lower() == 'отмена':
        await message.answer(
            "❌ Добавление товара отменено.",
            reply_markup=get_products_management_keyboard()
        )
        await state.clear()
    else:
        await message.answer(
            "Отправьте фото, напишите 'пропустить' или 'отмена':",
            reply_markup=get_cancel_keyboard()
        )


# --- Сохранение товара ---
async def save_product(message: Message, state: FSMContext):
    """Сохранение товара в базу данных"""
    data = await state.get_data()

    try:
        product = await database.add_product(
            shop_id=data['shop_id'],
            category_id=data['category_id'],
            name=data['product_name'],
            description=data['product_description'],
            price_original=data['product_price'],
            currency=data['product_currency'],
            weight=data.get('product_weight'),
            photo_file_id=data.get('product_photo_file_id')
        )

        await message.answer(
            f"✅ Товар '{product.name}' успешно добавлен!\n\n"
            f"ID: {product.id}\n"
            f"Цена: {product.price_original} {product.currency}",
            reply_markup=get_admin_menu()
        )
        await state.clear()

    except Exception as e:
        await message.answer(
            f"❌ Ошибка при добавлении товара: {str(e)}",
            reply_markup=get_admin_menu()
        )
        await state.clear()


# --- Навигация назад в управлении товарами ---
@router.callback_query(F.data == "back_to_products_management")
async def back_to_products_management(callback: CallbackQuery, state: FSMContext):
    """Возврат в меню управления товарами"""
    await state.clear()
    await callback.message.edit_text(
        "📦 <b>Управление товарами</b>\n\n"
        "Выберите действие:",
        reply_markup=get_products_management_keyboard()
    )
    await callback.answer()


# --- Отмена операции через кнопку ---
@router.callback_query(F.data == "cancel_operation")
async def cancel_operation(callback: CallbackQuery, state: FSMContext):
    """Отмена текущей операции"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Операция отменена.",
        reply_markup=get_products_management_keyboard()
    )
    await callback.answer()


# --- Просмотр деталей заказа админом ---
@router.callback_query(F.data.startswith("admin_order_"))
async def show_admin_order_details(callback: CallbackQuery):
    """Показать детали заказа для админа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return

    order_id = int(callback.data.split("_")[2])
    order = await database.get_order_by_id(order_id)

    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    # Получаем клиента
    client = await database.get_client_by_id(order.client_id)

    # Получаем товары заказа
    order_items = await database.get_order_items(order.id)

    # Формируем текст
    text = (
        f"📦 <b>Заказ #{order.tracking_number}</b>\n\n"
        f"👤 Клиент: {client.name}\n"
        f"📱 Телефон: {client.phone}\n"
        f"🆔 Telegram: <a href='tg://user?id={client.telegram_id}'>@{client.telegram_id}</a>\n"
        f"📍 Адрес: {client.address}\n\n"
        f"📅 Дата заказа: {order.order_date.strftime('%d.%m.%Y %H:%M')}\n"
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
        reply_markup=get_admin_order_keyboard(order.id),
        disable_web_page_preview=True
    )
    await callback.answer()


# --- Изменение статуса заказа ---
@router.callback_query(F.data.startswith("change_status_"))
async def change_order_status(callback: CallbackQuery):
    """Показать меню выбора статуса"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return

    order_id = int(callback.data.split("_")[2])

    await callback.message.edit_text(
        "📝 <b>Выберите новый статус заказа:</b>",
        reply_markup=get_status_keyboard(order_id)
    )
    await callback.answer()


# --- Установка статуса ---
@router.callback_query(F.data.startswith("set_status_"))
async def set_order_status(callback: CallbackQuery):
    """Установить новый статус заказа"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return

    parts = callback.data.split("_", 3)
    order_id = int(parts[2])
    new_status = parts[3]

    order = await database.get_order_by_id(order_id)
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    # Обновляем статус
    await database.update_order_status(order_id, new_status)

    # Уведомляем клиента
    client = await database.get_client_by_id(order.client_id)
    try:
        await callback.bot.send_message(
            client.telegram_id,
            f"📦 <b>Обновление статуса заказа</b>\n\n"
            f"Заказ #{order.tracking_number}\n"
            f"Новый статус: {new_status}"
        )
    except Exception as e:
        pass  # Игнорируем ошибки отправки

    await callback.answer(f"✅ Статус изменен на: {new_status}")

    # Обновляем информацию о заказе
    order = await database.get_order_by_id(order_id)
    client = await database.get_client_by_id(order.client_id)
    order_items = await database.get_order_items(order.id)

    text = (
        f"📦 <b>Заказ #{order.tracking_number}</b>\n\n"
        f"👤 Клиент: {client.name}\n"
        f"📱 Телефон: {client.phone}\n"
        f"🆔 Telegram: <a href='tg://user?id={client.telegram_id}'>@{client.telegram_id}</a>\n"
        f"📍 Адрес: {client.address}\n\n"
        f"📅 Дата заказа: {order.order_date.strftime('%d.%m.%Y %H:%M')}\n"
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
        reply_markup=get_admin_order_keyboard(order.id),
        disable_web_page_preview=True
    )


# --- Управление курсами валют ---
@router.message(F.text == "💱 Курсы валют")
async def manage_exchange_rates(message: Message, state: FSMContext):
    """Управление курсами валют"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав доступа.")
        return

    # Показываем текущие курсы
    text = "💱 <b>Текущие курсы валют:</b>\n\n"
    for currency in ['USD', 'EUR', 'CNY', 'JPY']:
        rate = await database.get_exchange_rate(currency)
        if rate:
            text += f"{currency}: {rate.rate_to_rub} ₽\n"
        else:
            text += f"{currency}: не установлен\n"

    text += "\nВведите валюту для изменения (USD, EUR, CNY, JPY):"

    await message.answer(text)
    await state.set_state(AdminStates.setting_exchange_rate_currency)


# --- Ввод валюты для курса ---
@router.message(AdminStates.setting_exchange_rate_currency)
async def process_exchange_rate_currency(message: Message, state: FSMContext):
    """Обработка ввода валюты"""
    currency = message.text.strip().upper()
    if currency not in ['USD', 'EUR', 'CNY', 'JPY']:
        await message.answer("❌ Введите корректную валюту (USD, EUR, CNY, JPY):")
        return

    await state.update_data(exchange_currency=currency)
    await message.answer(f"Введите новый курс для {currency} (в рублях):")
    await state.set_state(AdminStates.setting_exchange_rate_value)


# --- Ввод курса ---
@router.message(AdminStates.setting_exchange_rate_value)
async def process_exchange_rate_value(message: Message, state: FSMContext):
    """Обработка ввода курса"""
    try:
        rate = float(message.text.strip())
        data = await state.get_data()
        currency = data['exchange_currency']

        await database.set_exchange_rate(currency, rate)

        await message.answer(
            f"✅ Курс {currency} установлен: {rate} ₽",
            reply_markup=get_admin_menu()
        )
        await state.clear()

    except ValueError:
        await message.answer("❌ Введите корректный курс (число):")


# --- Рассылка (главное меню) ---
@router.message(F.text == "📢 Рассылка")
async def broadcast_menu(message: Message, state: FSMContext):
    """Меню рассылки"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав доступа.")
        return

    await message.answer(
        "📢 <b>Рассылка сообщений</b>\n\n"
        "Отправьте сообщение для рассылки всем пользователям:\n"
        "- Текст\n"
        "- Фото с текстом\n"
        "- Документ с текстом\n\n"
        "Или нажмите 'Отмена' для возврата:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.broadcast_message)


# --- Обработка сообщения для рассылки ---
@router.message(AdminStates.broadcast_message, F.text | F.photo | F.document)
async def process_broadcast_message(message: Message, state: FSMContext):
    """Обработка сообщения для рассылки"""
    if message.text and message.text.strip().lower() == 'отмена':
        await message.answer(
            "❌ Рассылка отменена.",
            reply_markup=get_admin_menu()
        )
        await state.clear()
        return

    # Сохраняем данные сообщения
    broadcast_data = {
        'message_type': 'text',
        'content': None,
        'caption': None,
        'file_id': None
    }

    if message.text:
        broadcast_data['content'] = message.text
        broadcast_data['message_type'] = 'text'
    elif message.photo:
        broadcast_data['file_id'] = message.photo[-1].file_id
        broadcast_data['message_type'] = 'photo'
        broadcast_data['caption'] = message.caption
    elif message.document:
        broadcast_data['file_id'] = message.document.file_id
        broadcast_data['message_type'] = 'document'
        broadcast_data['caption'] = message.caption
        broadcast_data['file_name'] = message.document.file_name

    await state.update_data(broadcast_data=broadcast_data)

    # Получаем количество пользователей
    clients = await database.get_all_clients()
    user_count = len(clients)

    # Показываем предпросмотр и запрашиваем подтверждение
    preview_text = "📢 <b>Предпросмотр рассылки:</b>\n\n"

    if broadcast_data['message_type'] == 'text':
        preview_text += broadcast_data['content']
    elif broadcast_data['message_type'] == 'photo':
        preview_text += "🖼️ <b>Фото с подписью:</b>\n"
        if broadcast_data['caption']:
            preview_text += broadcast_data['caption']
        else:
            preview_text += "(без подписи)"
    elif broadcast_data['message_type'] == 'document':
        preview_text += f"📎 <b>Документ:</b> {broadcast_data.get('file_name', 'файл')}\n"
        if broadcast_data['caption']:
            preview_text += f"Подпись: {broadcast_data['caption']}"

    preview_text += f"\n\n👥 <b>Будет отправлено:</b> {user_count} пользователям"

    # Создаем клавиатуру подтверждения
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    confirmation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Начать рассылку", callback_data="confirm_broadcast"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_broadcast")
        ]
    ])

    if broadcast_data['message_type'] == 'text':
        await message.answer(
            preview_text,
            reply_markup=confirmation_keyboard
        )
    elif broadcast_data['message_type'] == 'photo':
        await message.answer_photo(
            photo=broadcast_data['file_id'],
            caption=preview_text,
            reply_markup=confirmation_keyboard
        )
    elif broadcast_data['message_type'] == 'document':
        await message.answer_document(
            document=broadcast_data['file_id'],
            caption=preview_text,
            reply_markup=confirmation_keyboard
        )

    await state.set_state(AdminStates.broadcast_confirmation)


# --- Подтверждение рассылки ---
@router.callback_query(AdminStates.broadcast_confirmation, F.data == "confirm_broadcast")
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и запуск рассылки"""
    data = await state.get_data()
    broadcast_data = data['broadcast_data']

    # Получаем всех клиентов
    clients = await database.get_all_clients()
    total_users = len(clients)

    if total_users == 0:
        await callback.message.edit_text(
            "❌ Нет пользователей для рассылки.",
            reply_markup=get_admin_menu()
        )
        await state.clear()
        return

    # Отправляем сообщение о начале рассылки
    progress_message = await callback.message.answer(
        f"📢 <b>Начата рассылка</b>\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"✅ Отправлено: 0/{total_users}\n"
        f"❌ Ошибок: 0\n\n"
        f"⏳ Ожидайте завершения..."
    )

    success_count = 0
    error_count = 0

    # Рассылаем сообщение
    for i, client in enumerate(clients, 1):
        try:
            if broadcast_data['message_type'] == 'text':
                await callback.bot.send_message(
                    chat_id=client.telegram_id,
                    text=broadcast_data['content']
                )
            elif broadcast_data['message_type'] == 'photo':
                await callback.bot.send_photo(
                    chat_id=client.telegram_id,
                    photo=broadcast_data['file_id'],
                    caption=broadcast_data.get('caption')
                )
            elif broadcast_data['message_type'] == 'document':
                await callback.bot.send_document(
                    chat_id=client.telegram_id,
                    document=broadcast_data['file_id'],
                    caption=broadcast_data.get('caption')
                )

            success_count += 1

            # Обновляем прогресс каждые 10 сообщений или для последнего сообщения
            if i % 10 == 0 or i == total_users:
                await progress_message.edit_text(
                    f"📢 <b>Рассылка в процессе</b>\n\n"
                    f"👥 Всего пользователей: {total_users}\n"
                    f"✅ Отправлено: {i}/{total_users}\n"
                    f"❌ Ошибок: {error_count}\n\n"
                    f"⏳ Прогресс: {i / total_users * 100:.1f}%"
                )

        except Exception as e:
            error_count += 1
            continue

        # Небольшая задержка чтобы не превысить лимиты Telegram
        import asyncio
        await asyncio.sleep(0.1)

    # Финальное сообщение о результатах
    await progress_message.edit_text(
        f"📢 <b>Рассылка завершена!</b>\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"✅ Успешно отправлено: {success_count}\n"
        f"❌ Ошибок: {error_count}\n"
        f"📊 Эффективность: {success_count / total_users * 100:.1f}%"
    )

    await callback.message.answer(
        "🔑 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu()
    )

    await state.clear()
    await callback.answer()


# --- Отмена рассылки ---
@router.callback_query(AdminStates.broadcast_confirmation, F.data == "cancel_broadcast")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    """Отмена рассылки"""
    await callback.message.edit_text(
        "❌ Рассылка отменена.",
        reply_markup=get_admin_menu()
    )
    await state.clear()
    await callback.answer()


# --- Обработка отмены через текст ---
@router.message(AdminStates.broadcast_message)
async def handle_broadcast_cancel(message: Message, state: FSMContext):
    """Обработка отмены рассылки через текст"""
    if message.text and message.text.strip().lower() == 'отмена':
        await message.answer(
            "❌ Рассылка отменена.",
            reply_markup=get_admin_menu()
        )
        await state.clear()
    else:
        await message.answer(
            "Пожалуйста, отправьте текст, фото или документ для рассылки, "
            "или напишите 'Отмена' для возврата:",
            reply_markup=get_cancel_keyboard()
        )


# --- Навигация назад ---
@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery, state: FSMContext):
    """Возврат в админ-панель"""
    await state.clear()
    # Удаляем предыдущее сообщение и отправляем новое с правильной клавиатурой
    await callback.message.delete()
    await callback.message.answer(
        "🔑 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu()  # ReplyKeyboardMarkup для обычных сообщений
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_admin_orders")
async def back_to_admin_orders(callback: CallbackQuery):
    """Возврат к списку заказов"""
    orders = await database.get_all_orders()

    if not orders:
        await callback.message.edit_text("📦 Заказов пока нет.")
        await callback.answer()
        return

    await callback.message.edit_text(
        f"📊 <b>Все заказы ({len(orders)}):</b>\n\n"
        "Выберите заказ для просмотра и управления:",
        reply_markup=get_admin_orders_keyboard(orders)
    )
    await callback.answer()
