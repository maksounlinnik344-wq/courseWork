# --- Импорты ---
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List


# --- Основное меню ---
def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🛍️ Каталог товаров"),
        KeyboardButton(text="🛒 Корзина")
    )
    builder.row(
        KeyboardButton(text="📦 Мои заказы"),
        KeyboardButton(text="👤 Профиль")
    )
    if is_admin:
        builder.row(KeyboardButton(text="🔑 Админ-панель"))
    builder.row(KeyboardButton(text="ℹ️ О боте"))
    return builder.as_markup(resize_keyboard=True)


# --- Скрытая клавиатура ---
def get_hidden_keyboard() -> ReplyKeyboardMarkup:
    """Скрытая клавиатура"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="📋 Меню"))
    return builder.as_markup(resize_keyboard=True)


# --- Клавиатура для ввода телефона ---
def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для ввода номера телефона"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="📱 Поделиться номером", request_contact=True))
    builder.row(KeyboardButton(text="✍️ Ввести вручную"))
    return builder.as_markup(resize_keyboard=True)


# --- Админ-панель ---
def get_admin_menu() -> ReplyKeyboardMarkup:
    """Меню админ-панели"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📊 Все заказы"),
        KeyboardButton(text="📦 Управление товарами")
    )
    builder.row(
        KeyboardButton(text="💱 Курсы валют"),
        KeyboardButton(text="📢 Рассылка")
    )
    builder.row(KeyboardButton(text="🔙 Назад в меню"))
    return builder.as_markup(resize_keyboard=True)


# --- Инлайн-клавиатура для стран ---
def get_countries_keyboard(countries: List) -> InlineKeyboardMarkup:
    """Клавиатура выбора страны"""
    builder = InlineKeyboardBuilder()
    for country in countries:
        builder.row(
            InlineKeyboardButton(
                text=f"{country.flag_emoji} {country.name}",
                callback_data=f"country_{country.id}"
            )
        )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu"))
    return builder.as_markup()


# --- Инлайн-клавиатура для магазинов ---
def get_shops_keyboard(shops: List, country_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора магазина"""
    builder = InlineKeyboardBuilder()
    for shop in shops:
        builder.row(
            InlineKeyboardButton(
                text=f"🏪 {shop.name}",
                callback_data=f"shop_{shop.id}"
            )
        )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_countries"))
    return builder.as_markup()


# --- Инлайн-клавиатура для категорий ---
def get_categories_keyboard(shop_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора категории"""
    builder = InlineKeyboardBuilder()
    categories = [
        ("👕 Одежда", "category_1"),
        ("👟 Обувь", "category_2"),
        ("💻 Электроника", "category_3"),
        ("🎮 Игры и игрушки", "category_4"),
        ("📚 Книги", "category_5"),
        ("🏠 Для дома", "category_6")
    ]
    for name, callback in categories:
        builder.row(
            InlineKeyboardButton(
                text=name,
                callback_data=f"{callback}_shop_{shop_id}"
            )
        )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_shops"))
    return builder.as_markup()


# --- Инлайн-клавиатура для товаров ---
def get_products_keyboard(products: List, page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Клавиатура списка товаров с пагинацией"""
    builder = InlineKeyboardBuilder()

    for product in products:
        builder.row(
            InlineKeyboardButton(
                text=f"🛍️ {product.name}",
                callback_data=f"product_{product.id}"
            )
        )

    # Пагинация
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{page - 1}")
        )
    if page < total_pages - 1:
        pagination_buttons.append(
            InlineKeyboardButton(text="Вперед ➡️", callback_data=f"page_{page + 1}")
        )
    if pagination_buttons:
        builder.row(*pagination_buttons)

    builder.row(InlineKeyboardButton(text="🔙 К категориям", callback_data="back_to_categories"))
    return builder.as_markup()


# --- Инлайн-клавиатура для товара ---
def get_product_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для просмотра товара"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🛒 Добавить в корзину",
            callback_data=f"add_to_cart_{product_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="🔙 К товарам", callback_data="back_to_products")
    )
    return builder.as_markup()


# --- Инлайн-клавиатура для корзины ---
def get_cart_keyboard(cart_items: List) -> InlineKeyboardMarkup:
    """Клавиатура корзины"""
    builder = InlineKeyboardBuilder()

    for cart_item, product in cart_items:
        builder.row(
            InlineKeyboardButton(
                text=f"❌ {product.name} (x{cart_item.quantity})",
                callback_data=f"remove_from_cart_{product.id}"
            )
        )

    if cart_items:
        builder.row(
            InlineKeyboardButton(
                text="✅ Оформить заказ",
                callback_data="checkout"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🗑️ Очистить корзину",
                callback_data="clear_cart"
            )
        )

    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu"))
    return builder.as_markup()


# --- Инлайн-клавиатура для выбора типа доставки ---
def get_delivery_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа доставки"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🐌 Эконом (20-30 дней)",
            callback_data="delivery_эконом"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📦 Стандарт (10-15 дней)",
            callback_data="delivery_стандарт"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🚀 Экспресс (5-7 дней)",
            callback_data="delivery_экспресс"
        )
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_cart"))
    return builder.as_markup()


# --- Инлайн-клавиатура для подтверждения заказа ---
def get_order_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения заказа"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_checkout")
    )
    return builder.as_markup()


# --- Инлайн-клавиатура для заказов ---
def get_orders_keyboard(orders: List) -> InlineKeyboardMarkup:
    """Клавиатура списка заказов"""
    builder = InlineKeyboardBuilder()

    for order in orders:
        builder.row(
            InlineKeyboardButton(
                text=f"📦 {order.tracking_number} - {order.status}",
                callback_data=f"order_{order.id}"
            )
        )

    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu"))
    return builder.as_markup()


# --- Инлайн-клавиатура для заказа ---
def get_order_keyboard(order_id: int, can_cancel: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура просмотра заказа"""
    builder = InlineKeyboardBuilder()

    if can_cancel:
        builder.row(
            InlineKeyboardButton(
                text="❌ Отменить заказ",
                callback_data=f"cancel_order_{order_id}"
            )
        )

    builder.row(InlineKeyboardButton(text="🔙 К заказам", callback_data="back_to_orders"))
    return builder.as_markup()


# --- Инлайн-клавиатура для админ-заказов ---
def get_admin_orders_keyboard(orders: List) -> InlineKeyboardMarkup:
    """Клавиатура списка заказов для админа"""
    builder = InlineKeyboardBuilder()

    for order in orders[:10]:  # Показываем только первые 10
        builder.row(
            InlineKeyboardButton(
                text=f"📦 {order.tracking_number} - {order.status}",
                callback_data=f"admin_order_{order.id}"
            )
        )

    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin"))
    return builder.as_markup()


# --- Инлайн-клавиатура для управления заказом админом ---
def get_admin_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Клавиатура управления заказом для админа"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📝 Изменить статус",
            callback_data=f"change_status_{order_id}"
        )
    )
    builder.row(InlineKeyboardButton(text="🔙 К заказам", callback_data="back_to_admin_orders"))
    return builder.as_markup()


# --- Инлайн-клавиатура для выбора статуса ---
def get_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора статуса заказа"""
    builder = InlineKeyboardBuilder()
    statuses = [
        '📦 Обработка',
        '🛃 Упаковка',
        '✈️ В пути',
        '🚚 На таможне',
        '📮 Вручение',
        '✅ Получен'
    ]
    for status in statuses:
        builder.row(
            InlineKeyboardButton(
                text=status,
                callback_data=f"set_status_{order_id}_{status}"
            )
        )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_order_{order_id}"))
    return builder.as_markup()


# --- Инлайн-клавиатура для управления товарами ---
def get_products_management_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления товарами для админа"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📥 Добавить товар", callback_data="add_product")
    )
    builder.row(
        InlineKeyboardButton(text="👁️ Просмотреть все товары", callback_data="view_products")
    )
    builder.row(
        InlineKeyboardButton(text="🗑️ Удалить товар", callback_data="delete_product")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад в админ-панель", callback_data="back_to_admin")
    )
    return builder.as_markup()


# --- Инлайн-клавиатура для отмены операций ---
def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для отмены операций"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_operation")
    )
    return builder.as_markup()


# --- Клавиатура для выбора имени из Telegram ---
def get_name_keyboard(first_name: str = None, last_name: str = None) -> ReplyKeyboardMarkup:
    """Клавиатура для выбора имени из Telegram"""
    builder = ReplyKeyboardBuilder()

    if first_name and last_name:
        full_name = f"{first_name} {last_name}".strip()
        builder.row(KeyboardButton(text=full_name))
    elif first_name:
        builder.row(KeyboardButton(text=first_name))

    builder.row(KeyboardButton(text="✍️ Ввести другое имя"))
    builder.row(KeyboardButton(text="❌ Отменить регистрацию"))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


# --- Клавиатура только для регистрации (без меню) ---
def get_registration_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура только с кнопкой отмены для процесса регистрации"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Отменить регистрацию"))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


# --- Клавиатура для редактирования профиля ---
def get_profile_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура управления профилем"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="✏️ Изменить имя"),
        KeyboardButton(text="📱 Изменить телефон")
    )
    builder.row(
        KeyboardButton(text="📍 Изменить адрес"),
        KeyboardButton(text="📋 Главное меню")
    )
    return builder.as_markup(resize_keyboard=True)


# --- Клавиатура для отмены редактирования ---
def get_cancel_edit_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для отмены редактирования"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Отменить редактирование"))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


# === НОВЫЕ КЛАВИАТУРЫ ДЛЯ DADATA ===

# --- Клавиатура для ввода адреса ---
def get_address_input_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для ввода адреса с Dadata"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Отменить регистрацию"))
    return builder.as_markup(resize_keyboard=True)


# --- Инлайн-клавиатура для выбора адреса из подсказок Dadata ---
def get_address_suggestions_keyboard(suggestions: list) -> InlineKeyboardMarkup:
    """Клавиатура с номерами адресов"""
    builder = InlineKeyboardBuilder()

    # Создаем кнопки с номерами
    buttons = []
    for i in range(len(suggestions)):
        buttons.append(InlineKeyboardButton(
            text=f"📍 {i + 1}",
            callback_data=f"select_address_{i}"
        ))

    # Распределяем кнопки по 3 в ряд
    for i in range(0, len(buttons), 3):
        builder.row(*buttons[i:i + 3])

    builder.row(InlineKeyboardButton(
        text="✍️ Ввести адрес вручную",
        callback_data="enter_address_manual"
    ))

    return builder.as_markup()


# --- Клавиатура для подтверждения адреса ---
def get_address_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения выбранного адреса"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, верно", callback_data="confirm_address"),
        InlineKeyboardButton(text="✏️ Ввести другой адрес", callback_data="enter_new_address")
    )
    return builder.as_markup()

def get_restart_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для перезапуска после отмены"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Начать заново")],
            [KeyboardButton(text="❌ Выйти")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
