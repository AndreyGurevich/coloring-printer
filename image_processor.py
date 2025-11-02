import cv2
import numpy as np
from PIL import Image, ImageEnhance


class ImageProcessor:
    @staticmethod
    def enhance_for_coloring(input_path: str, output_path: str = None) -> str:
        """
        Улучшает изображение для раскраски:
        - Усиливает контрастность
        - Делает линии более четкими
        - Убирает серые оттенки

        Args:
            input_path: Путь к исходному изображению
            output_path: Путь для сохранения (опционально)

        Returns:
            str: Путь к обработанному файлу
        """
        if output_path is None:
            output_path = input_path.replace('.png', '_enhanced.png')

        # Открываем изображение через PIL
        img_pil = Image.open(input_path)

        # Конвертируем в grayscale если нужно
        if img_pil.mode != 'L':
            img_pil = img_pil.convert('L')

        # Увеличиваем контрастность
        enhancer = ImageEnhance.Contrast(img_pil)
        img_pil = enhancer.enhance(2.0)  # Усиливаем контраст в 2 раза

        # Конвертируем в numpy для OpenCV
        img_cv = np.array(img_pil)

        # Применяем пороговую обработку (threshold)
        # Все что светлее 200 -> белое, темнее -> черное
        _, img_binary = cv2.threshold(img_cv, 200, 255, cv2.THRESH_BINARY)

        # Опционально: небольшое размытие для сглаживания
        # img_binary = cv2.GaussianBlur(img_binary, (3, 3), 0)

        # Сохраняем
        cv2.imwrite(output_path, img_binary)

        print(f"Enhanced image saved to: {output_path}")
        return output_path

    @staticmethod
    def create_outline_version(input_path: str, output_path: str = None) -> str:
        """
        Создает версию только с контурами (edge detection)

        Args:
            input_path: Путь к исходному изображению
            output_path: Путь для сохранения (опционально)

        Returns:
            str: Путь к обработанному файлу
        """
        if output_path is None:
            output_path = input_path.replace('.png', '_outline.png')

        # Читаем изображение
        img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)

        # Применяем Canny edge detection
        edges = cv2.Canny(img, 50, 150)

        # Инвертируем (чтобы линии были черные на белом)
        edges_inverted = cv2.bitwise_not(edges)

        # Сохраняем
        cv2.imwrite(output_path, edges_inverted)

        print(f"Outline version saved to: {output_path}")
        return output_path