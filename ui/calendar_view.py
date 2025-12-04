"""
Календарное представление записей
"""

import customtkinter as ctk
from datetime import datetime, date, timedelta
import calendar
from typing import Callable

from src.database import Database
from src.emotion_analyzer import EmotionAnalyzer


class CalendarView(ctk.CTkToplevel):
    """Окно календаря"""

    COLORS = {
        'bg_dark': '#1a1a2e',
        'bg_card': '#16213e',
        'bg_input': '#0f3460',
        'accent': '#e94560',
        'text': '#ffffff',
        'text_secondary': '#a0a0a0',
        'success': '#4ECDC4',
        'joy': '#FFD93D',
        'sadness': '#74B9FF',
        'anger': '#FF6B6B',
        'fear': '#9B59B6',
        'surprise': '#F39C12',
        'calm': '#4ECDC4'
    }

    MONTH_NAMES = [
        '', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
        'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
    ]

    DAY_NAMES = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

    def __init__(self, parent, db: Database, analyzer: EmotionAnalyzer,
                 on_date_select: Callable = None):
        super().__init__(parent)

        self.db = db
        self.analyzer = analyzer
        self.on_date_select = on_date_select

        # Текущий отображаемый месяц
        today = date.today()
        self.current_year = today.year
        self.current_month = today.month

        # Настройка окна
        self.title("📅 Календарь настроения")
        self.geometry("700x600")

        self.configure(fg_color=self.COLORS['bg_dark'])

        self._create_ui()
        self._load_month()

    def _create_ui(self):
        """Создание интерфейса"""
        # Навигация
        nav_frame = ctk.CTkFrame(self, fg_color=self.COLORS['bg_card'])
        nav_frame.pack(fill="x", padx=20, pady=20)

        nav_content = ctk.CTkFrame(nav_frame, fg_color="transparent")
        nav_content.pack(pady=15)

        ctk.CTkButton(
            nav_content,
            text="◀",
            width=50,
            height=40,
            fg_color=self.COLORS['bg_input'],
            hover_color=self.COLORS['accent'],
            command=self._prev_month
        ).pack(side="left", padx=10)

        self.month_label = ctk.CTkLabel(
            nav_content,
            text="",
            font=ctk.CTkFont(size=22, weight="bold"),
            width=200
        )
        self.month_label.pack(side="left", padx=20)

        ctk.CTkButton(
            nav_content,
            text="▶",
            width=50,
            height=40,
            fg_color=self.COLORS['bg_input'],
            hover_color=self.COLORS['accent'],
            command=self._next_month
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            nav_content,
            text="Сегодня",
            width=100,
            height=40,
            fg_color=self.COLORS['accent'],
            command=self._go_today
        ).pack(side="left", padx=20)

        # Дни недели
        days_frame = ctk.CTkFrame(self, fg_color="transparent")
        days_frame.pack(fill="x", padx=20)

        for day in self.DAY_NAMES:
            ctk.CTkLabel(
                days_frame,
                text=day,
                font=ctk.CTkFont(size=14, weight="bold"),
                width=85,
                text_color=self.COLORS['text_secondary']
            ).pack(side="left", padx=5)

        # Сетка календаря
        self.calendar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.calendar_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Легенда
        legend_frame = ctk.CTkFrame(self, fg_color=self.COLORS['bg_card'], corner_radius=10)
        legend_frame.pack(fill="x", padx=20, pady=(0, 20))

        legend_content = ctk.CTkFrame(legend_frame, fg_color="transparent")
        legend_content.pack(pady=10)

        emotions = [
            ('joy', 'Радость'), ('calm', 'Спокойствие'), ('sadness', 'Грусть'),
            ('anger', 'Гнев'), ('fear', 'Страх'), ('surprise', 'Удивление')
        ]

        for emotion, name in emotions:
            item = ctk.CTkFrame(legend_content, fg_color="transparent")
            item.pack(side="left", padx=10)

            color_box = ctk.CTkFrame(
                item,
                width=20,
                height=20,
                fg_color=self.COLORS.get(emotion, '#95A5A6'),
                corner_radius=5
            )
            color_box.pack(side="left", padx=(0, 5))
            color_box.pack_propagate(False)

            ctk.CTkLabel(
                item,
                text=name,
                font=ctk.CTkFont(size=11),
                text_color=self.COLORS['text_secondary']
            ).pack(side="left")

    def _load_month(self):
        """Загрузка месяца"""
        # Обновляем заголовок
        self.month_label.configure(
            text=f"{self.MONTH_NAMES[self.current_month]} {self.current_year}"
        )

        # Очищаем сетку
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        # Получаем данные за месяц
        start_date = date(self.current_year, self.current_month, 1)
        if self.current_month == 12:
            end_date = date(self.current_year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(self.current_year, self.current_month + 1, 1) - timedelta(days=1)

        daily_data = self.db.get_daily_mood(start_date, end_date)

        # Создаём словарь данных по дням
        mood_by_day = {}
        for item in daily_data:
            d = item['date']
            if isinstance(d, str):
                d = datetime.strptime(d, "%Y-%m-%d").date()
            mood_by_day[d.day] = item

        # Создаём сетку
        cal = calendar.Calendar()
        weeks = cal.monthdayscalendar(self.current_year, self.current_month)

        today = date.today()

        for week in weeks:
            week_frame = ctk.CTkFrame(self.calendar_frame, fg_color="transparent")
            week_frame.pack(fill="x", pady=2)

            for day in week:
                if day == 0:
                    # Пустая ячейка
                    empty = ctk.CTkFrame(week_frame, width=85, height=70, fg_color="transparent")
                    empty.pack(side="left", padx=5, pady=2)
                    empty.pack_propagate(False)
                else:
                    self._create_day_cell(week_frame, day, mood_by_day.get(day), today)

    def _create_day_cell(self, parent, day: int, mood_data: dict, today: date):
        """Создание ячейки дня"""
        current_date = date(self.current_year, self.current_month, day)
        is_today = current_date == today
        has_entries = mood_data is not None

        # Определяем цвет
        if has_entries:
            emotions = mood_data.get('emotions', 'calm')
            if isinstance(emotions, str):
                # Берём первую эмоцию
                emotion = emotions.split(',')[0].strip()
            else:
                emotion = 'calm'
            bg_color = self.COLORS.get(emotion, self.COLORS['bg_input'])
        else:
            bg_color = self.COLORS['bg_input']

        # Ячейка
        cell = ctk.CTkFrame(
            parent,
            width=85,
            height=70,
            fg_color=bg_color,
            corner_radius=10,
            cursor="hand2" if has_entries else "arrow"
        )
        cell.pack(side="left", padx=5, pady=2)
        cell.pack_propagate(False)

        # Рамка для сегодняшнего дня
        if is_today:
            cell.configure(border_width=3, border_color=self.COLORS['accent'])

        # Номер дня
        day_label = ctk.CTkLabel(
            cell,
            text=str(day),
            font=ctk.CTkFont(size=18, weight="bold" if has_entries else "normal"),
            text_color="white" if has_entries else self.COLORS['text_secondary']
        )
        day_label.pack(expand=True)

        # Индикатор записей
        if has_entries:
            avg_score = mood_data.get('avg_score', 0.5)
            emoji = self.analyzer.get_emotion_info(emotion)['emoji']

            ctk.CTkLabel(
                cell,
                text=emoji,
                font=ctk.CTkFont(size=16)
            ).pack(pady=(0, 5))

        # Клик
        if has_entries or current_date <= today:
            def on_click(e, d=current_date):
                if self.on_date_select:
                    self.on_date_select(d)
                self.destroy()

            cell.bind("<Button-1>", on_click)
            day_label.bind("<Button-1>", on_click)

    def _prev_month(self):
        """Предыдущий месяц"""
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._load_month()

    def _next_month(self):
        """Следующий месяц"""
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._load_month()

    def _go_today(self):
        """Переход к текущему месяцу"""
        today = date.today()
        self.current_year = today.year
        self.current_month = today.month
        self._load_month()