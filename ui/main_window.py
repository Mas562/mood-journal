"""
Главное окно приложения MoodJournal
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, date, timedelta
from typing import Optional
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.database import Database
from src.emotion_analyzer import EmotionAnalyzer
from src.charts import ChartGenerator
from src.utils import (
    format_date, format_time, parse_tags, tags_to_string,
    get_greeting, get_mood_phrase, truncate_text, get_date_range
)


class MainWindow(ctk.CTk):
    """Главное окно приложения"""

    # Цвета темы
    COLORS = {
        'bg_dark': '#1a1a2e',
        'bg_card': '#16213e',
        'bg_input': '#0f3460',
        'accent': '#e94560',
        'accent_hover': '#ff6b6b',
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

    def __init__(self, db: Database, analyzer: EmotionAnalyzer, charts: ChartGenerator):
        super().__init__()

        self.db = db
        self.analyzer = analyzer
        self.charts = charts

        # Настройка окна
        self.title("📔 MoodJournal — Дневник настроения")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        # Устанавливаем тёмную тему
        self.configure(fg_color=self.COLORS['bg_dark'])

        # Текущий выбранный день
        self.selected_date = date.today()
        self.current_entry_id = None

        # Создаём интерфейс
        self._create_ui()

        # Загружаем данные
        self._load_entries()
        self._update_stats()

    def _create_ui(self):
        """Создание пользовательского интерфейса"""
        # Главный контейнер
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === Левая панель (сайдбар) ===
        self._create_sidebar()

        # === Центральная область ===
        self._create_main_area()

        # === Правая панель (статистика) ===
        self._create_stats_panel()

    def _create_sidebar(self):
        """Создание боковой панели"""
        sidebar = ctk.CTkFrame(self, width=280, corner_radius=0,
                               fg_color=self.COLORS['bg_card'])
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # Лого и заголовок
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            logo_frame,
            text="📔 MoodJournal",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.COLORS['accent']
        ).pack(anchor="w")

        # Приветствие
        self.greeting_label = ctk.CTkLabel(
            logo_frame,
            text=get_greeting(),
            font=ctk.CTkFont(size=14),
            text_color=self.COLORS['text_secondary']
        )
        self.greeting_label.pack(anchor="w", pady=(5, 0))

        # Разделитель
        ctk.CTkFrame(sidebar, height=2, fg_color=self.COLORS['bg_input']).pack(
            fill="x", padx=20, pady=10
        )

        # Навигация по датам
        nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            nav_frame,
            text="📅 Навигация",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        # Кнопки быстрой навигации
        quick_nav = ctk.CTkFrame(nav_frame, fg_color="transparent")
        quick_nav.pack(fill="x")

        ctk.CTkButton(
            quick_nav,
            text="Сегодня",
            width=120,
            height=35,
            fg_color=self.COLORS['accent'],
            hover_color=self.COLORS['accent_hover'],
            command=self._go_to_today
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            quick_nav,
            text="Вчера",
            width=120,
            height=35,
            fg_color=self.COLORS['bg_input'],
            hover_color=self.COLORS['accent'],
            command=self._go_to_yesterday
        ).pack(side="left")

        # Выбор даты
        date_nav = ctk.CTkFrame(nav_frame, fg_color="transparent")
        date_nav.pack(fill="x", pady=15)

        ctk.CTkButton(
            date_nav,
            text="◀",
            width=40,
            fg_color=self.COLORS['bg_input'],
            hover_color=self.COLORS['accent'],
            command=self._prev_day
        ).pack(side="left")

        self.date_label = ctk.CTkLabel(
            date_nav,
            text=format_date(self.selected_date, full=True),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.date_label.pack(side="left", expand=True)

        ctk.CTkButton(
            date_nav,
            text="▶",
            width=40,
            fg_color=self.COLORS['bg_input'],
            hover_color=self.COLORS['accent'],
            command=self._next_day
        ).pack(side="right")

        # Разделитель
        ctk.CTkFrame(sidebar, height=2, fg_color=self.COLORS['bg_input']).pack(
            fill="x", padx=20, pady=10
        )

        # Список записей за день
        entries_label = ctk.CTkFrame(sidebar, fg_color="transparent")
        entries_label.pack(fill="x", padx=20)

        ctk.CTkLabel(
            entries_label,
            text="📝 Записи за день",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        self.entries_count_label = ctk.CTkLabel(
            entries_label,
            text="0",
            font=ctk.CTkFont(size=14),
            text_color=self.COLORS['text_secondary']
        )
        self.entries_count_label.pack(side="right")

        # Скроллируемый список записей
        self.entries_list_frame = ctk.CTkScrollableFrame(
            sidebar,
            fg_color="transparent",
            height=250
        )
        self.entries_list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Кнопка новой записи
        ctk.CTkButton(
            sidebar,
            text="➕ Новая запись",
            height=45,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=self.COLORS['success'],
            hover_color="#45b7aa",
            command=self._new_entry
        ).pack(fill="x", padx=20, pady=(10, 5))

        # Меню кнопок
        menu_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        menu_frame.pack(fill="x", padx=20, pady=(5, 20))

        ctk.CTkButton(
            menu_frame,
            text="🔍 Поиск",
            width=75,
            height=35,
            fg_color=self.COLORS['bg_input'],
            hover_color=self.COLORS['accent'],
            command=self._open_search
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            menu_frame,
            text="📅",
            width=45,
            height=35,
            fg_color=self.COLORS['bg_input'],
            hover_color=self.COLORS['accent'],
            command=self._open_calendar
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            menu_frame,
            text="⚙️",
            width=45,
            height=35,
            fg_color=self.COLORS['bg_input'],
            hover_color=self.COLORS['accent'],
            command=self._open_settings
        ).pack(side="left", padx=2)

    def _create_main_area(self):
        """Создание центральной области"""
        main_frame = ctk.CTkFrame(self, fg_color=self.COLORS['bg_dark'])
        main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # === Заголовок записи ===
        header = ctk.CTkFrame(main_frame, fg_color=self.COLORS['bg_card'], corner_radius=15)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header.grid_columnconfigure(1, weight=1)

        # Эмодзи эмоции
        self.emotion_emoji_label = ctk.CTkLabel(
            header,
            text="📝",
            font=ctk.CTkFont(size=50)
        )
        self.emotion_emoji_label.grid(row=0, column=0, rowspan=2, padx=20, pady=20)

        # Заголовок
        self.entry_title_label = ctk.CTkLabel(
            header,
            text="Новая запись",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.entry_title_label.grid(row=0, column=1, sticky="w", pady=(20, 0))

        # Подзаголовок с эмоцией
        self.emotion_label = ctk.CTkLabel(
            header,
            text="Начните писать, чтобы определить настроение",
            font=ctk.CTkFont(size=14),
            text_color=self.COLORS['text_secondary']
        )
        self.emotion_label.grid(row=1, column=1, sticky="w", pady=(0, 20))

        # Прогресс-бар эмоции
        self.emotion_progress = ctk.CTkProgressBar(
            header,
            width=200,
            height=8,
            progress_color=self.COLORS['calm']
        )
        self.emotion_progress.grid(row=0, column=2, rowspan=2, padx=20)
        self.emotion_progress.set(0.5)

        # === Текстовая область ===
        editor_frame = ctk.CTkFrame(main_frame, fg_color=self.COLORS['bg_card'], corner_radius=15)
        editor_frame.grid(row=1, column=0, sticky="nsew")
        editor_frame.grid_columnconfigure(0, weight=1)
        editor_frame.grid_rowconfigure(0, weight=1)

        # Текстовое поле
        self.text_editor = ctk.CTkTextbox(
            editor_frame,
            font=ctk.CTkFont(size=16),
            fg_color=self.COLORS['bg_input'],
            text_color=self.COLORS['text'],
            corner_radius=10,
            wrap="word"
        )
        self.text_editor.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        # Подсказка
        self.placeholder_text = "Как прошёл ваш день? Что вы чувствуете?\n\nНачните писать здесь..."
        self.text_editor.insert("1.0", self.placeholder_text)
        self.text_editor.configure(text_color=self.COLORS['text_secondary'])

        # Привязка событий
        self.text_editor.bind("<FocusIn>", self._on_text_focus_in)
        self.text_editor.bind("<FocusOut>", self._on_text_focus_out)
        self.text_editor.bind("<KeyRelease>", self._on_text_change)

        # === Нижняя панель ===
        bottom_frame = ctk.CTkFrame(editor_frame, fg_color="transparent")
        bottom_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))

        # Теги
        tags_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        tags_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            tags_frame,
            text="🏷️ Теги:",
            font=ctk.CTkFont(size=13)
        ).pack(side="left")

        self.tags_entry = ctk.CTkEntry(
            tags_frame,
            placeholder_text="работа, отдых, спорт...",
            width=250,
            height=35,
            fg_color=self.COLORS['bg_input']
        )
        self.tags_entry.pack(side="left", padx=10)

        # Кнопки
        buttons_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        buttons_frame.pack(side="right")

        ctk.CTkButton(
            buttons_frame,
            text="🗑️ Удалить",
            width=100,
            height=40,
            fg_color=self.COLORS['anger'],
            hover_color="#ff5252",
            command=self._delete_entry
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            buttons_frame,
            text="💾 Сохранить",
            width=120,
            height=40,
            fg_color=self.COLORS['success'],
            hover_color="#45b7aa",
            font=ctk.CTkFont(weight="bold"),
            command=self._save_entry
        ).pack(side="left", padx=5)

    def _create_stats_panel(self):
        """Создание панели статистики"""
        stats_panel = ctk.CTkFrame(self, width=320, corner_radius=0,
                                   fg_color=self.COLORS['bg_card'])
        stats_panel.grid(row=0, column=2, sticky="nsew")
        stats_panel.grid_propagate(False)

        # Заголовок
        ctk.CTkLabel(
            stats_panel,
            text="📊 Статистика",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)

        # Период
        period_frame = ctk.CTkFrame(stats_panel, fg_color="transparent")
        period_frame.pack(fill="x", padx=15)

        self.period_var = ctk.StringVar(value="week")

        for text, value in [("Неделя", "week"), ("Месяц", "month"), ("Год", "year")]:
            ctk.CTkRadioButton(
                period_frame,
                text=text,
                variable=self.period_var,
                value=value,
                command=self._update_stats
            ).pack(side="left", padx=5)

        # Разделитель
        ctk.CTkFrame(stats_panel, height=2, fg_color=self.COLORS['bg_input']).pack(
            fill="x", padx=15, pady=15
        )

        # Статистические карточки
        stats_cards = ctk.CTkFrame(stats_panel, fg_color="transparent")
        stats_cards.pack(fill="x", padx=15)

        # Всего записей - ИСПРАВЛЕНО: сохраняем ссылку напрямую
        self.total_entries_label = self._create_stat_card(stats_cards, "📝", "Записей", "0")

        # Серия дней
        self.streak_label = self._create_stat_card(stats_cards, "🔥", "Серия дней", "0")

        # Преобладающая эмоция
        self.dominant_emotion_label = self._create_stat_card(stats_cards, "❤️", "Преобладает", "—")

        # Разделитель
        ctk.CTkFrame(stats_panel, height=2, fg_color=self.COLORS['bg_input']).pack(
            fill="x", padx=15, pady=15
        )

        # График настроения
        ctk.CTkLabel(
            stats_panel,
            text="📈 Настроение",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15)

        self.chart_frame = ctk.CTkFrame(stats_panel, fg_color=self.COLORS['bg_input'],
                                        height=200, corner_radius=10)
        self.chart_frame.pack(fill="x", padx=15, pady=10)
        self.chart_frame.pack_propagate(False)

        # Распределение эмоций
        ctk.CTkLabel(
            stats_panel,
            text="🎭 Эмоции",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 0))

        self.pie_frame = ctk.CTkFrame(stats_panel, fg_color=self.COLORS['bg_input'],
                                      height=200, corner_radius=10)
        self.pie_frame.pack(fill="x", padx=15, pady=10)
        self.pie_frame.pack_propagate(False)

        # Фраза дня
        self.mood_phrase_label = ctk.CTkLabel(
            stats_panel,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.COLORS['text_secondary'],
            wraplength=280
        )
        self.mood_phrase_label.pack(pady=15, padx=15)

    def _create_stat_card(self, parent, emoji: str, title: str, value: str) -> ctk.CTkLabel:
        """Создание карточки статистики - ИСПРАВЛЕНО: возвращает label"""
        card = ctk.CTkFrame(parent, fg_color=self.COLORS['bg_input'], corner_radius=10)
        card.pack(fill="x", pady=5)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            content,
            text=f"{emoji} {title}",
            font=ctk.CTkFont(size=13),
            text_color=self.COLORS['text_secondary']
        ).pack(side="left")

        # Создаём label и возвращаем его
        value_label = ctk.CTkLabel(
            content,
            text=value,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        value_label.pack(side="right")

        return value_label

    # ===== Обработчики событий =====

    def _on_text_focus_in(self, event):
        """Фокус на текстовом поле"""
        current = self.text_editor.get("1.0", "end-1c")
        if current == self.placeholder_text:
            self.text_editor.delete("1.0", "end")
            self.text_editor.configure(text_color=self.COLORS['text'])

    def _on_text_focus_out(self, event):
        """Потеря фокуса текстовым полем"""
        current = self.text_editor.get("1.0", "end-1c").strip()
        if not current:
            self.text_editor.insert("1.0", self.placeholder_text)
            self.text_editor.configure(text_color=self.COLORS['text_secondary'])

    def _on_text_change(self, event):
        """Изменение текста — анализ эмоций"""
        text = self.text_editor.get("1.0", "end-1c")

        if text == self.placeholder_text or not text.strip():
            return

        # Анализ эмоций
        result = self.analyzer.analyze(text)

        # Обновляем UI
        emotion_name = EmotionAnalyzer.emotion_to_russian(result['emotion'])

        self.emotion_emoji_label.configure(text=result['emoji'])
        self.emotion_label.configure(
            text=f"{emotion_name}: {int(result['score'] * 100)}%",
            text_color=result['color']
        )
        self.emotion_progress.configure(progress_color=result['color'])
        self.emotion_progress.set(result['score'])

    def _go_to_today(self):
        """Переход к сегодняшнему дню"""
        self.selected_date = date.today()
        self._update_date_display()
        self._load_entries()

    def _go_to_yesterday(self):
        """Переход ко вчерашнему дню"""
        self.selected_date = date.today() - timedelta(days=1)
        self._update_date_display()
        self._load_entries()

    def _prev_day(self):
        """Предыдущий день"""
        self.selected_date -= timedelta(days=1)
        self._update_date_display()
        self._load_entries()

    def _next_day(self):
        """Следующий день"""
        if self.selected_date < date.today():
            self.selected_date += timedelta(days=1)
            self._update_date_display()
            self._load_entries()

    def _update_date_display(self):
        """Обновление отображения даты"""
        self.date_label.configure(text=format_date(self.selected_date, full=True))

    def _load_entries(self):
        """Загрузка записей за выбранный день"""
        # Очищаем список
        for widget in self.entries_list_frame.winfo_children():
            widget.destroy()

        # Получаем записи
        entries = self.db.get_entries_by_date(self.selected_date)
        self.entries_count_label.configure(text=str(len(entries)))

        if not entries:
            ctk.CTkLabel(
                self.entries_list_frame,
                text="Нет записей за этот день",
                text_color=self.COLORS['text_secondary']
            ).pack(pady=20)
            self._new_entry()
            return

        # Отображаем записи
        for entry in entries:
            self._create_entry_card(entry)

        # Выбираем первую запись
        if entries:
            self._select_entry(entries[0]['id'])

    def _create_entry_card(self, entry: dict):
        """Создание карточки записи в списке"""
        emotion_info = self.analyzer.get_emotion_info(entry['emotion'])

        card = ctk.CTkFrame(
            self.entries_list_frame,
            fg_color=self.COLORS['bg_input'],
            corner_radius=10,
            cursor="hand2"
        )
        card.pack(fill="x", pady=5, padx=5)

        # Контент карточки
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=12, pady=10)

        # Верхняя строка: время и эмодзи
        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(
            top_row,
            text=format_time(entry['time']),
            font=ctk.CTkFont(size=12),
            text_color=self.COLORS['text_secondary']
        ).pack(side="left")

        ctk.CTkLabel(
            top_row,
            text=emotion_info['emoji'],
            font=ctk.CTkFont(size=18)
        ).pack(side="right")

        # Превью текста
        preview = truncate_text(entry['content'], 80)
        ctk.CTkLabel(
            content,
            text=preview,
            font=ctk.CTkFont(size=13),
            text_color=self.COLORS['text'],
            anchor="w",
            justify="left",
            wraplength=220
        ).pack(fill="x", pady=(5, 0))

        # Теги если есть
        if entry['tags']:
            tags = parse_tags(entry['tags'])[:3]  # Максимум 3 тега
            tags_text = " ".join([f"#{t}" for t in tags])
            ctk.CTkLabel(
                content,
                text=tags_text,
                font=ctk.CTkFont(size=11),
                text_color=self.COLORS['accent']
            ).pack(anchor="w", pady=(5, 0))

        # Привязка клика
        entry_id = entry['id']
        card.bind("<Button-1>", lambda e, eid=entry_id: self._select_entry(eid))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda e, eid=entry_id: self._select_entry(eid))
            for subchild in child.winfo_children():
                subchild.bind("<Button-1>", lambda e, eid=entry_id: self._select_entry(eid))
                for subsubchild in subchild.winfo_children():
                    subsubchild.bind("<Button-1>", lambda e, eid=entry_id: self._select_entry(eid))

    def _select_entry(self, entry_id: int):
        """Выбор записи для редактирования"""
        entry = self.db.get_entry(entry_id)
        if not entry:
            return

        self.current_entry_id = entry_id

        # Заполняем редактор
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", entry['content'])
        self.text_editor.configure(text_color=self.COLORS['text'])

        # Теги
        self.tags_entry.delete(0, "end")
        if entry['tags']:
            self.tags_entry.insert(0, entry['tags'])

        # Обновляем отображение эмоции
        emotion_info = self.analyzer.get_emotion_info(entry['emotion'])
        emotion_name = EmotionAnalyzer.emotion_to_russian(entry['emotion'])

        self.emotion_emoji_label.configure(text=emotion_info['emoji'])
        self.entry_title_label.configure(text=f"Запись в {format_time(entry['time'])}")
        self.emotion_label.configure(
            text=f"{emotion_name}: {int(entry['emotion_score'] * 100)}%",
            text_color=emotion_info['color']
        )
        self.emotion_progress.configure(progress_color=emotion_info['color'])
        self.emotion_progress.set(entry['emotion_score'])

        # Обновляем фразу
        self.mood_phrase_label.configure(
            text=get_mood_phrase(entry['emotion'], entry['emotion_score'])
        )

    def _new_entry(self):
        """Создание новой записи"""
        self.current_entry_id = None

        # Очищаем редактор
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", self.placeholder_text)
        self.text_editor.configure(text_color=self.COLORS['text_secondary'])

        # Очищаем теги
        self.tags_entry.delete(0, "end")

        # Сбрасываем отображение
        self.emotion_emoji_label.configure(text="📝")
        self.entry_title_label.configure(text="Новая запись")
        self.emotion_label.configure(
            text="Начните писать, чтобы определить настроение",
            text_color=self.COLORS['text_secondary']
        )
        self.emotion_progress.configure(progress_color=self.COLORS['calm'])
        self.emotion_progress.set(0.5)

    def _save_entry(self):
        """Сохранение записи"""
        text = self.text_editor.get("1.0", "end-1c").strip()

        if not text or text == self.placeholder_text:
            messagebox.showwarning("Внимание", "Напишите что-нибудь перед сохранением!")
            return

        # Анализ эмоций
        result = self.analyzer.analyze(text)

        # Теги
        tags_text = self.tags_entry.get().strip()
        tags = parse_tags(tags_text)

        if self.current_entry_id:
            # Обновление существующей записи
            self.db.update_entry(
                self.current_entry_id,
                content=text,
                emotion=result['emotion'],
                emotion_score=result['score'],
                tags=tags
            )
            message = "Запись обновлена! ✅"
        else:
            # Создание новой записи
            self.current_entry_id = self.db.add_entry(
                content=text,
                emotion=result['emotion'],
                emotion_score=result['score'],
                tags=tags,
                entry_date=self.selected_date
            )
            message = "Запись сохранена! ✅"

        # Показываем уведомление
        self._show_notification(message)

        # Обновляем список и статистику
        self._load_entries()
        self._update_stats()

    def _delete_entry(self):
        """Удаление записи"""
        if not self.current_entry_id:
            messagebox.showinfo("Информация", "Нечего удалять")
            return

        if messagebox.askyesno("Подтверждение", "Удалить эту запись?"):
            self.db.delete_entry(self.current_entry_id)
            self._show_notification("Запись удалена! 🗑️")
            self._new_entry()
            self._load_entries()
            self._update_stats()

    def _show_notification(self, message: str):
        """Показ уведомления"""
        notif = ctk.CTkToplevel(self)
        notif.overrideredirect(True)
        notif.attributes("-topmost", True)

        x = self.winfo_x() + self.winfo_width() // 2 - 150
        y = self.winfo_y() + 50
        notif.geometry(f"300x50+{x}+{y}")

        frame = ctk.CTkFrame(notif, fg_color=self.COLORS['success'], corner_radius=10)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        ctk.CTkLabel(
            frame,
            text=message,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white"
        ).pack(expand=True)

        notif.after(2000, notif.destroy)

    def _update_stats(self):
        """Обновление статистики"""
        period = self.period_var.get()
        start_date, end_date = get_date_range(period)

        total = self.db.get_total_entries()
        self.total_entries_label.configure(text=str(total))

        streak = self._calculate_streak()
        self.streak_label.configure(text=str(streak))

        emotion_stats = self.db.get_emotion_stats(start_date, end_date)

        if emotion_stats:
            dominant = max(emotion_stats, key=emotion_stats.get)
            emotion_info = self.analyzer.get_emotion_info(dominant)
            dominant_name = EmotionAnalyzer.emotion_to_russian(dominant)
            self.dominant_emotion_label.configure(
                text=f"{emotion_info['emoji']} {dominant_name}"
            )
        else:
            self.dominant_emotion_label.configure(text="—")

        self._update_charts(start_date, end_date, emotion_stats)

    def _calculate_streak(self) -> int:
        """Расчёт серии дней с записями"""
        today = date.today()
        streak = 0

        for i in range(365):
            check_date = today - timedelta(days=i)
            entries = self.db.get_entries_by_date(check_date)

            if entries:
                streak += 1
            elif i > 0:
                break

        return streak

    def _update_charts(self, start_date: date, end_date: date, emotion_stats: dict):
        """Обновление графиков"""
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        for widget in self.pie_frame.winfo_children():
            widget.destroy()

        daily_data = self.db.get_daily_mood(start_date, end_date)

        if daily_data:
            try:
                fig = self.charts.create_mood_line_chart(daily_data, figsize=(3.5, 1.8))
                canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
                plt.close(fig)
            except Exception as e:
                ctk.CTkLabel(
                    self.chart_frame,
                    text="📈 График появится\nпосле нескольких записей",
                    text_color=self.COLORS['text_secondary']
                ).pack(expand=True)
        else:
            ctk.CTkLabel(
                self.chart_frame,
                text="📈 Нет данных\nза выбранный период",
                text_color=self.COLORS['text_secondary']
            ).pack(expand=True)

        if emotion_stats and sum(emotion_stats.values()) > 0:
            try:
                fig = self.charts.create_emotion_pie_chart(emotion_stats, figsize=(3.5, 1.8))
                canvas = FigureCanvasTkAgg(fig, master=self.pie_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
                plt.close(fig)
            except Exception as e:
                ctk.CTkLabel(
                    self.pie_frame,
                    text="🎭 Диаграмма появится\nпосле нескольких записей",
                    text_color=self.COLORS['text_secondary']
                ).pack(expand=True)
        else:
            ctk.CTkLabel(
                self.pie_frame,
                text="🎭 Нет данных\nза выбранный период",
                text_color=self.COLORS['text_secondary']
            ).pack(expand=True)

    # ===== Дополнительные окна =====

    def _open_search(self):
        """Открытие окна поиска"""
        SearchWindow(
            self,
            self.db,
            self.analyzer,
            on_entry_select=self._on_search_select
        )

    def _on_search_select(self, entry_id: int, entry_date):
        """Обработка выбора записи из поиска"""
        if isinstance(entry_date, str):
            entry_date = datetime.strptime(entry_date, "%Y-%m-%d").date()
        self.selected_date = entry_date
        self._update_date_display()
        self._load_entries()
        self._select_entry(entry_id)

    def _open_calendar(self):
        """Открытие календаря"""
        CalendarWindow(
            self,
            self.db,
            self.analyzer,
            on_date_select=self._on_calendar_select
        )

    def _on_calendar_select(self, selected_date: date):
        """Обработка выбора даты из календаря"""
        self.selected_date = selected_date
        self._update_date_display()
        self._load_entries()

    def _open_settings(self):
        """Открытие настроек"""
        SettingsWindow(
            self,
            self.db,
            on_theme_change=self._on_theme_change
        )

    def _on_theme_change(self, theme: str):
        """Обработка смены темы"""
        self.charts.set_dark_mode(theme == "dark")
        self._update_stats()


# ===== Дополнительные классы окон =====

class SearchWindow(ctk.CTkToplevel):
    """Окно поиска"""

    COLORS = {
        'bg_dark': '#1a1a2e',
        'bg_card': '#16213e',
        'bg_input': '#0f3460',
        'accent': '#e94560',
        'text': '#ffffff',
        'text_secondary': '#a0a0a0',
    }

    def __init__(self, parent, db, analyzer, on_entry_select=None):
        super().__init__(parent)

        self.db = db
        self.analyzer = analyzer
        self.on_entry_select = on_entry_select

        self.title("🔍 Поиск")
        self.geometry("600x700")
        self.configure(fg_color=self.COLORS['bg_dark'])

        self._create_ui()
        self._show_recent()

    def _create_ui(self):
        """Создание интерфейса"""
        # Поле поиска
        search_frame = ctk.CTkFrame(self, fg_color=self.COLORS['bg_card'])
        search_frame.pack(fill="x", padx=20, pady=20)

        search_content = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_content.pack(fill="x", padx=15, pady=15)

        self.search_entry = ctk.CTkEntry(
            search_content,
            placeholder_text="Поиск по тексту или тегам...",
            height=45,
            font=ctk.CTkFont(size=15),
            fg_color=self.COLORS['bg_input']
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            search_content,
            text="🔍",
            width=50,
            height=45,
            fg_color=self.COLORS['accent'],
            command=self._search
        ).pack(side="right")

        self.search_entry.bind("<Return>", lambda e: self._search())

        # Результаты
        self.results_count = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=self.COLORS['text_secondary']
        )
        self.results_count.pack(anchor="w", padx=20, pady=(0, 10))

        self.results_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def _show_recent(self):
        """Показать последние записи"""
        entries = self.db.get_all_entries(limit=20)
        self._display_results(entries)

    def _search(self):
        """Выполнение поиска"""
        query = self.search_entry.get().strip()

        if not query:
            self._show_recent()
            return

        entries = self.db.search_entries(query)
        self._display_results(entries)

    def _display_results(self, entries: list):
        """Отображение результатов"""
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        self.results_count.configure(text=f"Найдено: {len(entries)}")

        if not entries:
            ctk.CTkLabel(
                self.results_frame,
                text="Ничего не найдено 😕",
                font=ctk.CTkFont(size=14),
                text_color=self.COLORS['text_secondary']
            ).pack(pady=50)
            return

        for entry in entries:
            self._create_result_card(entry)

    def _create_result_card(self, entry: dict):
        """Создание карточки результата"""
        emotion_info = self.analyzer.get_emotion_info(entry['emotion'])

        card = ctk.CTkFrame(
            self.results_frame,
            fg_color=self.COLORS['bg_card'],
            corner_radius=10,
            cursor="hand2"
        )
        card.pack(fill="x", pady=5)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=12)

        # Заголовок
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x")

        entry_date = entry['date']
        if isinstance(entry_date, str):
            entry_date = datetime.strptime(entry_date, "%Y-%m-%d").date()

        ctk.CTkLabel(
            header,
            text=f"📅 {format_date(entry_date, full=True)}",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=f"{format_time(entry['time'])} {emotion_info['emoji']}",
            font=ctk.CTkFont(size=13)
        ).pack(side="right")

        # Текст
        preview = truncate_text(entry['content'], 150)
        ctk.CTkLabel(
            content,
            text=preview,
            font=ctk.CTkFont(size=13),
            text_color=self.COLORS['text'],
            anchor="w",
            justify="left",
            wraplength=530
        ).pack(fill="x", pady=(8, 0))

        # Клик
        entry_id = entry['id']
        entry_date_val = entry['date']

        def on_click(e):
            if self.on_entry_select:
                self.on_entry_select(entry_id, entry_date_val)
            self.destroy()

        card.bind("<Button-1>", on_click)
        for child in card.winfo_children():
            child.bind("<Button-1>", on_click)


class CalendarWindow(ctk.CTkToplevel):
    """Окно календаря"""

    COLORS = {
        'bg_dark': '#1a1a2e',
        'bg_card': '#16213e',
        'bg_input': '#0f3460',
        'accent': '#e94560',
        'text': '#ffffff',
        'text_secondary': '#a0a0a0',
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

    def __init__(self, parent, db, analyzer, on_date_select=None):
        super().__init__(parent)

        self.db = db
        self.analyzer = analyzer
        self.on_date_select = on_date_select

        today = date.today()
        self.current_year = today.year
        self.current_month = today.month

        self.title("📅 Календарь настроения")
        self.geometry("700x550")
        self.configure(fg_color=self.COLORS['bg_dark'])

        self._create_ui()
        self._load_month()

    def _create_ui(self):
        """Создание интерфейса"""
        import calendar
        self.cal = calendar

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

    def _load_month(self):
        """Загрузка месяца"""
        import calendar

        self.month_label.configure(
            text=f"{self.MONTH_NAMES[self.current_month]} {self.current_year}"
        )

        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        start_date = date(self.current_year, self.current_month, 1)
        if self.current_month == 12:
            end_date = date(self.current_year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(self.current_year, self.current_month + 1, 1) - timedelta(days=1)

        daily_data = self.db.get_daily_mood(start_date, end_date)

        mood_by_day = {}
        for item in daily_data:
            d = item['date']
            if isinstance(d, str):
                d = datetime.strptime(d, "%Y-%m-%d").date()
            mood_by_day[d.day] = item

        cal = calendar.Calendar()
        weeks = cal.monthdayscalendar(self.current_year, self.current_month)

        today = date.today()

        for week in weeks:
            week_frame = ctk.CTkFrame(self.calendar_frame, fg_color="transparent")
            week_frame.pack(fill="x", pady=2)

            for day in week:
                if day == 0:
                    empty = ctk.CTkFrame(week_frame, width=85, height=60, fg_color="transparent")
                    empty.pack(side="left", padx=5, pady=2)
                    empty.pack_propagate(False)
                else:
                    self._create_day_cell(week_frame, day, mood_by_day.get(day), today)

    def _create_day_cell(self, parent, day: int, mood_data: dict, today: date):
        """Создание ячейки дня"""
        current_date = date(self.current_year, self.current_month, day)
        is_today = current_date == today
        has_entries = mood_data is not None

        if has_entries:
            emotions = mood_data.get('emotions', 'calm')
            if isinstance(emotions, str):
                emotion = emotions.split(',')[0].strip()
            else:
                emotion = 'calm'
            bg_color = self.COLORS.get(emotion, self.COLORS['bg_input'])
        else:
            bg_color = self.COLORS['bg_input']

        cell = ctk.CTkFrame(
            parent,
            width=85,
            height=60,
            fg_color=bg_color,
            corner_radius=10,
            cursor="hand2"
        )
        cell.pack(side="left", padx=5, pady=2)
        cell.pack_propagate(False)

        if is_today:
            cell.configure(border_width=3, border_color=self.COLORS['accent'])

        day_label = ctk.CTkLabel(
            cell,
            text=str(day),
            font=ctk.CTkFont(size=16, weight="bold" if has_entries else "normal"),
            text_color="white" if has_entries else self.COLORS['text_secondary']
        )
        day_label.pack(expand=True)

        if has_entries:
            emoji = self.analyzer.get_emotion_info(emotion)['emoji']
            ctk.CTkLabel(
                cell,
                text=emoji,
                font=ctk.CTkFont(size=14)
            ).pack(pady=(0, 5))

        def on_click(e, d=current_date):
            if self.on_date_select:
                self.on_date_select(d)
            self.destroy()

        cell.bind("<Button-1>", on_click)
        day_label.bind("<Button-1>", on_click)

    def _prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._load_month()

    def _next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._load_month()


class SettingsWindow(ctk.CTkToplevel):
    """Окно настроек"""

    COLORS = {
        'bg_dark': '#1a1a2e',
        'bg_card': '#16213e',
        'bg_input': '#0f3460',
        'accent': '#e94560',
        'text': '#ffffff',
        'text_secondary': '#a0a0a0',
        'success': '#4ECDC4',
    }

    def __init__(self, parent, db, on_theme_change=None):
        super().__init__(parent)

        self.db = db
        self.on_theme_change = on_theme_change

        self.title("⚙️ Настройки")
        self.geometry("450x500")
        self.resizable(False, False)
        self.configure(fg_color=self.COLORS['bg_dark'])

        self.transient(parent)
        self.grab_set()

        self._create_ui()

    def _create_ui(self):
        """Создание интерфейса"""
        # Заголовок
        ctk.CTkLabel(
            self,
            text="⚙️ Настройки",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=20)

        # Тема
        theme_frame = ctk.CTkFrame(self, fg_color=self.COLORS['bg_card'], corner_radius=10)
        theme_frame.pack(fill="x", padx=20, pady=10)

        theme_content = ctk.CTkFrame(theme_frame, fg_color="transparent")
        theme_content.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            theme_content,
            text="🎨 Тема оформления",
            font=ctk.CTkFont(size=14)
        ).pack(side="left")

        self.theme_var = ctk.StringVar(value="Тёмная")
        ctk.CTkOptionMenu(
            theme_content,
            values=["Тёмная", "Светлая", "Системная"],
            variable=self.theme_var,
            width=150,
            fg_color=self.COLORS['bg_input'],
            command=self._change_theme
        ).pack(side="right")

        # Экспорт
        export_frame = ctk.CTkFrame(self, fg_color=self.COLORS['bg_card'], corner_radius=10)
        export_frame.pack(fill="x", padx=20, pady=10)

        export_content = ctk.CTkFrame(export_frame, fg_color="transparent")
        export_content.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            export_content,
            text="💾 Экспорт данных",
            font=ctk.CTkFont(size=14)
        ).pack(side="left")

        ctk.CTkButton(
            export_content,
            text="📤 Экспорт JSON",
            width=130,
            fg_color=self.COLORS['accent'],
            command=self._export_data
        ).pack(side="right")

        # Очистка
        clear_frame = ctk.CTkFrame(self, fg_color=self.COLORS['bg_card'], corner_radius=10)
        clear_frame.pack(fill="x", padx=20, pady=10)

        clear_content = ctk.CTkFrame(clear_frame, fg_color="transparent")
        clear_content.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            clear_content,
            text="🗑️ Удалить все данные",
            font=ctk.CTkFont(size=14),
            text_color="#FF6B6B"
        ).pack(side="left")

        ctk.CTkButton(
            clear_content,
            text="Очистить",
            width=100,
            fg_color="#FF6B6B",
            hover_color="#ff5252",
            command=self._clear_data
        ).pack(side="right")

        # О программе
        about_frame = ctk.CTkFrame(self, fg_color=self.COLORS['bg_card'], corner_radius=10)
        about_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            about_frame,
            text="📔 MoodJournal v1.0\n\nУмный дневник с анализом настроения",
            font=ctk.CTkFont(size=13),
            text_color=self.COLORS['text_secondary']
        ).pack(pady=15)

        # Кнопка закрытия
        ctk.CTkButton(
            self,
            text="✓ Готово",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.COLORS['success'],
            command=self.destroy
        ).pack(fill="x", padx=20, pady=20)

    def _change_theme(self, value: str):
        theme_map = {"Тёмная": "dark", "Светлая": "light", "Системная": "system"}
        theme = theme_map.get(value, "dark")
        ctk.set_appearance_mode(theme)
        if self.on_theme_change:
            self.on_theme_change(theme)

    def _export_data(self):
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Сохранить данные"
        )
        if filepath:
            try:
                self.db.export_to_json(filepath)
                messagebox.showinfo("Успех", f"Данные экспортированы!")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def _clear_data(self):
        if messagebox.askyesno("⚠️ Внимание", "Удалить ВСЕ записи?"):
            try:
                self.db.cursor.execute("DELETE FROM entries")
                self.db.connection.commit()
                messagebox.showinfo("Готово", "Все записи удалены")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))