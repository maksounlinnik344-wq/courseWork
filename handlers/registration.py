# --- Импорты ---
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

import database
from config import ADMIN_IDS
from utils import RegistrationStates, validate_phone, normalize_phone, format_dadata_address, validate_address_basic
from keyboards import (
    get_main_menu,
    get_phone_keyboard,
    get_hidden_keyboard,
    get_name_keyboard,
    get_address_input_keyboard,
    get_address_suggestions_keyboard,
    get_address_confirmation_keyboard,
    get_registration_keyboard,
    get_restart_keyboard
)
from services.address_service import address_service

# --- Инициализация роутера ---
router = Router()


# --- Команда /start ---
@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    telegram_id = message.from_user.id

    client = await database.get_client_by_telegram_id(telegram_id)
    is_admin = telegram_id in ADMIN_IDS

    if client:
        await message.answer(
            f"🛍️ Добро пожаловать обратно, {client.name}!\n\n"
            "Выберите действие из меню ниже:",
            reply_markup=get_main_menu(is_admin=is_admin)
        )
    else:
        # Получаем данные из Telegram профиля
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name

        welcome_text = (
            "🌍 Добро пожаловать в OverseasShop! 🌍\n\n"
            "Мы поможем вам заказать товары из-за рубежа!\n\n"
            "⚠️ <b>Внимание:</b> Это учебный проект. Все операции виртуальные.\n\n"
            "Для начала работы нам нужно зарегистрировать вас."
        )

        # Если есть имя в Telegram, предлагаем использовать его
        if first_name:
            welcome_text += f"\n\nМы видим, что в Telegram вас зовут: <b>{first_name}</b>"
            if last_name:
                welcome_text += f" <b>{last_name}</b>"
            welcome_text += "\n\nХотите использовать это имя или ввести другое?"

            await message.answer(
                welcome_text,
                reply_markup=get_name_keyboard(first_name, last_name)
            )
        else:
            welcome_text += "\n\nКак вас зовут?"
            await message.answer(
                welcome_text,
                reply_markup=get_registration_keyboard()
            )

        await state.set_state(RegistrationStates.waiting_for_name)


# --- Регистрация - ввод имени ---
@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка ввода имени с автозаполнением из Telegram"""
    # Обработка отмены регистрации
    if message.text == "❌ Отменить регистрацию":
        await cancel_registration(message, state)
        return

    if message.text == "✍️ Ввести другое имя":
        await message.answer(
            "Хорошо! Как вас зовут?",
            reply_markup=get_registration_keyboard()
        )
        return

    if not message.text or len(message.text.strip()) < 2:
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name

        await message.answer(
            "Пожалуйста, введите корректное имя (минимум 2 символа):",
            reply_markup=get_name_keyboard(first_name, last_name)
        )
        return

    name = message.text.strip()
    # СОХРАНЯЕМ TELEGRAM_ID В СОСТОЯНИИ
    await state.update_data(name=name, telegram_id=message.from_user.id)

    await message.answer(
        f"Приятно познакомиться, {name}! 😊\n\n"
        "Теперь нам нужен ваш номер телефона для связи.\n"
        "Вы можете поделиться им через кнопку или ввести вручную:",
        reply_markup=get_phone_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_phone)


# --- Регистрация - ввод телефона ---
@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_contact(message: Message, state: FSMContext):
    """Обработка контакта (номера телефона)"""
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    await state.update_data(phone=phone)
    await ask_for_address(message, state)


@router.message(RegistrationStates.waiting_for_phone, F.text == "✍️ Ввести вручную")
async def request_manual_phone(message: Message, state: FSMContext):
    """Запрос ручного ввода номера телефона"""
    data = await state.get_data()
    name = data.get("name", "пользователь")

    await message.answer(
        f"{name}, введите ваш номер телефона:",
        reply_markup=get_registration_keyboard()
    )


@router.message(RegistrationStates.waiting_for_phone, F.text)
async def process_manual_phone(message: Message, state: FSMContext):
    """Обработка ручного ввода номера телефона"""
    # Обработка отмены регистрации
    if message.text == "❌ Отменить регистрацию":
        await cancel_registration(message, state)
        return

    phone = message.text.strip()

    if not validate_phone(phone):
        await message.answer(
            "Неверный формат номера телефона! ❌\n\n"
            "Введите номер в формате:\n"
            "+7XXXXXXXXXX или 8XXXXXXXXXX\n\n"
            "Например: +79123456789",
            reply_markup=get_registration_keyboard()
        )
        return

    phone = normalize_phone(phone)
    await state.update_data(phone=phone)
    await ask_for_address(message, state)


# === НОВЫЙ ПРОЦЕСС ВВОДА АДРЕСА С DADATA ===

async def ask_for_address(message: Message, state: FSMContext):
    """Запрос адреса доставки"""
    data = await state.get_data()
    name = data.get("name", "пользователь")

    # Проверяем доступность Dadata
    if address_service.is_available:
        address_text = (
            f"Отлично, {name}! 📱\n\n"
            "Теперь введите ваш адрес доставки в России:\n\n"
            "🔍 <b>Система автоматически найдет ваш адрес!</b>\n\n"
            "Просто введите:\n"
            "• <i>Город, улица, дом</i>\n"
            "• <i>Название города и улицы</i>\n"
            "• <i>Часть адреса</i>\n\n"
            "Примеры:\n"
            "• <i>Москва, Тверская 10</i>\n"
            "• <i>Санкт-Петербург, Невский проспект 25</i>\n"
            "• <i>Екатеринбург, Ленина</i>"
        )
    else:
        # Fallback если Dadata не доступен
        address_text = (
            f"Отлично, {name}! 📱\n\n"
            "Теперь введите ваш адрес доставки:\n\n"
            "Формат: <i>Город, Улица, Дом, Квартира</i>\n"
            "Пример: <i>Москва, ул. Тверская, д. 15, кв. 25</i>"
        )

    await message.answer(
        address_text,
        reply_markup=get_address_input_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_address_input)


@router.message(RegistrationStates.waiting_for_address_input)
async def process_address_input(message: Message, state: FSMContext):
    """Обработка ввода адреса с использованием Dadata"""
    if message.text == "❌ Отменить регистрацию":
        await cancel_registration(message, state)
        return

    address_query = message.text.strip()

    if len(address_query) < 3:
        await message.answer(
            "❌ Слишком короткий запрос.\n\n"
            "Введите адрес более подробно (минимум 3 символа):",
            reply_markup=get_address_input_keyboard()
        )
        return

    # Получаем подсказки от Dadata
    if address_service.is_available:
        suggestions = await address_service.suggest_address(address_query, count=5)

        if suggestions:
            # Сохраняем подсказки в состоянии
            await state.update_data(
                address_suggestions=suggestions,
                original_address_query=address_query
            )

            # Формируем текст сообщения с полными адресами
            address_list_text = "🔍 <b>Найдены подходящие адреса:</b>\n\n"
            for i, suggestion in enumerate(suggestions, 1):
                formatted_address = format_dadata_address(suggestion)
                if not formatted_address:
                    formatted_address = suggestion['value']
                address_list_text += f"{i}. {formatted_address}\n\n"

            address_list_text += "Выберите подходящий вариант:"

            await message.answer(
                address_list_text,
                reply_markup=get_address_suggestions_keyboard(suggestions)
            )
            await state.set_state(RegistrationStates.waiting_for_address_selection)
            return
        else:
            # Если Dadata не нашел подсказок
            await message.answer(
                "❌ Адрес не найден в базе.\n\n"
                "Попробуйте ввести адрес еще раз или введите вручную:",
                reply_markup=get_address_input_keyboard()
            )
            return

    # Если Dadata не доступен - используем ручной ввод
    if not validate_address_basic(address_query):
        await message.answer(
            "❌ Неверный формат адреса!\n\n"
            "Адрес должен содержать город и улицу.\n"
            "Пример: <i>Москва, ул. Тверская, д. 15, кв. 25</i>\n\n"
            "Введите адрес еще раз:",
            reply_markup=get_address_input_keyboard()
        )
        return

    await state.update_data(address=address_query)
    await complete_registration(message, state)


@router.callback_query(RegistrationStates.waiting_for_address_selection, F.data.startswith("select_address_"))
async def process_address_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора адреса из подсказок Dadata"""
    data = await state.get_data()
    suggestions = data.get('address_suggestions', [])

    try:
        address_index = int(callback.data.split('_')[2])
        selected_suggestion = suggestions[address_index]

        # Форматируем адрес для показа пользователю
        formatted_address = format_dadata_address(selected_suggestion)
        if not formatted_address:
            formatted_address = selected_suggestion['value']

        # Сохраняем выбранный адрес
        await state.update_data(
            selected_address=selected_suggestion,
            formatted_address=formatted_address
        )

        await callback.message.edit_text(
            f"📍 <b>Выбранный адрес:</b>\n\n"
            f"{formatted_address}\n\n"
            "Это правильный адрес?",
            reply_markup=get_address_confirmation_keyboard()
        )
        await state.set_state(RegistrationStates.waiting_for_address_confirmation)

    except (IndexError, ValueError):
        await callback.message.edit_text(
            "❌ Ошибка выбора адреса. Попробуйте еще раз.",
            reply_markup=get_address_suggestions_keyboard(suggestions)
        )

    await callback.answer()


@router.callback_query(RegistrationStates.waiting_for_address_selection, F.data == "enter_address_manual")
async def process_manual_address_entry(callback: CallbackQuery, state: FSMContext):
    """Обработка ручного ввода адреса"""
    data = await state.get_data()
    original_query = data.get('original_address_query', '')

    await callback.message.edit_text(
        "✍️ <b>Ручной ввод адреса</b>\n\n"
        f"Вы ввели: <i>{original_query}</i>\n\n"
        "Введите полный адрес вручную:",
    )
    await state.set_state(RegistrationStates.waiting_for_address_input)
    await callback.answer()


@router.callback_query(RegistrationStates.waiting_for_address_confirmation, F.data == "confirm_address")
async def process_address_confirmation(callback: CallbackQuery, state: FSMContext):
    """Подтверждение выбранного адреса"""
    data = await state.get_data()
    formatted_address = data.get('formatted_address', '')

    if not formatted_address:
        await callback.message.edit_text(
            "❌ Ошибка: адрес не найден. Попробуйте еще раз."
        )
        return

    await state.update_data(address=formatted_address)

    # ПРОСТО ВЫЗЫВАЕМ ФУНКЦИЮ ЗАВЕРШЕНИЯ РЕГИСТРАЦИИ
    await complete_registration_callback(callback, state)
    await callback.answer()


@router.callback_query(RegistrationStates.waiting_for_address_confirmation, F.data == "enter_new_address")
async def process_new_address_entry(callback: CallbackQuery, state: FSMContext):
    """Запрос нового адреса"""
    await callback.message.edit_text(
        "✍️ <b>Ввод нового адреса</b>\n\n"
        "Введите ваш адрес доставки:",
    )
    await state.set_state(RegistrationStates.waiting_for_address_input)
    await callback.answer()


async def complete_registration_callback(callback: CallbackQuery, state: FSMContext):
    """Завершение регистрации из callback"""
    data = await state.get_data()
    name = data.get("name")
    phone = data.get("phone")
    address = data.get("address")
    telegram_id = data.get("telegram_id")  # Берем из состояния

    # Если telegram_id нет в состоянии, используем из callback
    if not telegram_id:
        telegram_id = callback.from_user.id

    try:
        client = await database.create_client(
            telegram_id=telegram_id,
            name=name,
            phone=phone,
            address=address
        )

        is_admin = telegram_id in ADMIN_IDS

        # Используем callback.message для отправки сообщения
        await callback.message.answer(
            f"🎉 <b>Поздравляем! Регистрация завершена!</b> ✅\n\n"
            f"👤 <b>Имя:</b> {name}\n"
            f"📱 <b>Телефон:</b> {phone}\n"
            f"📍 <b>Адрес:</b> {address}\n\n"
            "Теперь вы можете пользоваться всеми возможностями бота!\n"
            "Выберите действие из меню:",
            reply_markup=get_main_menu(is_admin=is_admin)
        )

        await state.clear()

    except Exception as e:
        await callback.message.answer(
            "❌ Произошла ошибка при регистрации. Попробуйте позже или обратитесь к администратору.",
            reply_markup=get_registration_keyboard()
        )
        await state.clear()


async def complete_registration(message: Message, state: FSMContext):
    """Завершение регистрации из обычного сообщения"""
    data = await state.get_data()
    name = data.get("name")
    phone = data.get("phone")
    address = data.get("address")
    telegram_id = data.get("telegram_id")

    if not telegram_id:
        telegram_id = message.from_user.id

    try:
        client = await database.create_client(
            telegram_id=telegram_id,
            name=name,
            phone=phone,
            address=address
        )

        is_admin = telegram_id in ADMIN_IDS

        await message.answer(
            f"🎉 <b>Поздравляем! Регистрация завершена!</b> ✅\n\n"
            f"👤 <b>Имя:</b> {name}\n"
            f"📱 <b>Телефон:</b> {phone}\n"
            f"📍 <b>Адрес:</b> {address}\n\n"
            "Теперь вы можете пользоваться всеми возможностями бота!\n"
            "Выберите действие из меню:",
            reply_markup=get_main_menu(is_admin=is_admin)
        )

        await state.clear()

    except Exception as e:
        await message.answer(
            "❌ Произошла ошибка при регистрации. Попробуйте позже или обратитесь к администратору.",
            reply_markup=get_registration_keyboard()
        )
        await state.clear()


async def cancel_registration(message: Message, state: FSMContext):
    """Отмена регистрации с предложением начать заново"""
    await state.clear()
    await message.answer(
        "❌ <b>Регистрация отменена</b>\n\n"
        "Если хотите начать заново, нажмите кнопку ниже или отправьте /start",
        reply_markup=get_restart_keyboard()
    )


# --- Главное меню (только для зарегистрированных пользователей) ---
@router.message(F.text == "📋 Меню")
async def show_menu(message: Message, state: FSMContext):
    """Показать главное меню (только для зарегистрированных)"""
    telegram_id = message.from_user.id

    client = await database.get_client_by_telegram_id(telegram_id)

    if not client:
        await message.answer(
            "Вы не зарегистрированы. Отправьте /start для регистрации.",
            reply_markup=get_hidden_keyboard()
        )
        return

    is_admin = telegram_id in ADMIN_IDS

    await message.answer(
        "Главное меню:",
        reply_markup=get_main_menu(is_admin=is_admin)
    )


# --- О боте (доступно всем, но с проверкой) ---
@router.message(F.text == "ℹ️ О боте")
async def about_bot(message: Message, state: FSMContext):
    """Информация о боте"""
    await message.answer(
        "🌍 <b>OverseasShop</b> - ваш помощник в заказе товаров из-за рубежа!\n\n"
        "⚠️ <b>Важно:</b> Это учебный проект для курсовой работы.\n"
        "Все операции виртуальные - реальных платежей и доставки нет.\n\n"
        "🛍️ <b>Возможности бота:</b>\n"
        "• Каталог товаров из разных стран\n"
        "• Корзина и оформление заказов\n"
        "• Отслеживание статуса доставки\n"
        "• Выбор типа доставки\n\n"
        "📦 Доступные страны:\n"
        "🇺🇸 США\n"
        "🇩🇪 Германия\n"
        "🇨🇳 Китай\n"
        "🇯🇵 Япония\n\n"
        "Выберите действие из меню ниже 👇"
    )


# --- Обработчики для перезапуска ---
@router.message(F.text == "🔄 Начать заново")
async def restart_registration(message: Message, state: FSMContext):
    """Перезапуск регистрации"""
    await start_command(message, state)


@router.message(F.text == "❌ Выйти")
async def exit_bot(message: Message, state: FSMContext):
    """Выход из бота"""
    await state.clear()
    await message.answer(
        "До свидания! Если захотите вернуться, отправьте /start",
        reply_markup=get_hidden_keyboard()
    )