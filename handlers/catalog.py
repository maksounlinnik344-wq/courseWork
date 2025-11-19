# --- Импорты ---
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

import database
from utils import convert_to_rub, format_price
from keyboards import (
    get_countries_keyboard,
    get_shops_keyboard,
    get_categories_keyboard,
    get_products_keyboard,
    get_product_keyboard
)


# --- Инициализация роутера ---
router = Router()


# --- Просмотр каталога ---
@router.message(F.text == "🛍️ Каталог товаров")
async def show_catalog(message: Message):
    """Показать каталог стран"""
    client = await database.get_client_by_telegram_id(message.from_user.id)
    
    if not client:
        await message.answer("Пожалуйста, сначала зарегистрируйтесь через /start")
        return
    
    countries = await database.get_all_countries()
    
    if not countries:
        await message.answer(
            "К сожалению, каталог пока пуст. Попробуйте позже."
        )
        return
    
    await message.answer(
        "🌍 <b>Выберите страну:</b>\n\n"
        "Доступные страны для заказа товаров:",
        reply_markup=get_countries_keyboard(countries)
    )


# --- Обработка выбора страны ---
@router.callback_query(F.data.startswith("country_"))
async def process_country_selection(callback: CallbackQuery):
    """Обработка выбора страны"""
    country_id = int(callback.data.split("_")[1])
    country = await database.get_country_by_id(country_id)
    
    if not country:
        await callback.answer("Страна не найдена", show_alert=True)
        return
    
    shops = await database.get_shops_by_country(country_id)
    
    if not shops:
        await callback.answer(
            f"В стране {country.name} пока нет доступных магазинов",
            show_alert=True
        )
        return
    
    await callback.message.edit_text(
        f"{country.flag_emoji} <b>{country.name}</b>\n\n"
        f"Валюта: {country.currency}\n"
        f"Базовая стоимость доставки: {country.delivery_base_cost} ₽\n\n"
        "Выберите магазин:",
        reply_markup=get_shops_keyboard(shops, country_id)
    )
    await callback.answer()


# --- Обработка выбора магазина ---
@router.callback_query(F.data.startswith("shop_"))
async def process_shop_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора магазина"""
    shop_id = int(callback.data.split("_")[1])
    shop = await database.get_shop_by_id(shop_id)
    
    if not shop:
        await callback.answer("Магазин не найден", show_alert=True)
        return
    
    await state.update_data(current_shop_id=shop_id)
    
    await callback.message.edit_text(
        f"🏪 <b>{shop.name}</b>\n\n"
        f"{shop.description or 'Добро пожаловать в наш магазин!'}\n\n"
        "Выберите категорию товаров:",
        reply_markup=get_categories_keyboard(shop_id)
    )
    await callback.answer()


# --- Обработка выбора категории ---
@router.callback_query(F.data.startswith("category_"))
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории"""
    parts = callback.data.split("_")
    category_id = int(parts[1])
    shop_id = int(parts[3])
    
    category = await database.get_category_by_id(category_id)
    products = await database.get_products_by_category(category_id)
    
    # Фильтруем товары по магазину
    products = [p for p in products if p.shop_id == shop_id]
    
    if not products:
        await callback.answer(
            "В этой категории пока нет товаров",
            show_alert=True
        )
        return
    
    await state.update_data(current_category_id=category_id, current_products=products)
    
    # Получаем курсы валют
    exchange_rates = {}
    for currency in ['USD', 'EUR', 'CNY', 'JPY']:
        rate = await database.get_exchange_rate(currency)
        if rate:
            exchange_rates[currency] = rate.rate_to_rub
    
    # Показываем первые 5 товаров
    products_page = products[:5]
    
    text = f"📦 <b>{category.name}</b>\n\n"
    for product in products_page:
        price_rub = await convert_to_rub(product.price_original, product.currency, exchange_rates)
        text += (
            f"🛍️ <b>{product.name}</b>\n"
            f"💰 {product.price_original} {product.currency} (≈{format_price(price_rub)} ₽)\n"
            f"📝 {product.description[:100]}...\n\n"
        )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_products_keyboard(products_page, page=0, total_pages=(len(products) + 4) // 5)
    )
    await callback.answer()


# --- Обработка выбора товара ---
@router.callback_query(F.data.startswith("product_"))
async def process_product_selection(callback: CallbackQuery):
    """Обработка выбора товара"""
    product_id = int(callback.data.split("_")[1])
    product = await database.get_product_by_id(product_id)
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    # Получаем курс валюты
    rate = await database.get_exchange_rate(product.currency)
    exchange_rate = rate.rate_to_rub if rate else 1.0
    price_rub = product.price_original * exchange_rate
    
    text = (
        f"🛍️ <b>{product.name}</b>\n\n"
        f"📝 {product.description}\n\n"
        f"💰 Цена: {product.price_original} {product.currency}\n"
        f"💵 В рублях: ≈{format_price(price_rub)} ₽\n"
    )
    
    if product.weight:
        text += f"⚖️ Вес: {product.weight} кг\n"
    
    # Если есть фото, отправляем с фото
    if product.photo_file_id:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=product.photo_file_id,
            caption=text,
            reply_markup=get_product_keyboard(product_id)
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=get_product_keyboard(product_id)
        )
    
    await callback.answer()


# --- Добавление в корзину ---
@router.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart(callback: CallbackQuery):
    """Добавление товара в корзину"""
    product_id = int(callback.data.split("_")[3])
    client = await database.get_client_by_telegram_id(callback.from_user.id)
    
    if not client:
        await callback.answer("Ошибка: клиент не найден", show_alert=True)
        return
    
    product = await database.get_product_by_id(product_id)
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    await database.add_to_cart(client.id, product_id, quantity=1)
    
    await callback.answer(
        f"✅ Товар '{product.name}' добавлен в корзину!",
        show_alert=True
    )


# --- Навигация назад ---
@router.callback_query(F.data == "back_to_countries")
async def back_to_countries(callback: CallbackQuery):
    """Возврат к списку стран"""
    countries = await database.get_all_countries()
    await callback.message.edit_text(
        "🌍 <b>Выберите страну:</b>\n\n"
        "Доступные страны для заказа товаров:",
        reply_markup=get_countries_keyboard(countries)
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_shops")
async def back_to_shops(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку магазинов"""
    data = await state.get_data()
    shop_id = data.get("current_shop_id")
    
    if shop_id:
        shop = await database.get_shop_by_id(shop_id)
        if shop:
            shops = await database.get_shops_by_country(shop.country_id)
            country = await database.get_country_by_id(shop.country_id)
            
            await callback.message.edit_text(
                f"{country.flag_emoji} <b>{country.name}</b>\n\n"
                "Выберите магазин:",
                reply_markup=get_shops_keyboard(shops, country.id)
            )
    
    await callback.answer()


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    """Возврат к категориям"""
    data = await state.get_data()
    shop_id = data.get("current_shop_id")
    
    if shop_id:
        shop = await database.get_shop_by_id(shop_id)
        await callback.message.edit_text(
            f"🏪 <b>{shop.name}</b>\n\n"
            "Выберите категорию товаров:",
            reply_markup=get_categories_keyboard(shop_id)
        )
    
    await callback.answer()


@router.callback_query(F.data == "back_to_products")
async def back_to_products(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку товаров"""
    data = await state.get_data()
    category_id = data.get("current_category_id")
    products = data.get("current_products", [])
    
    if category_id and products:
        category = await database.get_category_by_id(category_id)
        
        # Получаем курсы валют
        exchange_rates = {}
        for currency in ['USD', 'EUR', 'CNY', 'JPY']:
            rate = await database.get_exchange_rate(currency)
            if rate:
                exchange_rates[currency] = rate.rate_to_rub
        
        products_page = products[:5]
        
        text = f"📦 <b>{category.name}</b>\n\n"
        for product in products_page:
            price_rub = await convert_to_rub(product.price_original, product.currency, exchange_rates)
            text += (
                f"🛍️ <b>{product.name}</b>\n"
                f"💰 {product.price_original} {product.currency} (≈{format_price(price_rub)} ₽)\n"
                f"📝 {product.description[:100]}...\n\n"
            )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_products_keyboard(products_page, page=0, total_pages=(len(products) + 4) // 5)
        )
    
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.delete()
    await callback.answer()
