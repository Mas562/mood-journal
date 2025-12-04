"""
Окно настроек приложения
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from typing import Callable

from src.database import Database
from src.utils import validate_password, hash_password


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

    def __init__(self, parent, db: Database, on_theme_change: Callable = None):
        super().__init__(parent)

        self.db = db
        self.on_theme_change = on_theme_change

        # Настройка окна
        self.title("⚙️ Настройки")
        self.geometry("500x600")
        self.resizable(False, False)

        self.configure(fg_color=self.COLORS['bg_dark'])

        # Делаем окно модальным
        self.transient(parent)
        self.grab_set()

        self._create_ui()
        self._load_settings()

    def _create_ui(self):
        """Создание интерфейса"""
        # Заголовок
        header = ctk.CTkFrame(self, fg_color=self.COLORS['bg_card'], corner_radius=0)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="⚙️ Настройки",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=20)

        # Контент
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # === Внешний вид ===
        self._create_section(content, "🎨 Внешний вид")

        # Тема
        theme_frame = ctk.CTkFrame(content, fg_color=self.COLORS['bg_card'], corner_radius=10)
        theme_frame.pack(fill="x", pady=5)

        theme_content = ctk.CTkFrame(theme_frame, fg_color="transparent")
        theme_content.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            theme_content,
            text="Тема оформления",
            font=ctk.CTkFont(size=14)
        ).pack(side="left")

        self.theme_var = ctk.StringVar(value="dark")
        theme_menu = ctk.CTkOptionMenu(
            theme_content,
            values=["Тёмная", "Светлая", "Системная"],
            variable=self.theme_var,
            width=150,
            fg_color=self.COLORS['bg_input'],
            command=self._on_theme_change
        )
        theme_menu.pack(side="right")

        # === Уведомления ===
        self._create_section(content, "🔔 Уведомления")

        notif_frame = ctk.CTkFrame(content, fg_color=self.COLORS['bg_card'], corner_radius=10)
        notif_frame.pack(fill="x", pady=5)

        notif_content = ctk.CTkFrame(notif_frame, fg_color="transparent")
        notif_content.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            notif_content,
            text="Напоминания о записи",
            font=ctk.CTkFont(size=14)
        ).pack(side="left")

        self.reminder_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            notif_content,
            text="",
            variable=self.reminder_var,
            onvalue=True,
            offvalue=False
        ).pack(side="right")

        # Время напоминания
        time_frame = ctk.CTkFrame(content, fg_color=self.COLORS['bg_card'], corner_radius=10)
        time_frame.pack(fill="x", pady=5)

        time_content = ctk.CTkFrame(time_frame, fg_color="transparent")
        time_content.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            time_content,
            text="Время напоминания",
            font=ctk.CTkFont(size=14)
        ).pack(side="left")

        self.reminder_time = ctk.CTkEntry(
            time_content,
            width=100,
            placeholder_text="21:00",
            fg_color=self.COLORS['bg_input']
        )
        self.reminder_time.pack(side="right")

        # === Безопасность ===
        self._create_section(content, "🔒 Безопасность")

        pass_frame = ctk.CTkFrame(content, fg_color=self.COLORS['bg_card'], corner_radius=10)
        pass_frame.pack(fill="x", pady=5)

        pass_content = ctk.CTkFrame(pass_frame, fg_color="transparent")
        pass_content.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            pass_content,
            text="Защита паролем",
            font=ctk.CTkFont(size=14)
        ).pack(side="left")

        self.password_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(
            pass_content,
            text="",
            variable=self.password_var,
            onvalue=True,
            offvalue=False,
            command=self._toggle_password
        ).pack(side="right")

        # Поле пароля
        self.password_frame = ctk.CTkFrame(content, fg_color=self.COLORS['bg_card'], corner_radius=10)

        pass_input_content = ctk.CTkFrame(self.password_frame, fg_color="transparent")
        pass_input_content.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            pass_input_content,
            text="Пароль:",
            font=ctk.CTkFont(size=14)
        ).pack(side="left")

        self.password_entry = ctk.CTkEntry(
            pass_input_content,
            width=200,
            show="•",
            fg_color=self.COLORS['bg_input']
        )
        self.password_entry.pack(side="right")

        # === Данные ===
        self._create_section(content, "💾 Данные")

        # Экспорт
        export_frame = ctk.CTkFrame(content, fg_color=self.COLORS['bg_card'], corner_radius=10)
        export_frame.pack(fill="x", pady=5)

        export_content = ctk.CTkFrame(export_frame, fg_color="transparent")
        export_content.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            export_content,
            text="Экспорт данных",
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
        clear_frame = ctk.CTkFrame(content, fg_color=self.COLORS['bg_card'], corner_radius=10)
        clear_frame.pack(fill="x", pady=5)

        clear_content = ctk.CTkFrame(clear_frame, fg_color="transparent")
        clear_content.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            clear_content,
            text="Удалить все данные",
            font=ctk.CTkFont(size=14),
            text_color="#FF6B6B"
        ).pack(side="left")

        ctk.CTkButton(
            clear_content,
            text="🗑️ Очистить",
            width=100,
            fg_color="#FF6B6B",
            hover_color="#ff5252",
            command=self._clear_data
        ).pack(side="right")

        # === Кнопка сохранения ===
        ctk.CTkButton(
            self,
            text="💾 Сохранить настройки",
            height=45,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=self.COLORS['success'],
            hover_color="#45b7aa",
            command=self._save_settings
        ).pack(fill="x", padx=20, pady=20)

    def _create_section(self, parent, title: str):
        """Создание заголовка секции"""
        ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.COLORS['text']
        ).pack(anchor="w", pady=(15, 10))

    def _load_settings(self):
        """Загрузка настроек из БД"""
        theme = self.db.get_setting("theme", "dark")
        theme_map = {"dark": "Тёмная", "light": "Светлая", "system": "Системная"}
        self.theme_var.set(theme_map.get(theme, "Тёмная"))

        reminder = self.db.get_setting("reminder_enabled", "true")
        self.reminder_var.set(reminder == "true")

        reminder_time = self.db.get_setting("reminder_time", "21:00")
        self.reminder_time.insert(0, reminder_time)

        password = self.db.get_setting("password_enabled", "false")
        self.password_var.set(password == "true")

        if self.password_var.get():
            self.password_frame.pack(fill="x", pady=5)

    def _on_theme_change(self, value: str):
        """Смена темы"""
        theme_map = {"Тёмная": "dark", "Светлая": "light", "Системная": "system"}
        theme = theme_map.get(value, "dark")

        ctk.set_appearance_mode(theme)

        if self.on_theme_change:
            self.on_theme_change(theme)

    def _toggle_password(self):
        """Переключение защиты паролем"""
        if self.password_var.get():
            self.password_frame.pack(fill="x", pady=5, after=self.password_frame.master.winfo_children()[6])
        else:
            self.password_frame.pack_forget()

    def _export_data(self):
        """Экспорт данных"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Сохранить данные"
        )

        if filepath:
            try:
                self.db.export_to_json(filepath)
                messagebox.showinfo("Успех", f"Данные экспортированы в:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать:\n{e}")

    def _clear_data(self):
        """Очистка всех данных"""
        if messagebox.askyesno(
                "⚠️ Внимание",
                "Вы уверены, что хотите удалить ВСЕ записи?\n\nЭто действие нельзя отменить!"
        ):
            if messagebox.askyesno("Последнее предупреждение", "Точно удалить?"):
                try:
                    self.db.cursor.execute("DELETE FROM entries")
                    self.db.connection.commit()
                    messagebox.showinfo("Готово", "Все записи удалены")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось очистить:\n{e}")

    def _save_settings(self):
        """Сохранение настроек"""
        # Тема
        theme_map = {"Тёмная": "dark", "Светлая": "light", "Системная": "system"}
        theme = theme_map.get(self.theme_var.get(), "dark")
        self.db.set_setting("theme", theme)

        # Напоминания
        self.db.set_setting("reminder_enabled", "true" if self.reminder_var.get() else "false")
        self.db.set_setting("reminder_time", self.reminder_time.get())

        # Пароль
        self.db.set_setting("password_enabled", "true" if self.password_var.get() else "false")
        if self.password_var.get() and self.password_entry.get():
            hashed = hash_password(self.password_entry.get())
            self.db.set_setting("password_hash", hashed)

        messagebox.showinfo("Успех", "Настройки сохранены! ✅")
        self.destroy()