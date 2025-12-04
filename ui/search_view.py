"""
Окно поиска по записям
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable

from src.database import Database
from src.emotion_analyzer import EmotionAnalyzer
from src.utils import format_date, format_time, truncate_text, parse_tags


class SearchWindow(ctk.CTkToplevel):
    """Окно поиска"""

    COLORS = {
        'bg_dark': '#1a1a2e',
        'bg_card': '#16213e',
        'bg_input': '#0f3460',
        'accent': '#e94560',
        'text': '#ffffff',
        'text_secondary': '#a0a0a0',
        'success': '#4ECDC4',
    }

    def __init__(self, parent, db: Database, analyzer: EmotionAnalyzer,
                 on_entry_select: Callable = None):
        super().__init__(parent)

        self.db = db
        self.analyzer = analyzer
        self.on_entry_select = on_entry_select

        # Настройка окна
        self.title("🔍 Поиск")
        self.geometry("600x700")

        self.configure(fg_color=self.COLORS['bg_dark'])

        self._create_ui()

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

        # Привязка Enter
        self.search_entry.bind("<Return>", lambda e: self._search())

        # Фильтры
        filters_frame = ctk.CTkFrame(self, fg_color="transparent")
        filters_frame.pack(fill="x", padx=20)

        ctk.CTkLabel(
            filters_frame,
            text="Фильтр по эмоции:",
            font=ctk.CTkFont(size=13)
        ).pack(side="left")

        self.emotion_filter = ctk.CTkOptionMenu(
            filters_frame,
            values=["Все", "Радость", "Грусть", "Гнев", "Страх", "Удивление", "Спокойствие"],
            width=150,
            fg_color=self.COLORS['bg_input']
        )
        self.emotion_filter.pack(side="left", padx=10)
        self.emotion_filter.set("Все")

        # Результаты
        results_label = ctk.CTkLabel(
            self,
            text="📋 Результаты",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        results_label.pack(anchor="w", padx=20, pady=(20, 10))

        self.results_count = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=self.COLORS['text_secondary']
        )
        self.results_count.pack(anchor="w", padx=20)

        # Список результатов
        self.results_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Показываем последние записи
        self._show_recent()

    def _show_recent(self):
        """Показать последние записи"""
        entries = self.db.get_all_entries(limit=20)
        self._display_results(entries, "Последние записи")

    def _search(self):
        """Выполнение поиска"""
        query = self.search_entry.get().strip()

        if not query:
            self._show_recent()
            return

        entries = self.db.search_entries(query)

        # Фильтр по эмоции
        emotion_filter = self.emotion_filter.get()
        if emotion_filter != "Все":
            emotion_map = {
                "Радость": "joy", "Грусть": "sadness", "Гнев": "anger",
                "Страх": "fear", "Удивление": "surprise", "Спокойствие": "calm"
            }
            emotion = emotion_map.get(emotion_filter)
            if emotion:
                entries = [e for e in entries if e['emotion'] == emotion]

        self._display_results(entries, f"Результаты для: {query}")

    def _display_results(self, entries: list, title: str):
        """Отображение результатов"""
        # Очищаем
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        self.results_count.configure(text=f"{len(entries)} записей найдено")

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

        # Дата
        entry_date = entry['date']
        if isinstance(entry_date, str):
            entry_date = datetime.strptime(entry_date, "%Y-%m-%d").date()

        ctk.CTkLabel(
            header,
            text=f"📅 {format_date(entry_date, full=True)}",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left")

        # Время и эмоция
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

        # Теги
        if entry['tags']:
            tags = parse_tags(entry['tags'])
            tags_text = " ".join([f"#{t}" for t in tags[:5]])
            ctk.CTkLabel(
                content,
                text=tags_text,
                font=ctk.CTkFont(size=11),
                text_color=self.COLORS['accent']
            ).pack(anchor="w", pady=(5, 0))

        # Клик
        entry_id = entry['id']
        entry_date_val = entry['date']

        def on_click(e, eid=entry_id, edate=entry_date_val):
            if self.on_entry_select:
                self.on_entry_select(eid, edate)
            self.destroy()

        card.bind("<Button-1>", on_click)
        for child in card.winfo_children():
            child.bind("<Button-1>", on_click)
            for subchild in child.winfo_children():
                subchild.bind("<Button-1>", on_click)