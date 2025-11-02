from openai import OpenAI
import requests
from config import Config
import os
from datetime import datetime


class ImageGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)

    def generate_coloring_page(self, subject: str) -> tuple[str, str]:
        """
        Генерирует раскраску через DALL-E 3
        """
        prompt = self._create_coloring_prompt(subject)

        print(f"Generating image with prompt: {prompt}")

        try:
            # Используем DALL-E 3 (проверенное API)
            response = self.client.images.generate(
                model="dall-e-3",  # или "dall-e-2" для экономии
                prompt=prompt,
                size="1024x1024",
                quality="standard",  # или "hd" для лучшего качества
                n=1,
            )

            image_url = response.data[0].url
            print(f"Image generated: {image_url}")

            # Скачиваем изображение
            filepath = self._download_image(image_url, subject)

            return filepath, image_url

        except Exception as e:
            print(f"Error generating image: {e}")
            raise

    def _create_coloring_prompt(self, subject: str) -> str:
        """Создает промпт для генерации раскраски"""
        return (
            f"A simple black and white coloring page for children featuring {subject}. "
            f"Style: Bold black outlines only, no colors, no shading, no gradients. "
            f"Pure white background. Thick lines (4-5px width). "
            f"Simple cartoon style with large clear areas perfect for coloring. "
            f"Minimal details suitable for ages 3-8. "
            f"No text, no labels. "
            f"Line art only, like a traditional coloring book page."
        )

    def _download_image(self, url: str, subject: str) -> str:
        """Скачивает изображение по URL"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"coloring_{safe_subject}_{timestamp}.png"
        filepath = os.path.join(Config.OUTPUT_DIR, filename)

        response = requests.get(url)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        print(f"Image saved to: {filepath}")
        return filepath