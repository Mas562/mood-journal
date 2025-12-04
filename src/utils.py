"""
Вспомогательные функции и утилиты
"""

from datetime import datetime, date, timedelta
from typing import List, Tuple
import json
import os


def get_date_range(period: str) -> Tuple[date, date]:
    """
    Получение диапазона дат для периода

    Args:
        period: 'week', 'month', 'year', 'all'

    Returns:
        Tuple (start_date, end_date)
    """
    today = date.today()

    if period == 'week':
        start = today - timedelta(days=7)
    elif period == 'month':
        start = today - timedelta(days=30)
    elif period == 'year':
        start = today - timedelta(days=365)
    else:  # all
        start = date(2020, 1, 1)

    return start, today


def format_date(d: date, full: bool = False) -> str:
    """Форматирование даты для отображения"""
    if full:
        months = ['', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
        return f"{d.day} {months[d.month]} {d.year}"
    return d.strftime("%d.%m.%Y")


def format_time(t: str) -> str:
    """Форматирование времени"""
    try:
        time_obj = datetime.strptime(t, "%H:%M:%S")
        return time_obj.strftime("%H:%M")
    except:
        return t


def parse_tags(tags_str: str) -> List[str]:
    """Парсинг строки тегов в список"""
    if not tags_str:
        return []
    return [t.strip() for t in tags_str.split(',') if t.strip()]


def tags_to_string(tags: List[str]) -> str:
    """Конвертация списка тегов в строку"""
    return ', '.join(tags)


def truncate_text(text: str, max_length: int = 100) -> str:
    """Обрезка текста с многоточием"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + '...'


def get_greeting() -> str:
    """Получение приветствия в зависимости от времени суток"""
    hour = datetime.now().hour

    if 5 <= hour < 12:
        return "Доброе утро! ☀️"
    elif 12 <= hour < 18:
        return "Добрый день! 🌤️"
    elif 18 <= hour < 23:
        return "Добрый вечер! 🌙"
    else:
        return "Доброй ночи! 🌃"


def get_mood_phrase(emotion: str, score: float) -> str:
    """Получение фразы на основе эмоции"""
    phrases = {
        'joy': [
            "Отлично! Продолжайте в том же духе! 🌟",
            "Рада, что у вас хорошее настроение! ✨",
            "Замечательный день, не так ли? 🎉"
        ],
        'sadness': [
            "Грустные дни бывают у всех. Это пройдёт. 💙",
            "Помните: после дождя всегда выходит солнце. 🌈",
            "Позвольте себе погрустить, это нормально. 🫂"
        ],
        'anger': [
            "Глубокий вдох... и выдох. Вы справитесь. 🍃",
            "Злость — это нормальная эмоция. Важно её выразить. 💪",
            "Попробуйте прогуляться или сделать паузу. 🚶"
        ],
        'fear': [
            "Страх — это сигнал. Прислушайтесь к себе. 🤗",
            "Вы сильнее, чем думаете. 💜",
            "Шаг за шагом, всё получится. 🌸"
        ],
        'surprise': [
            "Жизнь полна сюрпризов! 🎁",
            "Неожиданности делают жизнь интересной! ✨",
            "Удивительный день, не правда ли? 🌟"
        ],
        'calm': [
            "Спокойствие — это сила. 🧘",
            "Хорошо, когда всё в балансе. ⚖️",
            "Гармония — прекрасное состояние. 🌿"
        ]
    }

    import random
    emotion_phrases = phrases.get(emotion, phrases['calm'])
    return random.choice(emotion_phrases)


def export_to_pdf(entries: List[dict], filepath: str):
    """Экспорт записей в PDF (заглушка — требует reportlab)"""
    # Для полной реализации нужен reportlab
    # pip install reportlab
    pass


def validate_password(password: str) -> Tuple[bool, str]:
    """Валидация пароля"""
    if len(password) < 4:
        return False, "Пароль должен быть не менее 4 символов"
    return True, ""


def hash_password(password: str) -> str:
    """Хеширование пароля"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def check_password(password: str, hashed: str) -> bool:
    """Проверка пароля"""
    return hash_password(password) == hashed