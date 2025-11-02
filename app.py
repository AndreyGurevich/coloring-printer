from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from config import Config
from models import (
    GenerateRequest, PrintRequest, HealthResponse,
    GenerateResponse, PrintResponse, ErrorResponse,
    AliceRequest, AliceResponse
)
from image_generator import ImageGenerator
from image_processor import ImageProcessor
from printer import Printer

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация сервисов
generator = ImageGenerator()
processor = ImageProcessor()
printer = Printer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    # Startup
    logger.info("=" * 50)
    logger.info("Coloring Printer Server (FastAPI)")
    logger.info("=" * 50)
    logger.info(f"OpenAI API configured: {bool(Config.OPENAI_API_KEY)}")
    logger.info(f"Printing enabled: {Config.ENABLE_PRINTING}")
    logger.info(f"Output directory: {Config.OUTPUT_DIR}")
    logger.info("=" * 50)

    Config.validate()

    yield

    # Shutdown
    logger.info("Shutting down...")


# Создание приложения
app = FastAPI(
    title="Coloring Printer API",
    description="API для генерации раскрасок через OpenAI и печати",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", tags=["Root"])
async def root():
    """Корневой endpoint"""
    return {
        "message": "Coloring Printer API",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """Проверка работоспособности сервера"""
    return HealthResponse(
        status="ok",
        message="Coloring printer server is running",
        openai_configured=bool(Config.OPENAI_API_KEY),
        printing_enabled=Config.ENABLE_PRINTING
    )


@app.post(
    "/generate",
    response_model=GenerateResponse,
    responses={500: {"model": ErrorResponse}},
    tags=["Generation"]
)
async def generate_coloring(request: GenerateRequest):
    """
    Генерирует раскраску через OpenAI DALL-E (без печати)

    - **subject**: Тема раскраски (например, "капибара", "динозавр")

    Возвращает пути к оригинальному и улучшенному изображению.
    """
    try:
        logger.info(f"Generating coloring page for: {request.subject}")

        # Генерируем изображение
        filepath, url = generator.generate_coloring_page(request.subject)

        # Улучшаем для раскраски
        enhanced_path = processor.enhance_for_coloring(filepath)

        logger.info(f"Successfully generated: {enhanced_path}")

        return GenerateResponse(
            status="success",
            subject=request.subject,
            original_file=filepath,
            enhanced_file=enhanced_path,
            openai_url=url
        )

    except Exception as e:
        logger.error(f"Error generating coloring page: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/print",
    response_model=PrintResponse,
    responses={500: {"model": ErrorResponse}},
    tags=["Printing"]
)
async def print_coloring(request: PrintRequest):
    """
    Генерирует раскраску и отправляет на печать

    - **subject**: Тема раскраски
    - **enhance**: Улучшить изображение для раскраски (по умолчанию true)

    Возвращает статус печати и путь к файлу.
    """
    try:
        logger.info(f"Printing coloring page for: {request.subject}")

        # Генерируем изображение
        filepath, url = generator.generate_coloring_page(request.subject)

        # Улучшаем если нужно
        if request.enhance:
            filepath = processor.enhance_for_coloring(filepath)

        # Печатаем
        success, message = printer.print_image(filepath)

        if not success:
            raise HTTPException(status_code=500, detail=message)

        logger.info(f"Successfully printed: {filepath}")

        return PrintResponse(
            status="success",
            subject=request.subject,
            file=filepath,
            print_message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error printing coloring page: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alice", tags=["Alice"])
async def alice_webhook(request: Request):
    """
    Webhook для Яндекс.Алисы

    Принимает запросы от навыка Алисы и обрабатывает команды.
    """
    try:
        data = await request.json()

        # Логируем запрос от Алисы
        logger.info(f"Alice request: {data}")

        # Извлекаем команду пользователя
        command = data.get('request', {}).get('command', '').lower()

        # Парсинг команды
        subject = parse_subject_from_command(command)

        if not subject:
            return create_alice_response(
                data,
                'Скажите, какую раскраску вы хотите? Например: "сделай раскраску капибара"'
            )

        # Генерируем и печатаем
        filepath, url = generator.generate_coloring_page(subject)
        enhanced_path = processor.enhance_for_coloring(filepath)
        success, message = printer.print_image(enhanced_path)

        if success:
            response_text = f'Готово! Раскраска "{subject}" отправлена на печать.'
        else:
            response_text = f'Раскраска "{subject}" создана, но не удалось напечатать: {message}'

        return create_alice_response(data, response_text)

    except Exception as e:
        logger.error(f"Error in Alice webhook: {str(e)}")
        return create_alice_response(
            data,
            f'Извините, произошла ошибка: {str(e)}'
        )


def parse_subject_from_command(command: str) -> str:
    """
    Парсит тему раскраски из команды пользователя

    "сделай раскраску капибара" -> "капибара"
    """
    keywords = ['раскраск', 'картинк', 'нарисуй', 'распечатай']

    for keyword in keywords:
        if keyword in command:
            parts = command.split(keyword)
            if len(parts) > 1:
                subject = parts[1].strip()
                # Убираем предлоги
                for prep in ['с ', 'про ', 'о ', 'about ', 'с']:
                    subject = subject.replace(prep, '').strip()

                if subject:
                    return subject

    return ""


def create_alice_response(request_data: dict, text: str, end_session: bool = False) -> dict:
    """Создает ответ для Алисы"""
    return {
        'version': request_data.get('version', '1.0'),
        'session': request_data.get('session', {}),
        'response': {
            'text': text,
            'end_session': end_session
        }
    }


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработчик HTTP ошибок"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработчик всех остальных ошибок"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        reload=Config.DEBUG,
        log_level="info"
    )