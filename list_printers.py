#!/usr/bin/env python3
"""
Утилита для просмотра списка доступных принтеров
"""
import subprocess
import sys


def list_printers():
    """Показывает список всех принтеров в системе"""
    print("=" * 60)
    print("Список доступных принтеров")
    print("=" * 60)

    try:
        # Получаем список принтеров
        result = subprocess.run(
            ['lpstat', '-p', '-d'],
            capture_output=True,
            text=True,
            check=True
        )

        print(result.stdout)

        if not result.stdout.strip():
            print("❌ Принтеры не найдены")
            print("\nУстановите CUPS и добавьте принтеры:")
            print("  sudo apt-get install cups")
            print("  Откройте http://localhost:631 для настройки")
            return

        print("\n" + "=" * 60)
        print("Как использовать:")
        print("=" * 60)
        print("\n1. Найдите имя нужного принтера в списке выше")
        print("   (например: 'HP_LaserJet' или 'Brother_Printer')")
        print("\n2. Добавьте его в файл .env:")
        print("   PRINTER_NAME=имя_принтера")
        print("\n3. Или оставьте пустым для использования принтера по умолчанию:")
        print("   PRINTER_NAME=")
        print("\n4. Включите печать:")
        print("   ENABLE_PRINTING=true")
        print("\n5. Перезапустите сервер")
        print("=" * 60)

    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка: {e.stderr}")
        print("\nВозможно, CUPS не установлен.")
        print("Установите: sudo apt-get install cups")
    except FileNotFoundError:
        print("❌ Команда lpstat не найдена")
        print("\nУстановите CUPS:")
        print("  Ubuntu/Debian: sudo apt-get install cups")
        print("  macOS: CUPS уже установлен")
        print("  Windows: Используйте WSL или установите CUPS")


def test_print(printer_name=None):
    """Тестовая печать"""
    print("\n" + "=" * 60)
    print("Тестовая печать")
    print("=" * 60)

    # Создаём временный тестовый файл
    import tempfile
    from PIL import Image, ImageDraw, ImageFont

    # Создаём простое изображение
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)

    draw.rectangle([10, 10, 390, 190], outline='black', width=3)
    draw.text((50, 80), "Тестовая печать", fill='black')
    draw.text((50, 120), "Test print", fill='black')

    # Сохраняем во временный файл
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        temp_path = f.name
        img.save(temp_path)

    try:
        if printer_name:
            cmd = ['lp', '-d', printer_name, temp_path]
            print(f"Печать на принтер: {printer_name}")
        else:
            cmd = ['lp', temp_path]
            print("Печать на принтер по умолчанию")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        print(f"✅ Успешно! {result.stdout}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка печати: {e.stderr}")
    except FileNotFoundError:
        print("❌ Команда lp не найдена. Установите CUPS.")
    finally:
        # Удаляем временный файл
        import os
        os.unlink(temp_path)


if __name__ == "__main__":
    list_printers()

    # Если передан аргумент --test, делаем тестовую печать
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        if len(sys.argv) > 2:
            # Печать на конкретный принтер
            test_print(sys.argv[2])
        else:
            # Печать на принтер по умолчанию
            test_print()
