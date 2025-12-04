"""
Модуль для работы с базой данных SQLite
"""

import sqlite3
import os
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import json


class Database:
    """Класс для управления базой данных дневника"""

    def __init__(self, db_path: str = "data/journal.db"):
        """Инициализация подключения к БД"""
        # Создаём папку data если её нет
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

        self._create_tables()

    def _create_tables(self):
        """Создание таблиц в БД"""
        # Таблица записей дневника
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                time TIME NOT NULL,
                content TEXT NOT NULL,
                emotion TEXT DEFAULT 'neutral',
                emotion_score REAL DEFAULT 0.5,
                tags TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица настроек
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Индексы для быстрого поиска
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entries_date ON entries(date)
        """)

        self.connection.commit()

    # ===== CRUD операции для записей =====

    def add_entry(self, content: str, emotion: str, emotion_score: float,
                  tags: List[str] = None, entry_date: date = None) -> int:
        """Добавление новой записи"""
        if entry_date is None:
            entry_date = date.today()

        current_time = datetime.now().strftime("%H:%M:%S")
        tags_str = ",".join(tags) if tags else ""

        self.cursor.execute("""
            INSERT INTO entries (date, time, content, emotion, emotion_score, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (entry_date, current_time, content, emotion, emotion_score, tags_str))

        self.connection.commit()
        return self.cursor.lastrowid

    def update_entry(self, entry_id: int, content: str = None,
                     emotion: str = None, emotion_score: float = None,
                     tags: List[str] = None) -> bool:
        """Обновление записи"""
        updates = []
        values = []

        if content is not None:
            updates.append("content = ?")
            values.append(content)
        if emotion is not None:
            updates.append("emotion = ?")
            values.append(emotion)
        if emotion_score is not None:
            updates.append("emotion_score = ?")
            values.append(emotion_score)
        if tags is not None:
            updates.append("tags = ?")
            values.append(",".join(tags))

        if not updates:
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(entry_id)

        query = f"UPDATE entries SET {', '.join(updates)} WHERE id = ?"
        self.cursor.execute(query, values)
        self.connection.commit()

        return self.cursor.rowcount > 0

    def delete_entry(self, entry_id: int) -> bool:
        """Удаление записи"""
        self.cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        self.connection.commit()
        return self.cursor.rowcount > 0

    def get_entry(self, entry_id: int) -> Optional[Dict[str, Any]]:
        """Получение записи по ID"""
        self.cursor.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_entries_by_date(self, entry_date: date) -> List[Dict[str, Any]]:
        """Получение записей за определённую дату"""
        self.cursor.execute(
            "SELECT * FROM entries WHERE date = ? ORDER BY time DESC",
            (entry_date,)
        )
        return [dict(row) for row in self.cursor.fetchall()]

    def get_entries_range(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Получение записей за период"""
        self.cursor.execute("""
            SELECT * FROM entries 
            WHERE date BETWEEN ? AND ? 
            ORDER BY date DESC, time DESC
        """, (start_date, end_date))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_all_entries(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Получение всех записей с пагинацией"""
        self.cursor.execute("""
            SELECT * FROM entries 
            ORDER BY date DESC, time DESC 
            LIMIT ? OFFSET ?
        """, (limit, offset))
        return [dict(row) for row in self.cursor.fetchall()]

    def search_entries(self, query: str) -> List[Dict[str, Any]]:
        """Поиск по записям"""
        search_pattern = f"%{query}%"
        self.cursor.execute("""
            SELECT * FROM entries 
            WHERE content LIKE ? OR tags LIKE ?
            ORDER BY date DESC, time DESC
        """, (search_pattern, search_pattern))
        return [dict(row) for row in self.cursor.fetchall()]

    # ===== Статистика =====

    def get_emotion_stats(self, start_date: date = None, end_date: date = None) -> Dict[str, int]:
        """Статистика по эмоциям за период"""
        if start_date and end_date:
            self.cursor.execute("""
                SELECT emotion, COUNT(*) as count 
                FROM entries 
                WHERE date BETWEEN ? AND ?
                GROUP BY emotion
            """, (start_date, end_date))
        else:
            self.cursor.execute("""
                SELECT emotion, COUNT(*) as count 
                FROM entries 
                GROUP BY emotion
            """)

        return {row['emotion']: row['count'] for row in self.cursor.fetchall()}

    def get_daily_mood(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Среднее настроение по дням"""
        self.cursor.execute("""
            SELECT date, AVG(emotion_score) as avg_score, 
                   GROUP_CONCAT(emotion) as emotions
            FROM entries 
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        """, (start_date, end_date))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_total_entries(self) -> int:
        """Общее количество записей"""
        self.cursor.execute("SELECT COUNT(*) FROM entries")
        return self.cursor.fetchone()[0]

    def get_streak(self) -> int:
        """Текущая серия дней с записями"""
        self.cursor.execute("""
            SELECT DISTINCT date FROM entries ORDER BY date DESC
        """)
        dates = [row['date'] for row in self.cursor.fetchall()]

        if not dates:
            return 0

        streak = 0
        today = date.today()

        for i, d in enumerate(dates):
            # Преобразуем строку в date если нужно
            if isinstance(d, str):
                d = datetime.strptime(d, "%Y-%m-%d").date()

            expected_date = today - timedelta(days=i)
            if d == expected_date:
                streak += 1
            else:
                break

        return streak

    # ===== Настройки =====

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Получение настройки"""
        self.cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = self.cursor.fetchone()
        return row['value'] if row else default

    def set_setting(self, key: str, value: str):
        """Сохранение настройки"""
        self.cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        """, (key, value))
        self.connection.commit()

    # ===== Экспорт/Импорт =====

    def export_to_json(self, filepath: str):
        """Экспорт всех данных в JSON"""
        entries = self.get_all_entries(limit=10000)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2, default=str)

    def close(self):
        """Закрытие соединения с БД"""
        self.connection.close()


# Импорт для streak
from datetime import timedelta