# --- Скрипт для инициализации базы данных тестовыми данными ---
import asyncio
from database import (
    init_db, add_country, add_shop, add_category, add_product,
    set_exchange_rate, add_admin
)
from config import ADMIN_IDS


async def initialize_database():
    """Инициализация базы данных с тестовыми данными"""
    print("🔄 Инициализация базы данных...")

    # Создаем таблицы
    await init_db()
    print("✅ Таблицы созданы")

    # Добавляем курсы валют
    print("💱 Добавление курсов валют...")
    await set_exchange_rate('USD', 95.0)
    await set_exchange_rate('EUR', 105.0)
    await set_exchange_rate('CNY', 13.0)
    await set_exchange_rate('JPY', 0.65)
    print("✅ Курсы валют установлены")

    # Добавляем страны
    print("🌍 Добавление стран...")
    usa = await add_country('США', 'USD', '🇺🇸', 1500)
    germany = await add_country('Германия', 'EUR', '🇩🇪', 1200)
    china = await add_country('Китай', 'CNY', '🇨🇳', 800)
    japan = await add_country('Япония', 'JPY', '🇯🇵', 1800)
    print("✅ Страны добавлены")

    # Добавляем магазины (минимум 2 на каждую страну)
    print("🏪 Добавление магазинов...")

    # США - 2 магазина
    amazon = await add_shop(usa.id, 'Amazon', 'Крупнейший интернет-магазин США с миллионами товаров', 'amazon.com')
    ebay = await add_shop(usa.id, 'eBay', 'Всемирно известный аукцион и торговая площадка', 'ebay.com')
    walmart = await add_shop(usa.id, 'Walmart', 'Крупнейшая розничная сеть США', 'walmart.com')

    # Германия - 2 магазина
    zalando = await add_shop(germany.id, 'Zalando', 'Крупнейший европейский онлайн-магазин моды', 'zalando.de')
    otto = await add_shop(germany.id, 'Otto', 'Немецкий интернет-магазин бытовой техники и моды', 'otto.de')
    mediamarkt = await add_shop(germany.id, 'MediaMarkt', 'Европейская сеть электроники', 'mediamarkt.de')

    # Китай - 2 магазина
    aliexpress = await add_shop(china.id, 'AliExpress', 'Популярная международная торговая площадка', 'aliexpress.com')
    jd = await add_shop(china.id, 'JD.com', 'Крупнейший китайский онлайн-ритейлер', 'jd.com')
    taobao = await add_shop(china.id, 'Taobao', 'Китайская платформа для покупок с широким ассортиментом', 'taobao.com')

    # Япония - 2 магазина
    rakuten = await add_shop(japan.id, 'Rakuten', 'Японский интернет-магазин с разнообразными товарами',
                             'rakuten.co.jp')
    yodobashi = await add_shop(japan.id, 'Yodobashi', 'Крупнейший магазин электроники в Японии', 'yodobashi.com')
    uniqlo = await add_shop(japan.id, 'Uniqlo', 'Японский бренд качественной повседневной одежды', 'uniqlo.com')

    print("✅ Магазины добавлены")

    # Добавляем категории
    print("📦 Добавление категорий...")
    clothing = await add_category('👕 Одежда', 'Мужская, женская и детская одежда')
    shoes = await add_category('👟 Обувь', 'Обувь для всей семьи и любого случая')
    electronics = await add_category('💻 Электроника', 'Современные гаджеты и электроника')
    games = await add_category('🎮 Игры и игрушки', 'Видеоигры, настольные игры и игрушки')
    books = await add_category('📚 Книги', 'Книги на разных языках и жанрах')
    home = await add_category('🏠 Для дома', 'Товары для дома, кухни и быта')
    beauty = await add_category('💄 Красота', 'Косметика, уход и парфюмерия')
    sports = await add_category('⚽ Спорт', 'Спортивные товары и инвентарь')
    print("✅ Категории добавлены")

    # Добавляем товары (минимум 2 в каждом магазине)
    print("🛍️ Добавление товаров...")

    # Amazon (США) - 3 товара
    await add_product(
        amazon.id, electronics.id,
        'Apple AirPods Pro 2',
        'Беспроводные наушники с активным шумоподавлением и улучшенным звуком',
        249.0, 'USD', 0.05
    )
    await add_product(
        amazon.id, electronics.id,
        'Kindle Paperwhite 11',
        'Электронная книга с водонепроницаемым дизайном и подсветкой',
        139.99, 'USD', 0.2
    )
    await add_product(
        amazon.id, books.id,
        'The Great Gatsby - Collector\'s Edition',
        'Классический роман Ф. Скотта Фицджеральда в подарочном издании',
        25.99, 'USD', 0.4
    )

    # eBay (США) - 3 товара
    await add_product(
        ebay.id, games.id,
        'PlayStation 5 DualSense Controller',
        'Беспроводной контроллер для PS5 с тактильной отдачей',
        69.99, 'USD', 0.3
    )
    await add_product(
        ebay.id, electronics.id,
        'iPhone 14 Pro Case',
        'Защитный чехол для iPhone 14 Pro с дизайнерским принтом',
        19.99, 'USD', 0.1
    )
    await add_product(
        ebay.id, sports.id,
        'Yoga Mat Premium',
        'Профессиональный коврик для йоги с противоскользящим покрытием',
        29.99, 'USD', 1.2
    )

    # Walmart (США) - 3 товара
    await add_product(
        walmart.id, home.id,
        'Kitchen Blender 2L',
        'Мощный блендер для кухни с 8 скоростями',
        49.99, 'USD', 2.5
    )
    await add_product(
        walmart.id, clothing.id,
        'Men\'s Casual Shirt',
        'Хлопковая рубашка для повседневной носки',
        24.99, 'USD', 0.3
    )
    await add_product(
        walmart.id, beauty.id,
        'Skincare Set',
        'Набор для ухода за кожей с витамином C',
        34.99, 'USD', 0.6
    )

    # Zalando (Германия) - 3 товара
    await add_product(
        zalando.id, clothing.id,
        'Nike Air Max 90 Premium',
        'Классические кроссовки с технологией Air Max',
        129.0, 'EUR', 0.8
    )
    await add_product(
        zalando.id, clothing.id,
        'Adidas Originals Hoodie',
        'Толстовка с капюшоном из коллекции Originals',
        59.99, 'EUR', 0.5
    )
    await add_product(
        zalando.id, shoes.id,
        'Puma RS-X Sneakers',
        'Стильные кроссовки с ретро-дизайном',
        89.99, 'EUR', 0.9
    )

    # Otto (Германия) - 3 товара
    await add_product(
        otto.id, home.id,
        'Dyson Vacuum Cleaner V11',
        'Беспроводной пылесос с технологией лазерной подсветки',
        599.0, 'EUR', 3.2
    )
    await add_product(
        otto.id, electronics.id,
        'Samsung 4K Smart TV 55"',
        'Телевизор с разрешением 4K и Smart TV функциями',
        799.0, 'EUR', 12.5
    )
    await add_product(
        otto.id, home.id,
        'KitchenAid Stand Mixer',
        'Профессиональный кухонный миксер для выпечки',
        429.0, 'EUR', 8.7
    )

    # MediaMarkt (Германия) - 3 товара
    await add_product(
        mediamarkt.id, electronics.id,
        'Sony WH-1000XM5 Headphones',
        'Наушники с шумоподавлением и премиальным звуком',
        349.0, 'EUR', 0.3
    )
    await add_product(
        mediamarkt.id, electronics.id,
        'Apple iPad Air 5',
        'Планшет с чипом M1 и поддержкой Apple Pencil',
        649.0, 'EUR', 0.5
    )
    await add_product(
        mediamarkt.id, games.id,
        'Xbox Series X Console',
        'Игровая консоль нового поколения от Microsoft',
        499.0, 'EUR', 4.5
    )

    # AliExpress (Китай) - 3 товара
    await add_product(
        aliexpress.id, electronics.id,
        'Xiaomi Smart Band 7 Pro',
        'Фитнес-браслет с AMOLED-экраном и GPS',
        299.0, 'CNY', 0.05
    )
    await add_product(
        aliexpress.id, electronics.id,
        'Wireless Silent Mouse',
        'Беспроводная мышь с бесшумными кликами и RGB подсветкой',
        89.0, 'CNY', 0.1
    )
    await add_product(
        aliexpress.id, home.id,
        'Smart LED Strip 5M RGB',
        'Умная RGB LED-лента с управлением через приложение',
        199.0, 'CNY', 0.3
    )

    # JD.com (Китай) - 3 товара
    await add_product(
        jd.id, electronics.id,
        'Huawei Watch GT 3',
        'Умные часы с двухнедельным временем работы',
        1299.0, 'CNY', 0.1
    )
    await add_product(
        jd.id, clothing.id,
        'Winter Down Jacket',
        'Теплая пуховая куртка для холодной погоды',
        599.0, 'CNY', 1.2
    )
    await add_product(
        jd.id, home.id,
        'Air Purifier Pro',
        'Очиститель воздуха с HEPA фильтром',
        899.0, 'CNY', 5.8
    )

    # Taobao (Китай) - 3 товара
    await add_product(
        taobao.id, clothing.id,
        'Traditional Chinese Dress',
        'Традиционное китайское платье Ципао',
        399.0, 'CNY', 0.6
    )
    await add_product(
        taobao.id, home.id,
        'Porcelain Tea Set',
        'Фарфоровый чайный набор ручной работы',
        599.0, 'CNY', 2.3
    )
    await add_product(
        taobao.id, beauty.id,
        'Korean Skincare 10-Step Set',
        'Корейский набор для ухода за кожей из 10 средств',
        299.0, 'CNY', 1.1
    )

    # Rakuten (Япония) - 3 товара
    await add_product(
        rakuten.id, games.id,
        'Nintendo Switch OLED Model',
        'Игровая консоль с улучшенным OLED-экраном',
        37980.0, 'JPY', 0.4
    )
    await add_product(
        rakuten.id, books.id,
        'Japanese Manga Collection Vol.1-5',
        'Коллекция популярной манги на японском языке',
        8500.0, 'JPY', 1.2
    )
    await add_product(
        rakuten.id, beauty.id,
        'SK-II Facial Treatment Essence',
        'Легендарная эссенция для ухода за кожей',
        25000.0, 'JPY', 0.3
    )

    # Yodobashi (Япония) - 3 товара
    await add_product(
        yodobashi.id, electronics.id,
        'Sony Alpha A7 IV Camera',
        'Беззеркальная камера с полнокадровым сенсором',
        329800.0, 'JPY', 1.1
    )
    await add_product(
        yodobashi.id, electronics.id,
        'Canon EOS R5 Mirrorless',
        'Профессиональная камера с 8K видео',
        449800.0, 'JPY', 1.4
    )
    await add_product(
        yodobashi.id, electronics.id,
        'Fujifilm Instax Mini 12',
        'Мгновенная камера для печати фотографий',
        8800.0, 'JPY', 0.8
    )

    # Uniqlo (Япония) - 3 товара
    await add_product(
        uniqlo.id, clothing.id,
        'HEATTECH Ultra Warm T-Shirt',
        'Термобелье для холодной погоды с технологией нагрева',
        1990.0, 'JPY', 0.2
    )
    await add_product(
        uniqlo.id, clothing.id,
        'AIRism Cotton Oversized T-Shirt',
        'Футболка oversized из хлопка с технологией охлаждения',
        1490.0, 'JPY', 0.3
    )
    await add_product(
        uniqlo.id, clothing.id,
        'Blocktech Parka Coat',
        'Парка с водонепроницаемой технологией',
        7990.0, 'JPY', 0.9
    )

    print("✅ Товары добавлены")

    # Добавляем администраторов
    print("👑 Добавление администраторов...")
    for admin_id in ADMIN_IDS:
        try:
            await add_admin(admin_id, f"Admin_{admin_id}")
            print(f"✅ Администратор {admin_id} добавлен")
        except Exception as e:
            print(f"⚠️ Администратор {admin_id} уже существует или ошибка: {e}")

    print("\n🎉 Инициализация завершена успешно!")
    print("\n📊 Статистика базы данных:")
    print("   🌍 Стран: 4")
    print("   🏪 Магазинов: 12")
    print("   📦 Категорий: 8")
    print("   🛍️ Товаров: 36")
    print("   💱 Курсов валют: 4")
    print("\n✅ Каждая страна имеет минимум 3 магазина")
    print("✅ Каждый магазин имеет минимум 3 товара")
    print("✅ База данных готова к работе!")


if __name__ == "__main__":
    asyncio.run(initialize_database())