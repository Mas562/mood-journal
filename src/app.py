"""
Главный класс приложения MoodJournal
"""

import customtkinter as ctk
from src.database import Database
from src.emotion_analyzer import EmotionAnalyzer
from src.charts import ChartGenerator
from ui.main_window import MainWindow


class MoodJournalApp:
    """Главный класс приложения"""

    def __init__(self):
        """Инициализация приложения"""
        # Настройка темы
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Инициализация компонентов
        self.db = Database()
        self.analyzer = EmotionAnalyzer()
        self.charts = ChartGenerator(dark_mode=True)

        # Создание главного окна
        self.window = MainWindow(self.db, self.analyzer, self.charts)

    def run(self):
        """Запуск приложения"""
        self.window.mainloop()

        # Закрываем БД при выходе
        self.db.close()