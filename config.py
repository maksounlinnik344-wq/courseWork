# --- Импорты ---
import os
from dotenv import load_dotenv
from typing import List

# --- Загрузка переменных окружения ---
load_dotenv()

# --- Основные настройки бота ---
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не указан в .env файле!")

# ID администраторов (через запятую)
ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')
ADMIN_IDS: List[int] = []

if ADMIN_IDS_STR:
    try:
        ADMIN_IDS = [
            int(admin_id.strip())
            for admin_id in ADMIN_IDS_STR.split(',')
            if admin_id.strip()
        ]
    except ValueError:
        raise ValueError("❌ Неверный формат ADMIN_IDS! Используйте числа через запятую.")

if not ADMIN_IDS:
    raise ValueError("❌ ADMIN_IDS не указаны! Укажите ID администраторов.")

# === DADATA API НАСТРОЙКИ ===
DADATA_TOKEN = os.getenv('DADATA_TOKEN', '')
DADATA_SECRET = os.getenv('DADATA_SECRET', '')

# Проверяем наличие Dadata токенов (не обязательно, но желательно)
if not DADATA_TOKEN or not DADATA_SECRET:
    print("⚠️  Dadata токены не указаны. Функция умных подсказок адресов будет отключена.")
    print("💡 Для включения: зарегистрируйтесь на dadata.ru и укажите DADATA_TOKEN и DADATA_SECRET в .env")
else:
    print("✅ Dadata токены найдены. Умные подсказки адресов активны.")

# --- Настройки базы данных ---
# Используем DATABASE_URL из .env или создаем из PostgreSQL настроек
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    # Если DATABASE_URL не указан, создаем из PostgreSQL настроек
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'overseasshop_db')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')

    DATABASE_URL = (
        f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    print("ℹ️  Используется PostgreSQL база данных")
else:
    print(f"ℹ️  Используется база данных из DATABASE_URL: {DATABASE_URL.split('://')[0]}")

# --- Настройки логирования ---
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# --- Настройки доставки ---
DELIVERY_TYPES = {
    'эконом': {'days': '20-30', 'multiplier': 1.0},
    'стандарт': {'days': '10-15', 'multiplier': 1.5},
    'экспресс': {'days': '5-7', 'multiplier': 2.5}
}

# --- Таможенный сбор (процент от суммы заказа) ---
CUSTOMS_FEE_PERCENT = 0.15  # 15%


# --- Информация о конфигурации ---
def print_config_info():
    """Вывод информации о конфигурации"""
    print("\n=== КОНФИГУРАЦИЯ БОТА ===")
    print(f"🤖 Бот: {'✅ Настроен' if BOT_TOKEN else '❌ Не настроен'}")
    print(f"👑 Админы: {len(ADMIN_IDS)} пользователей")
    print(f"🗺️  Dadata: {'✅ Включен' if DADATA_TOKEN and DADATA_SECRET else '❌ Выключен'}")
    print(f"🗄️  База данных: {DATABASE_URL.split('://')[0]}")
    print("========================\n")


# Автоматически выводим информацию при импорте
if __name__ != "__main__":
    print_config_info()