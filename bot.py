# --- Импорты стандартных и сторонних библиотек ---
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# --- Импорты собственных модулей ---
from config import BOT_TOKEN, ADMIN_IDS
from database import init_db, close_db
from utils import setup_logging

# --- Импорт роутеров ---
from handlers import registration, catalog, cart, orders, profile, admin


# --- Основная функция ---
async def main():
    """Основная функция запуска бота"""

    # --- Настройка логирования ---
    setup_logging()
    logger = logging.getLogger(__name__)

    # --- Инициализация бота и диспетчера ---
    bot = Bot(
        token=BOT_TOKEN,
        parse_mode=ParseMode.HTML
    )
    await bot.set_my_commands([])  # Удаление бокового меню

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # --- Регистрация роутеров ---
    dp.include_router(registration.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(orders.router)
    dp.include_router(profile.router)
    dp.include_router(admin.router)

    try:
        # --- Инициализация базы данных ---
        logger.info("Инициализация базы данных...")
        await init_db()
        logger.info("База данных инициализирована успешно")

        # --- Уведомление администраторов ---
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    "🤖 Бот OverseasShop запущен и готов к работе!"
                )
            except Exception as e:
                logger.warning(f"Не удалось отправить уведомление админу {admin_id}: {e}")

        logger.info("Бот запущен и готов к работе!")

        # --- Запуск поллинга ---
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

    finally:
        # --- Закрытие соединения с базой данных ---
        await close_db()
        logger.info("Соединение с базой данных закрыто")


# --- Точка входа ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
