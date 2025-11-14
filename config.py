import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # OpenAI настройки
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')  # или gpt-4o-mini

    # Локальные настройки
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
    ENABLE_PRINTING = os.getenv('ENABLE_PRINTING', 'false').lower() == 'true'
    PRINTER_NAME = os.getenv('PRINTER_NAME', '')  # Пустое значение = принтер по умолчанию
    LP_COMMAND_PATH = os.getenv('LP_COMMAND_PATH', '/usr/bin/lp')  # Полный путь к команде lp
    LP_OPTIONS = os.getenv('LP_OPTIONS', '')  # Дополнительные опции для lp (например: "-o fit-to-page -o scaling=100")
    PAGE_SIZE = os.getenv('PAGE_SIZE', 'A4')  # Формат страницы для печати (A4, Letter, A3, etc.)

    # Размеры страниц в мм (ширина, высота)
    PAGE_SIZES = {
        'A4': (210, 297),
        'A3': (297, 420),
        'A5': (148, 210),
        'Letter': (216, 279),
        'Legal': (216, 356),
    }

    # Flask настройки
    FLASK_HOST = '0.0.0.0'
    FLASK_PORT = 5000
    DEBUG = True

    @staticmethod
    def validate():
        """Проверка наличия обязательных настроек"""
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in .env file")

        # Создать папку output если её нет
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)