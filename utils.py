# --- Импорты ---
import logging
import re
from aiogram.fsm.state import State, StatesGroup
from config import LOG_LEVEL


# --- Настройка логирования ---
def setup_logging():
    """Настройка системы логирования"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


# --- Состояния FSM: Регистрация ---
class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    # Новые состояния для Dadata
    waiting_for_address_input = State()  # Пользователь вводит адрес
    waiting_for_address_selection = State()  # Пользователь выбирает из подсказок Dadata
    waiting_for_address_confirmation = State()  # Подтверждение выбранного адреса


# --- Состояния FSM: Каталог ---
class CatalogStates(StatesGroup):
    browsing_countries = State()
    browsing_shops = State()
    browsing_categories = State()
    browsing_products = State()
    viewing_product = State()


# --- Состояния FSM: Корзина ---
class CartStates(StatesGroup):
    viewing_cart = State()
    selecting_quantity = State()
    selecting_delivery = State()
    confirming_order = State()


# --- Состояния FSM: Админ ---
class AdminStates(StatesGroup):
    # Управление товарами
    adding_product_shop = State()
    adding_product_category = State()
    adding_product_name = State()
    adding_product_description = State()
    adding_product_price = State()
    adding_product_currency = State()
    adding_product_weight = State()
    adding_product_photo = State()
    deleting_product = State()

    # Управление заказами
    viewing_orders = State()
    changing_order_status = State()

    # Управление курсами
    setting_exchange_rate_currency = State()
    setting_exchange_rate_value = State()

    # Управление рассылками
    broadcast_message = State()
    broadcast_confirmation = State()


# --- Состояния FSM: Профиль ---
class ProfileStates(StatesGroup):
    changing_name = State()
    changing_phone = State()
    changing_address = State()
    # Новые состояния для редактирования адреса через Dadata
    changing_address_input = State()
    changing_address_selection = State()
    changing_address_confirmation = State()


# --- Валидация телефона ---
def validate_phone(phone: str) -> bool:
    """Валидация номера телефона"""
    clean_phone = re.sub(r'[^\d+]', '', phone)
    patterns = [
        r'^\+7\d{10}$',
        r'^8\d{10}$',
        r'^7\d{10}$',
    ]
    return any(re.match(p, clean_phone) for p in patterns)


def normalize_phone(phone: str) -> str:
    """Нормализация номера телефона к формату +7XXXXXXXXXX"""
    clean_phone = re.sub(r'[^\d+]', '', phone)
    if clean_phone.startswith('+7'):
        return clean_phone
    elif clean_phone.startswith('8'):
        return '+7' + clean_phone[1:]
    elif clean_phone.startswith('7'):
        return '+' + clean_phone
    else:
        return '+' + clean_phone


# --- Валидация адреса (базовая) ---
def validate_address_basic(address: str) -> bool:
    """Базовая валидация адреса"""
    if not address or len(address.strip()) < 10:
        return False

    # Проверяем, что есть хотя бы город и улица
    address_lower = address.lower()
    has_city = any(keyword in address_lower for keyword in ['г.', 'город', 'гор.', 'г '])
    has_street = any(keyword in address_lower for keyword in ['ул.', 'улица', 'ул ', 'проспект', 'пр.'])

    return has_city and has_street


# --- Форматирование адреса из Dadata ---
def format_dadata_address(suggestion_data: dict) -> str:
    """Форматирование адреса из данных Dadata"""
    data = suggestion_data.get('data', {})

    components = []

    # Город
    if data.get('city'):
        components.append(f"г. {data['city']}")
    elif data.get('settlement'):
        components.append(f"{data['settlement']}")

    # Улица
    if data.get('street'):
        street_type = data.get('street_type', 'ул.')
        components.append(f"{street_type} {data['street']}")

    # Дом
    if data.get('house'):
        components.append(f"д. {data['house']}")

    # Квартира
    if data.get('flat'):
        components.append(f"кв. {data['flat']}")

    return ", ".join(components) if components else suggestion_data.get('value', '')


# --- Конвертация валют ---
async def convert_to_rub(amount: float, currency: str, exchange_rates: dict) -> float:
    """Конвертация суммы в рубли"""
    if currency == 'RUB':
        return amount
    rate = exchange_rates.get(currency, 1.0)
    return amount * rate


def format_price(price: float) -> str:
    """Форматирование цены"""
    return f"{price:,.2f}".replace(',', ' ')


# --- Статусы заказов ---
ORDER_STATUSES = [
    '📦 Обработка',
    '🛃 Упаковка',
    '✈️ В пути',
    '🚚 На таможне',
    '📮 Вручение',
    '✅ Получен',
    '❌ Отменен'
]


def get_next_status(current_status: str) -> str:
    """Получить следующий статус заказа"""
    try:
        current_index = ORDER_STATUSES.index(current_status)
        if current_index < len(ORDER_STATUSES) - 2:  # Не включая "Отменен"
            return ORDER_STATUSES[current_index + 1]
        return current_status
    except ValueError:
        return ORDER_STATUSES[0]

