"""
Модуль для создания графиков и визуализаций
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import numpy as np


class ChartGenerator:
    """Генератор графиков для визуализации настроения"""

    # Цвета эмоций
    EMOTION_COLORS = {
        'joy': '#FFD93D',
        'sadness': '#74B9FF',
        'anger': '#FF6B6B',
        'fear': '#9B59B6',
        'surprise': '#F39C12',
        'calm': '#4ECDC4'
    }

    EMOTION_NAMES = {
        'joy': 'Радость',
        'sadness': 'Грусть',
        'anger': 'Гнев',
        'fear': 'Страх',
        'surprise': 'Удивление',
        'calm': 'Спокойствие'
    }

    def __init__(self, dark_mode: bool = False):
        """Инициализация генератора"""
        self.dark_mode = dark_mode
        self._setup_style()

    def _setup_style(self):
        """Настройка стиля графиков"""
        if self.dark_mode:
            self.bg_color = '#1a1a2e'
            self.text_color = '#ffffff'
            self.grid_color = '#333355'
        else:
            self.bg_color = '#ffffff'
            self.text_color = '#333333'
            self.grid_color = '#dddddd'

    def set_dark_mode(self, enabled: bool):
        """Переключение тёмного режима"""
        self.dark_mode = enabled
        self._setup_style()

    def create_mood_line_chart(self, data: List[Dict[str, Any]],
                                 figsize: tuple = (8, 4)) -> Figure:
        """
        Создание линейного графика настроения по дням

        Args:
            data: Список словарей с ключами 'date' и 'avg_score'
            figsize: Размер фигуры

        Returns:
            Matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=figsize, facecolor=self.bg_color)
        ax.set_facecolor(self.bg_color)

        if not data:
            ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center',
                   fontsize=14, color=self.text_color, transform=ax.transAxes)
            return fig

        # Подготовка данных
        dates = []
        scores = []
        colors = []

        for item in data:
            d = item['date']
            if isinstance(d, str):
                d = datetime.strptime(d, "%Y-%m-%d").date()
            dates.append(d)
            scores.append(item['avg_score'])

            # Определяем цвет по скору
            if item['avg_score'] >= 0.7:
                colors.append(self.EMOTION_COLORS['joy'])
            elif item['avg_score'] >= 0.5:
                colors.append(self.EMOTION_COLORS['calm'])
            elif item['avg_score'] >= 0.3:
                colors.append(self.EMOTION_COLORS['sadness'])
            else:
                colors.append(self.EMOTION_COLORS['anger'])

        # Рисуем линию
        ax.plot(dates, scores, color='#4ECDC4', linewidth=2, alpha=0.8)

        # Рисуем точки
        ax.scatter(dates, scores, c=colors, s=80, zorder=5, edgecolors='white', linewidths=2)

        # Заливка под линией
        ax.fill_between(dates, scores, alpha=0.2, color='#4ECDC4')

        # Настройка осей
        ax.set_ylim(0, 1)
        ax.set_ylabel('Настроение', color=self.text_color, fontsize=11)
        ax.set_xlabel('Дата', color=self.text_color, fontsize=11)

        # Форматирование дат
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates) // 7)))

        # Сетка
        ax.grid(True, alpha=0.3, color=self.grid_color)

        # Цвет текста на осях
        ax.tick_params(colors=self.text_color)
        for spine in ax.spines.values():
            spine.set_color(self.grid_color)

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        return fig

    def create_emotion_pie_chart(self, stats: Dict[str, int],
                                   figsize: tuple = (6, 6)) -> Figure:
        """
        Создание круговой диаграммы эмоций

        Args:
            stats: Словарь {эмоция: количество}
            figsize: Размер фигуры

        Returns:
            Matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=figsize, facecolor=self.bg_color)

        if not stats or sum(stats.values()) == 0:
            ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center',
                   fontsize=14, color=self.text_color, transform=ax.transAxes)
            ax.set_facecolor(self.bg_color)
            return fig

        # Подготовка данных
        emotions = list(stats.keys())
        values = list(stats.values())
        colors = [self.EMOTION_COLORS.get(e, '#95A5A6') for e in emotions]
        labels = [self.EMOTION_NAMES.get(e, e) for e in emotions]

        # Создаём пирог
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            explode=[0.02] * len(values),
            shadow=True
        )

        # Стилизация текста
        for text in texts:
            text.set_color(self.text_color)
            text.set_fontsize(11)

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)

        ax.set_facecolor(self.bg_color)

        return fig

    def create_emotion_bar_chart(self, stats: Dict[str, int],
                                   figsize: tuple = (8, 4)) -> Figure:
        """
        Создание столбчатой диаграммы эмоций
        """
        fig, ax = plt.subplots(figsize=figsize, facecolor=self.bg_color)
        ax.set_facecolor(self.bg_color)

        if not stats:
            ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center',
                   fontsize=14, color=self.text_color, transform=ax.transAxes)
            return fig

        emotions = list(stats.keys())
        values = list(stats.values())
        colors = [self.EMOTION_COLORS.get(e, '#95A5A6') for e in emotions]
        labels = [self.EMOTION_NAMES.get(e, e) for e in emotions]

        bars = ax.bar(labels, values, color=colors, edgecolor='white', linewidth=2)

        # Добавляем значения над столбцами
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value}',
                   ha='center', va='bottom', color=self.text_color, fontweight='bold')

        ax.set_ylabel('Количество записей', color=self.text_color)
        ax.tick_params(colors=self.text_color)

        for spine in ax.spines.values():
            spine.set_color(self.grid_color)

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        return fig

    def create_calendar_heatmap(self, data: List[Dict[str, Any]],
                                  year: int, month: int,
                                  figsize: tuple = (8, 6)) -> Figure:
        """
        Создание тепловой карты-календаря
        """
        fig, ax = plt.subplots(figsize=figsize, facecolor=self.bg_color)
        ax.set_facecolor(self.bg_color)

        # Создаём матрицу для месяца
        import calendar
        cal = calendar.Calendar()

        weeks = cal.monthdayscalendar(year, month)

        # Создаём словарь скоров по датам
        score_map = {}
        for item in data:
            d = item['date']
            if isinstance(d, str):
                d = datetime.strptime(d, "%Y-%m-%d").date()
            score_map[d.day] = item.get('avg_score', 0.5)

        # Рисуем ячейки
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

        for week_idx, week in enumerate(weeks):
            for day_idx, day in enumerate(week):
                if day != 0:
                    score = score_map.get(day, None)

                    if score is not None:
                        # Цвет по скору
                        if score >= 0.7:
                            color = self.EMOTION_COLORS['joy']
                        elif score >= 0.5:
                            color = self.EMOTION_COLORS['calm']
                        elif score >= 0.3:
                            color = self.EMOTION_COLORS['sadness']
                        else:
                            color = self.EMOTION_COLORS['anger']
                    else:
                        color = self.grid_color

                    rect = plt.Rectangle((day_idx, len(weeks) - week_idx - 1),
                                         0.9, 0.9,
                                         facecolor=color,
                                         edgecolor='white',
                                         linewidth=2)
                    ax.add_patch(rect)

                    ax.text(day_idx + 0.45, len(weeks) - week_idx - 0.5,
                           str(day),
                           ha='center', va='center',
                           color='white' if score else self.text_color,
                           fontsize=10, fontweight='bold')

        # Заголовки дней недели
        for i, day in enumerate(days):
            ax.text(i + 0.45, len(weeks) + 0.2, day,
                   ha='center', va='center', color=self.text_color, fontsize=10)

        ax.set_xlim(-0.1, 7)
        ax.set_ylim(-0.1, len(weeks) + 0.6)
        ax.set_aspect('equal')
        ax.axis('off')

        # Название месяца
        month_names = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                      'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        ax.set_title(f'{month_names[month]} {year}', color=self.text_color,
                    fontsize=14, fontweight='bold', pad=10)

        plt.tight_layout()
        return fig

    def embed_in_tkinter(self, fig: Figure, parent) -> FigureCanvasTkAgg:
        """
        Встраивание графика в Tkinter виджет

        Args:
            fig: Matplotlib Figure
            parent: Tkinter родительский виджет

        Returns:
            FigureCanvasTkAgg canvas
        """
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        return canvas