# services/address_service.py
import asyncio
from dadata import Dadata
from config import DADATA_TOKEN, DADATA_SECRET


class AddressService:
    def __init__(self):
        self.dadata = None
        self.is_available = False
        self.initialize_dadata()

    def initialize_dadata(self):
        """Инициализация Dadata"""
        try:
            if DADATA_TOKEN and DADATA_SECRET:
                self.dadata = Dadata(DADATA_TOKEN, DADATA_SECRET)
                self.is_available = True
                print("✅ Dadata успешно инициализирован")
            else:
                print("⚠️ Dadata не настроен: отсутствуют токены")
        except Exception as e:
            print(f"❌ Ошибка инициализации Dadata: {e}")
            self.is_available = False

    async def suggest_address(self, query: str, count: int = 5):
        """Получить подсказки адресов"""
        if not self.is_available:
            return []

        try:
            # Запускаем в отдельном потоке, т.к. Dadata синхронный
            loop = asyncio.get_event_loop()
            suggestions = await loop.run_in_executor(
                None,
                lambda: self.dadata.suggest("address", query, count=count)
            )

            formatted_suggestions = []
            for suggestion in suggestions:
                formatted_suggestions.append({
                    'value': suggestion['value'],
                    'data': suggestion['data']
                })

            return formatted_suggestions
        except Exception as e:
            print(f"❌ Ошибка получения подсказок: {e}")
            return []

    async def clean_address(self, address: str):
        """Очистить и стандартизировать адрес"""
        if not self.is_available:
            return None

        try:
            loop = asyncio.get_event_loop()
            cleaned = await loop.run_in_executor(
                None,
                lambda: self.dadata.clean("address", address)
            )
            return cleaned
        except Exception as e:
            print(f"❌ Ошибка очистки адреса: {e}")
            return None


# Глобальный экземпляр
address_service = AddressService()