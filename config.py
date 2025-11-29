"""
Конфигурация бота - загрузка переменных окружения.
"""
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


class Config:
    """Класс для хранения конфигурации бота."""
    
    # Telegram Bot Token
    TG_TOKEN: str = os.getenv("TG_TOKEN", "")
    
    # Admin Telegram ID
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    
    # Game settings
    GAME_DURATION_SECONDS: int = 60
    
    @classmethod
    def validate(cls) -> bool:
        """Проверяет, что все необходимые переменные окружения установлены."""
        if not cls.TG_TOKEN:
            raise ValueError("TG_TOKEN не установлен в переменных окружения!")
        if not cls.ADMIN_ID:
            raise ValueError("ADMIN_ID не установлен в переменных окружения!")
        return True
