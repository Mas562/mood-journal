#!/usr/bin/env python3
"""
MoodJournal — Умный дневник с анализом настроения
Точка входа в приложение
"""

import sys
import os

# Добавляем пути
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import MoodJournalApp


def main():
    """Запуск приложения"""
    app = MoodJournalApp()
    app.run()


if __name__ == "__main__":
    main()