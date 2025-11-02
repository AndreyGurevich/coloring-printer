import subprocess
import platform
from config import Config


class Printer:
    @staticmethod
    def print_image(filepath: str) -> tuple[bool, str]:
        """
        Печатает изображение на принтере по умолчанию

        Args:
            filepath: Путь к файлу для печати

        Returns:
            tuple: (успех, сообщение)
        """
        if not Config.ENABLE_PRINTING:
            message = f"[STUB] Would print: {filepath}"
            print(message)
            return True, message

        system = platform.system()

        try:
            if system == "Windows":
                return Printer._print_windows(filepath)
            elif system == "Linux":
                return Printer._print_linux(filepath)
            elif system == "Darwin":  # macOS
                return Printer._print_macos(filepath)
            else:
                return False, f"Unsupported OS: {system}"
        except Exception as e:
            return False, f"Print error: {str(e)}"

    @staticmethod
    def _print_windows(filepath: str) -> tuple[bool, str]:
        """Печать в Windows"""
        try:
            # Используем стандартную команду Windows
            import os
            os.startfile(filepath, "print")
            return True, f"Sent to default printer (Windows): {filepath}"
        except Exception as e:
            return False, f"Windows print error: {str(e)}"

    @staticmethod
    def _print_linux(filepath: str) -> tuple[bool, str]:
        """Печать в Linux через CUPS"""
        try:
            result = subprocess.run(
                ['lp', filepath],
                capture_output=True,
                text=True,
                check=True
            )
            return True, f"Sent to default printer (Linux): {result.stdout}"
        except subprocess.CalledProcessError as e:
            return False, f"Linux print error: {e.stderr}"

    @staticmethod
    def _print_macos(filepath: str) -> tuple[bool, str]:
        """Печать в macOS"""
        try:
            result = subprocess.run(
                ['lpr', filepath],
                capture_output=True,
                text=True,
                check=True
            )
            return True, f"Sent to default printer (macOS): {result.stdout}"
        except subprocess.CalledProcessError as e:
            return False, f"macOS print error: {e.stderr}"