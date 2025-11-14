#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, send_from_directory
import openai
import requests
import os
import logging
from datetime import datetime
from config import Config
import subprocess
from PIL import Image

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Валидация конфигурации
Config.validate()

app = Flask(__name__)

# Инициализация OpenAI клиента
openai.api_key = Config.OPENAI_API_KEY


def generate_coloring_page(subject: str, style: str = "simple", detail_level: str = "medium") -> str:
    """
    Генерирует раскраску через DALL-E

    Args:
        subject: Что рисовать (например, "кот")
        style: Стиль (simple, cartoon, realistic)
        detail_level: Уровень детализации (low, medium, high)

    Returns:
        URL сгенерированного изображения
    """
    # Составляем промпт в зависимости от параметров
    style_prompts = {
        "simple": "simple line art, clean lines, minimalistic",
        "cartoon": "cartoon style, fun and playful lines",
        "realistic": "realistic line art, detailed outlines"
    }

    detail_prompts = {
        "low": "very simple, few details, suitable for young children",
        "medium": "moderate amount of details, balanced complexity",
        "high": "highly detailed, intricate patterns, for advanced coloring"
    }

    prompt = f"""Black and white coloring page of {subject}.
{style_prompts.get(style, style_prompts['simple'])}.
{detail_prompts.get(detail_level, detail_prompts['medium'])}.
Clear outlines, no shading, no colors, white background, ready to print and color."""

    logger.info(f"Generating coloring page with prompt: {prompt}")

    try:
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )

        image_url = response.data[0].url
        logger.info(f"Generated image URL: {image_url}")
        return image_url

    except Exception as e:
        logger.error(f"Error generating image: {e}")
        raise


def pad_image_to_page_size(image_path: str, page_size: str) -> str:
    """
    Добавляет padding к изображению для соответствия пропорциям страницы

    Args:
        image_path: путь к исходному квадратному изображению
        page_size: формат страницы (A4, Letter, и т.д.)

    Returns:
        путь к padded изображению
    """
    if page_size not in Config.PAGE_SIZES:
        logger.warning(f"Unknown page size: {page_size}, using A4")
        page_size = 'A4'

    # Получаем соотношение сторон страницы
    page_width, page_height = Config.PAGE_SIZES[page_size]
    page_aspect_ratio = page_width / page_height

    # Открываем исходное изображение
    img = Image.open(image_path)
    img_width, img_height = img.size

    # Вычисляем новые размеры с учетом пропорций страницы
    # Изображение квадратное (1024x1024), страница вертикальная (например, 210x297)
    # Нужно добавить padding по высоте
    new_width = img_width
    new_height = int(img_width / page_aspect_ratio)

    # Создаем новое изображение с белым фоном
    padded_img = Image.new('RGB', (new_width, new_height), 'white')

    # Вставляем исходное изображение по центру
    offset_y = (new_height - img_height) // 2
    padded_img.paste(img, (0, offset_y))

    # Сохраняем padded версию
    padded_path = image_path.replace('.png', '_padded.png')
    padded_img.save(padded_path)

    logger.info(f"Padded image saved to: {padded_path} (size: {new_width}x{new_height})")
    return padded_path


def download_image(url: str, subject: str) -> str:
    """Скачивает изображение локально"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_subject = safe_subject.replace(' ', '_')
    filename = f"coloring_{safe_subject}_{timestamp}.png"
    filepath = os.path.join(Config.OUTPUT_DIR, filename)

    response = requests.get(url)
    response.raise_for_status()

    with open(filepath, 'wb') as f:
        f.write(response.content)

    logger.info(f"Image saved to: {filepath}")
    return filepath


def print_image(filepath: str) -> bool:
    """
    Печатает изображение

    Args:
        filepath: путь к оригинальному изображению (квадратному)

    Returns:
        True если печать успешна, False иначе
    """
    if not Config.ENABLE_PRINTING:
        logger.info("Printing disabled in config")
        return False

    try:
        # Создаем padded версию изображения для печати
        padded_filepath = pad_image_to_page_size(filepath, Config.PAGE_SIZE)

        # Используем полный путь к команде lp
        lp_path = Config.LP_COMMAND_PATH

        # Формируем базовую команду печати
        cmd = [lp_path]

        # Добавляем принтер если указан
        if Config.PRINTER_NAME:
            cmd.extend(['-d', Config.PRINTER_NAME])
            logger.info(f"Printing to printer: {Config.PRINTER_NAME}")
        else:
            logger.info("Printing to default printer")

        # Добавляем опции из .env если указаны
        if Config.LP_OPTIONS:
            # Разбиваем строку опций на отдельные аргументы
            import shlex
            options = shlex.split(Config.LP_OPTIONS)
            cmd.extend(options)
            logger.info(f"Using LP options: {Config.LP_OPTIONS}")

        # Добавляем путь к padded файлу для печати
        cmd.append(padded_filepath)

        logger.info(f"Running command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Printed: {padded_filepath}")
        logger.info(f"Print output: {result.stdout}")

        # Удаляем временный padded файл после печати
        try:
            os.remove(padded_filepath)
            logger.info(f"Removed temporary padded file: {padded_filepath}")
        except Exception as e:
            logger.warning(f"Could not remove temporary file {padded_filepath}: {e}")

        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Print error: {e.stderr}")
        return False
    except FileNotFoundError as e:
        logger.error(f"lp command not found at {Config.LP_COMMAND_PATH}: {e}")
        logger.error("Try setting LP_COMMAND_PATH in .env to the full path (e.g., /usr/bin/lp)")
        return False
    except Exception as e:
        logger.error(f"Error during printing: {e}")
        return False


@app.route('/')
def index():
    """Главная страница с формой"""
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    """API endpoint для генерации раскраски"""
    try:
        data = request.json
        subject = data.get('subject', '').strip()
        style = data.get('style', 'simple')
        detail_level = data.get('detail_level', 'medium')
        should_print = data.get('print', False)

        if not subject:
            return jsonify({'error': 'Subject is required'}), 400

        logger.info(f"Request: subject='{subject}', style='{style}', detail='{detail_level}', print={should_print}")

        # Генерируем изображение
        image_url = generate_coloring_page(subject, style, detail_level)

        # Скачиваем локально
        filepath = download_image(image_url, subject)
        filename = os.path.basename(filepath)

        # Печатаем если нужно
        printed = False
        if should_print:
            printed = print_image(filepath)

        return jsonify({
            'success': True,
            'image_url': f'/output/{filename}',
            'original_url': image_url,
            'filename': filename,
            'printed': printed
        })

    except Exception as e:
        logger.error(f"Error in /generate: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/output/<filename>')
def serve_output(filename):
    """Отдаёт сгенерированные файлы"""
    return send_from_directory(Config.OUTPUT_DIR, filename)


@app.route('/print', methods=['POST'])
def print_endpoint():
    """API endpoint для печати уже сгенерированного файла"""
    try:
        data = request.json
        filename = data.get('filename', '').strip()

        if not filename:
            return jsonify({'success': False, 'message': 'Filename is required'}), 400

        filepath = os.path.join(Config.OUTPUT_DIR, filename)

        # Проверяем существование файла
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'message': 'Файл не найден'}), 404

        logger.info(f"Print request for: {filename}")

        # Печатаем
        success = print_image(filepath)

        if success:
            return jsonify({'success': True, 'message': 'Отправлено на печать!'})
        else:
            if not Config.ENABLE_PRINTING:
                return jsonify({'success': False, 'message': 'Печать отключена в настройках'})
            else:
                return jsonify({'success': False, 'message': 'Не удалось отправить на печать'})

    except Exception as e:
        logger.error(f"Error in /print: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/gallery')
def gallery():
    """Показывает галерею всех сгенерированных раскрасок"""
    try:
        files = []
        for filename in os.listdir(Config.OUTPUT_DIR):
            if filename.endswith('.png'):
                filepath = os.path.join(Config.OUTPUT_DIR, filename)
                stat = os.stat(filepath)
                files.append({
                    'filename': filename,
                    'url': f'/output/{filename}',
                    'timestamp': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })

        # Сортируем по времени (новые сначала)
        files.sort(key=lambda x: x['timestamp'], reverse=True)

        return render_template('gallery.html', files=files)
    except Exception as e:
        logger.error(f"Error in /gallery: {e}")
        return str(e), 500


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Starting Coloring Printer Web Server")
    logger.info("=" * 60)
    logger.info(f"Host: {Config.FLASK_HOST}:{Config.FLASK_PORT}")
    logger.info(f"Output directory: {Config.OUTPUT_DIR}")
    logger.info(f"Printing enabled: {Config.ENABLE_PRINTING}")
    logger.info("=" * 60)

    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.DEBUG
    )
