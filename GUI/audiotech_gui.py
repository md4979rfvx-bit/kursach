# audiotech_gui.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import scrolledtext
from database import Database
from datetime import datetime
import csv
import os

COLORS = {
    'primary': '#800000',
    'primary_dark': '#500000',
    'primary_light': '#A64B4B',
    'secondary': '#1C1C1C',
    'secondary_light': '#2D2D2D',
    'accent': '#D4AF37',
    'text': '#F5F5F5',
    'text_secondary': '#B0B0B0',
    'background': '#121212',
    'success': '#4CAF50',
    'warning': '#FF9800',
    'error': '#F44336'
}


class AudiotechApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Домашняя аудиотека")
        self.root.geometry("1400x800")
        self.root.configure(bg=COLORS['background'])

        # Инициализация БД
        self.db = Database()
        if not self.db.connection:
            messagebox.showerror("Ошибка", "Не удалось подключиться к базе данных")
            self.root.destroy()
            return

        # Текущие данные
        self.current_artist_id = None
        self.current_media_item_id = None
        self.current_release_id = None

        # Создание стилей
        self.setup_styles()

        # Создание интерфейса
        self.create_widgets()

        # Загрузка начальных данных
        self.load_media_items()
        self.update_statistics()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Primary.TButton',
                        background=COLORS['primary'],
                        foreground=COLORS['text'],
                        borderwidth=1,
                        padding=5)

        style.map('Primary.TButton',
                  background=[('active', COLORS['primary_dark']),
                              ('pressed', COLORS['primary_dark'])])

        style.configure('Secondary.TButton',
                        background=COLORS['secondary_light'],
                        foreground=COLORS['text'],
                        borderwidth=1,
                        padding=5)

        style.configure('Treeview',
                        background=COLORS['secondary'],
                        foreground=COLORS['text'],
                        fieldbackground=COLORS['secondary'],
                        rowheight=25)

        style.configure('Treeview.Heading',
                        background=COLORS['primary'],
                        foreground=COLORS['text'],
                        relief='flat',
                        padding=5)

        style.configure('TNotebook',
                        background=COLORS['background'],
                        borderwidth=0)

        style.configure('TNotebook.Tab',
                        background=COLORS['secondary_light'],
                        foreground=COLORS['text_secondary'],
                        padding=[10, 5])

        style.map('TNotebook.Tab',
                  background=[('selected', COLORS['primary'])],
                  foreground=[('selected', COLORS['text'])])

    def create_widgets(self):
        # Верхняя панель
        self.create_header()

        # Основной контейнер с вкладками
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Создание вкладок
        self.create_collection_tab()
        self.create_artists_tab()
        self.create_releases_tab()
        self.create_reports_tab()
        self.create_statistics_tab()

    def create_header(self):
        header = tk.Frame(self.root, bg=COLORS['primary'], height=70)
        header.pack(fill='x')
        header.pack_propagate(False)

        # Логотип
        logo = tk.Label(header,
                        text="🎵 ДОМАШНЯЯ АУДИОТЕКА",
                        font=('Arial', 22, 'bold'),
                        bg=COLORS['primary'],
                        fg=COLORS['text'])
        logo.pack(side='left', padx=20, pady=15)

        # Кнопка экспорта
        export_btn = ttk.Button(header,
                                text="📤 Экспорт данных",
                                style='Primary.TButton',
                                command=self.export_all_data)
        export_btn.pack(side='right', padx=20, pady=10)

        # Статус подключения
        self.status_label = tk.Label(header,
                                     text="✅ Подключено к БД",
                                     font=('Arial', 10),
                                     bg=COLORS['primary'],
                                     fg=COLORS['success'])
        self.status_label.pack(side='right', padx=20)

    # ===== ВКЛАДКА КОЛЛЕКЦИЯ =====
    def create_collection_tab(self):
        self.collection_tab = tk.Frame(self.notebook, bg=COLORS['background'])
        self.notebook.add(self.collection_tab, text='📀 Коллекция')

        # Панель поиска и фильтров
        filter_frame = tk.Frame(self.collection_tab, bg=COLORS['secondary_light'])
        filter_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(filter_frame,
                 text="Поиск:",
                 font=('Arial', 11),
                 bg=COLORS['secondary_light'],
                 fg=COLORS['text']).pack(side='left', padx=10)

        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.load_media_items())
        search_entry = ttk.Entry(filter_frame,
                                 textvariable=self.search_var,
                                 width=40,
                                 font=('Arial', 11))
        search_entry.pack(side='left', padx=5)

        # Кнопки действий
        btn_frame = tk.Frame(filter_frame, bg=COLORS['secondary_light'])
        btn_frame.pack(side='right', padx=10)

        ttk.Button(btn_frame,
                   text="➕ Добавить",
                   style='Primary.TButton',
                   command=self.add_media_item_dialog).pack(side='left', padx=2)

        ttk.Button(btn_frame,
                   text="✏️ Редактировать",
                   style='Primary.TButton',
                   command=self.edit_media_item_dialog).pack(side='left', padx=2)

        ttk.Button(btn_frame,
                   text="🗑️ Удалить",
                   style='Primary.TButton',
                   command=self.delete_media_item).pack(side='left', padx=2)

        ttk.Button(btn_frame,
                   text="🔄 Обновить",
                   style='Secondary.TButton',
                   command=self.load_media_items).pack(side='left', padx=2)

        # Таблица коллекции
        table_frame = tk.Frame(self.collection_tab, bg=COLORS['background'])
        table_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        columns = ('ID', 'Кат. номер', 'Альбом', 'Исполнитель', 'Формат',
                   'Состояние', 'Цена', 'Дата покупки', 'Место хранения')

        self.collection_tree = ttk.Treeview(table_frame,
                                            columns=columns,
                                            show='headings',
                                            height=20)

        for col in columns:
            self.collection_tree.heading(col, text=col)
            self.collection_tree.column(col, width=100)

        self.collection_tree.column('Альбом', width=200)
        self.collection_tree.column('Исполнитель', width=150)
        self.collection_tree.column('Место хранения', width=150)

        scrollbar = ttk.Scrollbar(table_frame,
                                  orient='vertical',
                                  command=self.collection_tree.yview)
        self.collection_tree.configure(yscrollcommand=scrollbar.set)

        self.collection_tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

    # ===== ВКЛАДКА АРТИСТЫ =====
    def create_artists_tab(self):
        self.artists_tab = tk.Frame(self.notebook, bg=COLORS['background'])
        self.notebook.add(self.artists_tab, text='👥 Артисты')

        # Панель управления
        control_frame = tk.Frame(self.artists_tab, bg=COLORS['secondary_light'])
        control_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(control_frame,
                   text="➕ Добавить артиста",
                   style='Primary.TButton',
                   command=self.add_artist_dialog).pack(side='left', padx=5)

        ttk.Button(control_frame,
                   text="✏️ Редактировать",
                   style='Primary.TButton',
                   command=self.edit_artist_dialog).pack(side='left', padx=5)

        ttk.Button(control_frame,
                   text="🗑️ Удалить",
                   style='Primary.TButton',
                   command=self.delete_artist).pack(side='left', padx=5)

        ttk.Button(control_frame,
                   text="📄 Отчет по артисту",
                   style='Primary.TButton',
                   command=self.show_artist_report).pack(side='left', padx=5)

        # Таблица артистов
        table_frame = tk.Frame(self.artists_tab, bg=COLORS['background'])
        table_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        columns = ('ID', 'Имя/Название', 'Тип', 'Страна')

        self.artists_tree = ttk.Treeview(table_frame,
                                         columns=columns,
                                         show='headings',
                                         height=20)

        for col in columns:
            self.artists_tree.heading(col, text=col)
            self.artists_tree.column(col, width=150)

        self.artists_tree.column('Имя/Название', width=250)

        scrollbar = ttk.Scrollbar(table_frame,
                                  orient='vertical',
                                  command=self.artists_tree.yview)
        self.artists_tree.configure(yscrollcommand=scrollbar.set)

        self.artists_tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Загрузка артистов
        self.load_artists()

    # ===== ВКЛАДКА РЕЛИЗЫ =====
    def create_releases_tab(self):
        self.releases_tab = tk.Frame(self.notebook, bg=COLORS['background'])
        self.notebook.add(self.releases_tab, text='🎵 Релизы')

        # Панель управления
        control_frame = tk.Frame(self.releases_tab, bg=COLORS['secondary_light'])
        control_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(control_frame,
                   text="➕ Добавить релиз",
                   style='Primary.TButton',
                   command=self.add_release_dialog).pack(side='left', padx=5)

        # Таблица релизов
        table_frame = tk.Frame(self.releases_tab, bg=COLORS['background'])
        table_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        columns = ('ID', 'Название', 'Год', 'Лейбл', 'Страна', 'Исполнитель')

        self.releases_tree = ttk.Treeview(table_frame,
                                          columns=columns,
                                          show='headings',
                                          height=20)

        for col in columns:
            self.releases_tree.heading(col, text=col)
            self.releases_tree.column(col, width=120)

        self.releases_tree.column('Название', width=200)
        self.releases_tree.column('Исполнитель', width=150)

        scrollbar = ttk.Scrollbar(table_frame,
                                  orient='vertical',
                                  command=self.releases_tree.yview)
        self.releases_tree.configure(yscrollcommand=scrollbar.set)

        self.releases_tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Загрузка релизов
        self.load_releases()

    # ===== ВКЛАДКА ОТЧЕТЫ =====
    def create_reports_tab(self):
        self.reports_tab = tk.Frame(self.notebook, bg=COLORS['background'])
        self.notebook.add(self.reports_tab, text='📊 Отчеты')

        # Панель отчетов
        report_frame = tk.Frame(self.reports_tab, bg=COLORS['background'])
        report_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Кнопки генерации отчетов
        tk.Label(report_frame,
                 text="ГЕНЕРАЦИЯ ОТЧЕТОВ",
                 font=('Arial', 16, 'bold'),
                 bg=COLORS['background'],
                 fg=COLORS['accent']).pack(pady=(0, 20))

        reports = [
            ("📈 Общий отчет по коллекции", self.generate_collection_report),
            ("🎤 Отчет по артистам", self.generate_artists_report),
            ("💿 Отчет по форматам", self.generate_formats_report),
            ("💰 Отчет по стоимости", self.generate_value_report),
            ("📅 Отчет по годам покупки", self.generate_purchase_years_report),
        ]

        for text, command in reports:
            btn = ttk.Button(report_frame,
                             text=text,
                             style='Primary.TButton',
                             command=command)
            btn.pack(pady=5, fill='x')

        # Область для вывода отчета
        self.report_text = scrolledtext.ScrolledText(report_frame,
                                                     width=80,
                                                     height=20,
                                                     font=('Consolas', 10),
                                                     bg=COLORS['secondary'],
                                                     fg=COLORS['text'])
        self.report_text.pack(pady=20, fill='both', expand=True)

        # Кнопки экспорта
        export_frame = tk.Frame(report_frame, bg=COLORS['background'])
        export_frame.pack(fill='x')

        ttk.Button(export_frame,
                   text="💾 Сохранить в файл",
                   style='Primary.TButton',
                   command=self.save_report_to_file).pack(side='left', padx=5)

        ttk.Button(export_frame,
                   text="📄 Экспорт в CSV",
                   style='Primary.TButton',
                   command=self.export_report_csv).pack(side='left', padx=5)

        ttk.Button(export_frame,
                   text="🧹 Очистить",
                   style='Secondary.TButton',
                   command=lambda: self.report_text.delete(1.0, tk.END)).pack(side='right', padx=5)

    # ===== ВКЛАДКА СТАТИСТИКА =====
    def create_statistics_tab(self):
        self.stats_tab = tk.Frame(self.notebook, bg=COLORS['background'])
        self.notebook.add(self.stats_tab, text='📈 Статистика')

        # Статистические данные
        stats_frame = tk.Frame(self.stats_tab, bg=COLORS['background'])
        stats_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Заголовок
        tk.Label(stats_frame,
                 text="СТАТИСТИКА КОЛЛЕКЦИИ",
                 font=('Arial', 18, 'bold'),
                 bg=COLORS['background'],
                 fg=COLORS['accent']).pack(pady=(0, 30))

        # Статистические карточки
        cards_frame = tk.Frame(stats_frame, bg=COLORS['background'])
        cards_frame.pack(fill='x', pady=10)

        self.stats_cards = {}

        card_data = [
            ('Всего носителей', 'total_items', '#800000'),
            ('Общая стоимость', 'total_value', '#4CAF50'),
            ('Артистов', 'artists_count', '#2196F3'),
            ('Релизов', 'releases_count', '#9C27B0'),
        ]

        for i, (title, key, color) in enumerate(card_data):
            card = tk.Frame(cards_frame,
                            bg=color,
                            relief='raised',
                            borderwidth=2)
            card.grid(row=0, column=i, padx=10, sticky='nsew')

            tk.Label(card,
                     text=title,
                     font=('Arial', 12),
                     bg=color,
                     fg='white').pack(pady=(10, 5))

            value_label = tk.Label(card,
                                   text="0",
                                   font=('Arial', 24, 'bold'),
                                   bg=color,
                                   fg='white')
            value_label.pack(pady=(5, 10))

            self.stats_cards[key] = value_label

        cards_frame.grid_columnconfigure(list(range(len(card_data))), weight=1)

        # Диаграммы статистики
        charts_frame = tk.Frame(stats_frame, bg=COLORS['background'])
        charts_frame.pack(fill='both', expand=True, pady=20)

        # Левая панель - по форматам
        left_frame = tk.Frame(charts_frame, bg=COLORS['secondary_light'])
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        tk.Label(left_frame,
                 text="📀 Распределение по форматам",
                 font=('Arial', 14, 'bold'),
                 bg=COLORS['secondary_light'],
                 fg=COLORS['text']).pack(pady=10)

        self.format_tree = ttk.Treeview(left_frame,
                                        columns=('Формат', 'Количество', '%'),
                                        show='headings',
                                        height=10)

        for col in ('Формат', 'Количество', '%'):
            self.format_tree.heading(col, text=col)
            self.format_tree.column(col, width=100)

        self.format_tree.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Правая панель - по состоянию
        right_frame = tk.Frame(charts_frame, bg=COLORS['secondary_light'])
        right_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))

        tk.Label(right_frame,
                 text="🔍 Распределение по состоянию",
                 font=('Arial', 14, 'bold'),
                 bg=COLORS['secondary_light'],
                 fg=COLORS['text']).pack(pady=10)

        self.condition_tree = ttk.Treeview(right_frame,
                                           columns=('Состояние', 'Количество', '%'),
                                           show='headings',
                                           height=10)

        for col in ('Состояние', 'Количество', '%'):
            self.condition_tree.heading(col, text=col)
            self.condition_tree.column(col, width=100)

        self.condition_tree.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Кнопка обновления
        ttk.Button(stats_frame,
                   text="🔄 Обновить статистику",
                   style='Primary.TButton',
                   command=self.update_statistics).pack(pady=20)

    # ===== МЕТОДЫ ДЛЯ КОЛЛЕКЦИИ =====
    def load_media_items(self):
        for item in self.collection_tree.get_children():
            self.collection_tree.delete(item)

        search = self.search_var.get() if self.search_var.get() else None
        items = self.db.get_all_media_items(search)

        for item in items:
            price = f"{item[6]:.2f} ₽" if item[6] else "—"
            self.collection_tree.insert('', 'end', values=item)

    def add_media_item_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить носитель")
        dialog.geometry("500x600")
        dialog.configure(bg=COLORS['background'])

        # Получаем справочники
        media_types = self.db.get_all_media_types()
        releases = self.db.get_all_releases()

        tk.Label(dialog,
                 text="ДОБАВЛЕНИЕ НОСИТЕЛЯ",
                 font=('Arial', 14, 'bold'),
                 bg=COLORS['background'],
                 fg=COLORS['accent']).pack(pady=10)

        # Поля формы
        fields = [
            ("Каталожный номер:", "entry"),
            ("Тип носителя:", "combobox", [t[1] for t in media_types]),
            ("Релиз:", "combobox", [r[1] for r in releases]),
            ("Состояние:", "combobox", ['Новое', 'Хорошее', 'Удовлетворительное', 'Плохое', 'Коллекционное']),
            ("Стоимость:", "entry"),
            ("Дата покупки (ДД.ММ.ГГГГ):", "entry"),
            ("Место хранения:", "entry"),
            ("Примечания:", "text"),
        ]

        entries = {}

        for i, (label, field_type, *options) in enumerate(fields):
            frame = tk.Frame(dialog, bg=COLORS['background'])
            frame.pack(fill='x', padx=20, pady=5)

            tk.Label(frame,
                     text=label,
                     font=('Arial', 11),
                     bg=COLORS['background'],
                     fg=COLORS['text']).pack(side='left', anchor='w')

            if field_type == 'entry':
                entry = ttk.Entry(frame, width=30)
                entry.pack(side='right')
                entries[label] = entry
            elif field_type == 'combobox':
                combo = ttk.Combobox(frame, values=options[0], width=27)
                combo.pack(side='right')
                entries[label] = combo
            elif field_type == 'text':
                text = scrolledtext.ScrolledText(frame, width=30, height=4)
                text.pack(side='right')
                entries[label] = text

        def save():
            try:
                # Получаем значения
                catalog_num = entries["Каталожный номер:"].get()
                media_type_name = entries["Тип носителя:"].get()
                release_title = entries["Релиз:"].get()
                condition = entries["Состояние:"].get()
                price = entries["Стоимость:"].get()
                date_str = entries["Дата покупки (ДД.ММ.ГГГГ):"].get()
                location = entries["Место хранения:"].get()
                notes = entries["Примечания:"].get("1.0", tk.END).strip()

                # Валидация
                if not catalog_num:
                    messagebox.showerror("Ошибка", "Введите каталожный номер")
                    return

                # Получаем ID типа носителя
                media_type_id = None
                for mt in media_types:
                    if mt[1] == media_type_name:
                        media_type_id = mt[0]
                        break

                # Получаем ID релиза
                release_id = None
                for r in releases:
                    if r[1] == release_title:
                        release_id = r[0]
                        break

                # Преобразуем дату
                purchase_date = None
                if date_str:
                    try:
                        purchase_date = datetime.strptime(date_str, "%d.%m.%Y").date()
                    except:
                        messagebox.showerror("Ошибка", "Неправильный формат даты. Используйте ДД.ММ.ГГГГ")
                        return

                # Преобразуем цену
                purchase_price = float(price.replace(',', '.')) if price else None

                # Сохраняем
                item_id = self.db.add_media_item((
                    catalog_num, media_type_id, release_id,
                    condition, purchase_price, purchase_date,
                    location, notes
                ))

                messagebox.showinfo("Успех", f"Носитель добавлен (ID: {item_id})")
                self.load_media_items()
                self.update_statistics()
                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить носитель: {str(e)}")

        # Кнопки
        btn_frame = tk.Frame(dialog, bg=COLORS['background'])
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame,
                   text="💾 Сохранить",
                   style='Primary.TButton',
                   command=save).pack(side='left', padx=10)

        ttk.Button(btn_frame,
                   text="❌ Отмена",
                   command=dialog.destroy).pack(side='left', padx=10)

    def edit_media_item_dialog(self):
        selected = self.collection_tree.selection()
        if not selected:
            messagebox.showwarning("Выбор", "Выберите носитель для редактирования")
            return

        # Получаем данные выбранного элемента
        item_values = self.collection_tree.item(selected[0])['values']
        # TODO: Реализовать редактирование
        messagebox.showinfo("Редактирование", "Функция редактирования в разработке")

    def delete_media_item(self):
        selected = self.collection_tree.selection()
        if not selected:
            messagebox.showwarning("Выбор", "Выберите носитель для удаления")
            return

        item_values = self.collection_tree.item(selected[0])['values']
        item_id = item_values[0]
        item_name = item_values[2]

        if messagebox.askyesno("Подтверждение", f"Удалить носитель '{item_name}'?"):
            try:
                self.db.delete_media_item(item_id)
                messagebox.showinfo("Успех", "Носитель удален")
                self.load_media_items()
                self.update_statistics()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить: {str(e)}")

    # ===== МЕТОДЫ ДЛЯ АРТИСТОВ =====
    def load_artists(self):
        for item in self.artists_tree.get_children():
            self.artists_tree.delete(item)

        artists = self.db.get_all_artists()
        for artist in artists:
            self.artists_tree.insert('', 'end', values=artist)

    def add_artist_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить артиста")
        dialog.geometry("400x300")
        dialog.configure(bg=COLORS['background'])

        tk.Label(dialog,
                 text="ДОБАВЛЕНИЕ АРТИСТА",
                 font=('Arial', 14, 'bold'),
                 bg=COLORS['background'],
                 fg=COLORS['accent']).pack(pady=10)

        # Поля формы
        fields_frame = tk.Frame(dialog, bg=COLORS['background'])
        fields_frame.pack(padx=20, pady=10)

        labels = ['Имя/Название:', 'Тип:', 'Страна:']
        entries = []

        for i, label_text in enumerate(labels):
            tk.Label(fields_frame,
                     text=label_text,
                     font=('Arial', 11),
                     bg=COLORS['background'],
                     fg=COLORS['text']).grid(row=i, column=0, sticky='w', pady=5)

            if label_text == 'Тип:':
                combo = ttk.Combobox(fields_frame,
                                     values=['Solo', 'Band', 'Orchestra', 'Other'],
                                     width=30)
                combo.grid(row=i, column=1, pady=5, padx=10)
                entries.append(combo)
            else:
                entry = ttk.Entry(fields_frame, width=32)
                entry.grid(row=i, column=1, pady=5, padx=10)
                entries.append(entry)

        def save():
            name = entries[0].get()
            artist_type = entries[1].get()
            country = entries[2].get()

            if not name:
                messagebox.showerror("Ошибка", "Введите имя артиста")
                return

            try:
                artist_id = self.db.add_artist(name, artist_type, country)
                messagebox.showinfo("Успех", f"Артист добавлен (ID: {artist_id})")
                self.load_artists()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить артиста: {str(e)}")

        # Кнопки
        btn_frame = tk.Frame(dialog, bg=COLORS['background'])
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame,
                   text="💾 Сохранить",
                   style='Primary.TButton',
                   command=save).pack(side='left', padx=10)

        ttk.Button(btn_frame,
                   text="❌ Отмена",
                   command=dialog.destroy).pack(side='left', padx=10)

    def edit_artist_dialog(self):
        selected = self.artists_tree.selection()
        if not selected:
            messagebox.showwarning("Выбор", "Выберите артиста для редактирования")
            return

        # TODO: Реализовать редактирование артиста
        messagebox.showinfo("Редактирование", "Функция редактирования артиста в разработке")

    def delete_artist(self):
        selected = self.artists_tree.selection()
        if not selected:
            messagebox.showwarning("Выбор", "Выберите артиста для удаления")
            return

        item_values = self.artists_tree.item(selected[0])['values']
        artist_id = item_values[0]
        artist_name = item_values[1]

        if messagebox.askyesno("Подтверждение", f"Удалить артиста '{artist_name}'?"):
            try:
                self.db.delete_artist(artist_id)
                messagebox.showinfo("Успех", "Артист удален")
                self.load_artists()
                self.update_statistics()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить: {str(e)}")

    def show_artist_report(self):
        selected = self.artists_tree.selection()
        if not selected:
            messagebox.showwarning("Выбор", "Выберите артиста для отчета")
            return

        item_values = self.artists_tree.item(selected[0])['values']
        artist_id = item_values[0]
        artist_name = item_values[1]

        # Генерация отчета
        self.generate_artist_report(artist_id, artist_name)
        self.notebook.select(3)  # Переключиться на вкладку отчетов

    # ===== МЕТОДЫ ДЛЯ РЕЛИЗОВ =====
    def load_releases(self):
        for item in self.releases_tree.get_children():
            self.releases_tree.delete(item)

        releases = self.db.get_all_releases()
        for release in releases:
            self.releases_tree.insert('', 'end', values=release)

    def add_release_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить музыкальный релиз")
        dialog.geometry("700x800")
        dialog.configure(bg=COLORS['background'])

        # Получаем данные для выпадающих списков
        artists = self.db.get_all_artists_for_select()
        genres = self.db.get_all_genres_for_select()

        # Список для хранения выбранных артистов и жанров
        selected_artists = []
        selected_genres = []

        tk.Label(dialog,
                 text="ДОБАВЛЕНИЕ МУЗЫКАЛЬНОГО РЕЛИЗА",
                 font=('Arial', 16, 'bold'),
                 bg=COLORS['background'],
                 fg=COLORS['accent']).pack(pady=10)

        # Создаем Notebook для организации формы
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Вкладка 1: Основная информация
        basic_frame = tk.Frame(notebook, bg=COLORS['background'])
        notebook.add(basic_frame, text='📋 Основное')

        # Поля основной информации
        fields_basic = [
            ("Название альбома/сингла:", "entry"),
            ("Год издания:", "entry"),
            ("Оригинальный год:", "entry"),
            ("Лейбл:", "entry"),
            ("Страна:", "entry"),
            ("Каталожный номер:", "entry"),
            ("Общая длительность (сек):", "entry"),
            ("Количество треков:", "entry"),
        ]

        entries_basic = {}
        row = 0

        for label_text, field_type in fields_basic:
            frame = tk.Frame(basic_frame, bg=COLORS['background'])
            frame.grid(row=row, column=0, columnspan=2, sticky='ew', padx=20, pady=5)
            frame.grid_columnconfigure(1, weight=1)

            tk.Label(frame,
                     text=label_text,
                     font=('Arial', 11),
                     bg=COLORS['background'],
                     fg=COLORS['text']).grid(row=0, column=0, sticky='w', padx=(0, 10))

            if field_type == 'entry':
                entry = ttk.Entry(frame, width=40)
                entry.grid(row=0, column=1, sticky='ew', padx=(10, 0))
                entries_basic[label_text] = entry

            row += 1

        # Вкладка 2: Артисты
        artists_frame = tk.Frame(notebook, bg=COLORS['background'])
        notebook.add(artists_frame, text='👥 Артисты')

        tk.Label(artists_frame,
                 text="Выберите артистов, участвующих в релизе:",
                 font=('Arial', 12),
                 bg=COLORS['background'],
                 fg=COLORS['text']).pack(pady=10)

        # Фрейм для списка артистов
        artists_list_frame = tk.Frame(artists_frame, bg=COLORS['secondary_light'])
        artists_list_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Список доступных артистов
        tk.Label(artists_list_frame,
                 text="Доступные артисты:",
                 font=('Arial', 11, 'bold'),
                 bg=COLORS['secondary_light'],
                 fg=COLORS['text']).pack(anchor='w', pady=(10, 5))

        # Treeview для выбора артистов
        columns_artists = ('ID', 'Имя/Название', 'Тип', 'Выбран')
        tree_artists = ttk.Treeview(artists_list_frame,
                                    columns=columns_artists,
                                    show='headings',
                                    height=10)

        for col in columns_artists:
            tree_artists.heading(col, text=col)
            tree_artists.column(col, width=100)

        tree_artists.column('Имя/Название', width=200)
        tree_artists.column('Выбран', width=80)

        # Заполняем список артистов
        for artist in artists:
            artist_id, name, artist_type = artist[0], artist[1], "Группа" if "Band" in str(artist) else "Соло"
            tree_artists.insert('', 'end',
                                values=(artist_id, name, artist_type, "❌"),
                                tags=(artist_id,))

        # Функция для переключения выбора артиста
        def toggle_artist(event):
            item = tree_artists.selection()[0]
            values = tree_artists.item(item)['values']
            artist_id = values[0]

            if values[3] == "✅":
                tree_artists.set(item, 'Выбран', "❌")
                if artist_id in selected_artists:
                    selected_artists.remove(artist_id)
            else:
                tree_artists.set(item, 'Выбран', "✅")
                selected_artists.append(artist_id)

        tree_artists.bind('<Double-Button-1>', toggle_artist)

        scrollbar_artists = ttk.Scrollbar(artists_list_frame,
                                          orient='vertical',
                                          command=tree_artists.yview)
        tree_artists.configure(yscrollcommand=scrollbar_artists.set)

        tree_artists.pack(side='left', fill='both', expand=True)
        scrollbar_artists.pack(side='right', fill='y')

        # Кнопки для артистов
        artists_btn_frame = tk.Frame(artists_frame, bg=COLORS['background'])
        artists_btn_frame.pack(pady=10)

        def select_all_artists():
            for item in tree_artists.get_children():
                values = tree_artists.item(item)['values']
                artist_id = values[0]
                if values[3] != "✅":
                    tree_artists.set(item, 'Выбран', "✅")
                    if artist_id not in selected_artists:
                        selected_artists.append(artist_id)

        def clear_all_artists():
            for item in tree_artists.get_children():
                values = tree_artists.item(item)['values']
                artist_id = values[0]
                tree_artists.set(item, 'Выбран', "❌")
                if artist_id in selected_artists:
                    selected_artists.remove(artist_id)

        ttk.Button(artists_btn_frame,
                   text="✅ Выбрать всех",
                   style='Primary.TButton',
                   command=select_all_artists).pack(side='left', padx=5)

        ttk.Button(artists_btn_frame,
                   text="❌ Очистить всех",
                   style='Secondary.TButton',
                   command=clear_all_artists).pack(side='left', padx=5)

        # Вкладка 3: Жанры
        genres_frame = tk.Frame(notebook, bg=COLORS['background'])
        notebook.add(genres_frame, text='🏷️ Жанры')

        tk.Label(genres_frame,
                 text="Выберите жанры релиза:",
                 font=('Arial', 12),
                 bg=COLORS['background'],
                 fg=COLORS['text']).pack(pady=10)

        # Фрейм для списка жанров
        genres_list_frame = tk.Frame(genres_frame, bg=COLORS['secondary_light'])
        genres_list_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Список доступных жанров
        tk.Label(genres_list_frame,
                 text="Доступные жанры:",
                 font=('Arial', 11, 'bold'),
                 bg=COLORS['secondary_light'],
                 fg=COLORS['text']).pack(anchor='w', pady=(10, 5))

        # Frame для чекбоксов жанров
        genres_checkbox_frame = tk.Frame(genres_list_frame, bg=COLORS['secondary_light'])
        genres_checkbox_frame.pack(fill='both', expand=True)

        # Создаем чекбоксы для жанров
        genre_vars = {}
        genre_checkboxes = {}

        for i, genre in enumerate(genres):
            genre_id, genre_name = genre
            var = tk.BooleanVar()
            genre_vars[genre_id] = var

            cb = tk.Checkbutton(genres_checkbox_frame,
                                text=genre_name,
                                variable=var,
                                font=('Arial', 11),
                                bg=COLORS['secondary_light'],
                                fg=COLORS['text'],
                                selectcolor=COLORS['primary_light'],
                                activebackground=COLORS['secondary_light'],
                                activeforeground=COLORS['text'],
                                command=lambda gid=genre_id, v=var: self.toggle_genre(gid, v, selected_genres))

            cb.grid(row=i // 3, column=i % 3, sticky='w', padx=10, pady=5)
            genre_checkboxes[genre_id] = cb

        # Кнопки для жанров
        genres_btn_frame = tk.Frame(genres_frame, bg=COLORS['background'])
        genres_btn_frame.pack(pady=10)

        def select_all_genres():
            for genre_id, var in genre_vars.items():
                var.set(True)
                if genre_id not in selected_genres:
                    selected_genres.append(genre_id)

        def clear_all_genres():
            for genre_id, var in genre_vars.items():
                var.set(False)
                if genre_id in selected_genres:
                    selected_genres.remove(genre_id)

        ttk.Button(genres_btn_frame,
                   text="✅ Выбрать все",
                   style='Primary.TButton',
                   command=select_all_genres).pack(side='left', padx=5)

        ttk.Button(genres_btn_frame,
                   text="❌ Очистить все",
                   style='Secondary.TButton',
                   command=clear_all_genres).pack(side='left', padx=5)

        # Метод для переключения жанров
        def toggle_genre(genre_id, var, selected_list):
            if var.get():
                if genre_id not in selected_list:
                    selected_list.append(genre_id)
            else:
                if genre_id in selected_list:
                    selected_list.remove(genre_id)

        # Привязываем метод к классу
        self.toggle_genre = toggle_genre

        # Функция сохранения релиза
        def save_release():
            try:
                # Получаем основные данные
                title = entries_basic["Название альбома/сингла:"].get()
                release_year = entries_basic["Год издания:"].get()
                original_year = entries_basic["Оригинальный год:"].get()
                label = entries_basic["Лейбл:"].get()
                country = entries_basic["Страна:"].get()
                catalog_code = entries_basic["Каталожный номер:"].get()
                total_duration = entries_basic["Общая длительность (сек):"].get()
                total_tracks = entries_basic["Количество треков:"].get()

                # Валидация
                if not title:
                    messagebox.showerror("Ошибка", "Введите название релиза")
                    return

                if not selected_artists:
                    messagebox.showerror("Ошибка", "Выберите хотя бы одного артиста")
                    return

                # Преобразуем числа
                release_year = int(release_year) if release_year else None
                original_year = int(original_year) if original_year else None
                total_duration = int(total_duration) if total_duration else None
                total_tracks = int(total_tracks) if total_tracks else None

                # Подготавливаем данные для БД
                release_data = (
                    title,
                    release_year,
                    original_year,
                    label,
                    country,
                    catalog_code,
                    total_duration,
                    total_tracks
                )

                # Сохраняем в БД
                release_id = self.db.add_release_with_artists_and_genres(
                    release_data,
                    selected_artists,
                    selected_genres
                )

                messagebox.showinfo("Успех",
                                    f"Релиз '{title}' добавлен!\nID: {release_id}\n"
                                    f"Артистов: {len(selected_artists)}\n"
                                    f"Жанров: {len(selected_genres)}")

                # Обновляем списки
                self.load_releases()
                self.update_statistics()
                dialog.destroy()

            except ValueError as e:
                messagebox.showerror("Ошибка", f"Неправильный формат числа: {str(e)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить релиз: {str(e)}")

        # Кнопки сохранения/отмены
        btn_frame = tk.Frame(dialog, bg=COLORS['background'])
        btn_frame.pack(pady=20, padx=20, fill='x')

        ttk.Button(btn_frame,
                   text="💾 Сохранить релиз",
                   style='Primary.TButton',
                   command=save_release).pack(side='left', padx=5)

        ttk.Button(btn_frame,
                   text="📋 Просмотреть данные",
                   style='Secondary.TButton',
                   command=lambda: self.preview_release_data(
                       entries_basic, selected_artists, selected_genres, artists, genres
                   )).pack(side='left', padx=5)

        ttk.Button(btn_frame,
                   text="❌ Отмена",
                   command=dialog.destroy).pack(side='right', padx=5)

    # ===== МЕТОДЫ ДЛЯ ОТЧЕТОВ =====
    def generate_collection_report(self):
        stats = self.db.get_collection_statistics()

        report = "=" * 60 + "\n"
        report += "ОТЧЕТ ПО КОЛЛЕКЦИИ АУДИОТЕКИ\n"
        report += "=" * 60 + "\n\n"

        report += f"Всего носителей в коллекции: {sum(count for _, count in stats['by_format'])}\n"
        report += f"Общая стоимость коллекции: {stats['total_value']:.2f} ₽\n"
        report += f"Количество релизов: {stats['releases_count']}\n"
        report += f"Количество артистов: {stats['artists_count']}\n\n"

        report += "Распределение по форматам:\n"
        report += "-" * 40 + "\n"
        for format_name, count in stats['by_format']:
            report += f"{format_name:25} {count:4d} шт.\n"

        report += "\nРаспределение по состоянию:\n"
        report += "-" * 40 + "\n"
        for condition, count in stats['by_condition']:
            report += f"{condition:25} {count:4d} шт.\n"

        report += "\nПокупки по годам:\n"
        report += "-" * 40 + "\n"
        report += "Год   Кол-во   Сумма\n"
        for year, count, sum_price in stats['by_year']:
            report += f"{int(year)}   {count:6d}   {sum_price or 0:8.2f} ₽\n"

        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(1.0, report)

    def generate_artists_report(self):
        artists_data = self.db.get_artist_report()

        report = "=" * 60 + "\n"
        report += "ОТЧЕТ ПО АРТИСТАМ\n"
        report += "=" * 60 + "\n\n"

        report += f"{'Артист':30} {'Релизов':8} {'Носителей':10} {'Стоимость':12}\n"
        report += "-" * 60 + "\n"

        total_releases = 0
        total_items = 0
        total_value = 0

        for artist in artists_data:
            name = artist[0] or "Неизвестный"
            releases = artist[1] or 0
            items = artist[2] or 0
            value = artist[3] or 0

            report += f"{name:30} {releases:8d} {items:10d} {value:12.2f} ₽\n"

            total_releases += releases
            total_items += items
            total_value += value

        report += "-" * 60 + "\n"
        report += f"{'ИТОГО':30} {total_releases:8d} {total_items:10d} {total_value:12.2f} ₽\n"

        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(1.0, report)

    def generate_artist_report(self, artist_id, artist_name):
        artist_data = self.db.get_artist_report(artist_id)

        report = "=" * 60 + "\n"
        report += f"ОТЧЕТ ПО АРТИСТУ: {artist_name}\n"
        report += "=" * 60 + "\n\n"

        if not artist_data:
            report += "Нет данных по данному артисту\n"
        else:
            report += f"{'Альбом':30} {'Формат':15} {'Состояние':15} {'Цена':10} {'Дата':12}\n"
            report += "-" * 82 + "\n"

            total_value = 0
            for item in artist_data:
                title = item[0] or "Без названия"
                format_name = item[1] or "—"
                condition = item[2] or "—"
                price = f"{item[3]:.2f} ₽" if item[3] else "—"
                date = item[4] or "—"

                report += f"{title:30} {format_name:15} {condition:15} {price:10} {date:12}\n"

                if item[3]:
                    total_value += item[3]

            report += "-" * 82 + "\n"
            report += f"Общая стоимость коллекции артиста: {total_value:.2f} ₽\n"

        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(1.0, report)

    def generate_formats_report(self):
        formats_data = self.db.get_format_report()

        report = "=" * 60 + "\n"
        report += "ОТЧЕТ ПО ФОРМАТАМ НОСИТЕЛЕЙ\n"
        report += "=" * 60 + "\n\n"

        report += f"{'Формат':20} {'Кол-во':8} {'Ср. цена':12} {'Сумма':12} {'Первая':12} {'Последняя':12}\n"
        report += "-" * 76 + "\n"

        total_items = 0
        total_value = 0

        for item in formats_data:
            format_name = item[0] or "Неизвестно"
            count = item[1] or 0
            avg_price = item[2] or 0
            sum_price = item[3] or 0
            first = item[4].strftime("%d.%m.%Y") if item[4] else "—"
            last = item[5].strftime("%d.%m.%Y") if item[5] else "—"

            report += f"{format_name:20} {count:8d} {avg_price:12.2f} ₽ {sum_price:12.2f} ₽ {first:12} {last:12}\n"

            total_items += count
            total_value += sum_price

        report += "-" * 76 + "\n"
        report += f"{'ИТОГО':20} {total_items:8d} {'—':12} {total_value:12.2f} ₽\n"

        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(1.0, report)

    def generate_value_report(self):
        stats = self.db.get_collection_statistics()

        report = "=" * 60 + "\n"
        report += "ОТЧЕТ ПО СТОИМОСТИ КОЛЛЕКЦИИ\n"
        report += "=" * 60 + "\n\n"

        report += f"Общая стоимость коллекции: {stats['total_value']:.2f} ₽\n\n"

        if stats['by_format']:
            report += "Стоимость по форматам:\n"
            report += "-" * 40 + "\n"

            # Нужно получить данные о стоимости по форматам
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT mt.type_name, 
                       COUNT(mi.media_item_id),
                       SUM(mi.purchase_price)
                FROM media_types mt
                LEFT JOIN media_items mi ON mt.media_type_id = mi.media_type_id
                GROUP BY mt.media_type_id, mt.type_name
                ORDER BY SUM(mi.purchase_price) DESC
            """)

            format_values = cursor.fetchall()

            for format_name, count, sum_price in format_values:
                if sum_price:
                    percent = (sum_price / stats['total_value'] * 100) if stats['total_value'] > 0 else 0
                    report += f"{format_name:20} {sum_price:10.2f} ₽ ({percent:.1f}%)\n"

        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(1.0, report)

    def generate_purchase_years_report(self):
        stats = self.db.get_collection_statistics()

        report = "=" * 60 + "\n"
        report += "ОТЧЕТ ПО ГОДАМ ПОКУПКИ\n"
        report += "=" * 60 + "\n\n"

        report += "Год   Кол-во покупок   Сумма покупок   Средний чек\n"
        report += "-" * 60 + "\n"

        total_items = 0
        total_value = 0

        for year, count, sum_price in stats['by_year']:
            avg_price = (sum_price / count) if count > 0 else 0
            report += f"{int(year)}   {count:14d}   {sum_price:13.2f} ₽   {avg_price:11.2f} ₽\n"

            total_items += count
            total_value += sum_price

        report += "-" * 60 + "\n"
        report += f"ИТОГО {total_items:14d}   {total_value:13.2f} ₽\n"

        avg_total = (total_value / total_items) if total_items > 0 else 0
        report += f"Средний чек за все годы: {avg_total:.2f} ₽\n"

        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(1.0, report)

    def save_report_to_file(self):
        report_text = self.report_text.get(1.0, tk.END).strip()
        if not report_text:
            messagebox.showwarning("Пустой отчет", "Нет данных для сохранения")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"отчет_аудиотека_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                messagebox.showinfo("Успех", f"Отчет сохранен в файл:\n{filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")

    def export_report_csv(self):
        report_text = self.report_text.get(1.0, tk.END).strip()
        if not report_text:
            messagebox.showwarning("Пустой отчет", "Нет данных для экспорта")
            return

        # Преобразуем текст отчета в CSV формат
        lines = report_text.split('\n')
        csv_data = []

        for line in lines:
            # Простая логика преобразования
            if '=' in line and len(line.replace('=', '').strip()) == 0:
                continue  # Пропускаем строки с разделителями
            if line.strip():
                # Разделяем по нескольким пробелам
                cells = [cell.strip() for cell in line.split('  ') if cell.strip()]
                if cells:
                    csv_data.append(cells)

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"отчет_аудиотека_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerows(csv_data)
                messagebox.showinfo("Успех", f"Данные экспортированы в CSV:\n{filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать: {str(e)}")

    def export_all_data(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"аудиотека_полная_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        if filename:
            try:
                # Получаем все данные
                media_items = self.db.get_all_media_items()

                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f, delimiter=';')

                    # Заголовок
                    writer.writerow([
                        'ID', 'Каталожный номер', 'Альбом', 'Исполнитель',
                        'Формат', 'Состояние', 'Цена (₽)', 'Дата покупки',
                        'Место хранения'
                    ])

                    # Данные
                    for item in media_items:
                        writer.writerow(item)

                messagebox.showinfo("Успех", f"Все данные экспортированы в:\n{filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать: {str(e)}")

    # ===== МЕТОДЫ ДЛЯ СТАТИСТИКИ =====
    def update_statistics(self):
        stats = self.db.get_collection_statistics()

        # Обновляем карточки
        total_items = sum(count for _, count in stats['by_format'])
        self.stats_cards['total_items'].config(text=str(total_items))
        self.stats_cards['total_value'].config(text=f"{stats['total_value']:.2f} ₽")
        self.stats_cards['artists_count'].config(text=str(stats['artists_count']))
        self.stats_cards['releases_count'].config(text=str(stats['releases_count']))

        # Очищаем таблицы
        for item in self.format_tree.get_children():
            self.format_tree.delete(item)
        for item in self.condition_tree.get_children():
            self.condition_tree.delete(item)

        # Заполняем таблицу форматов
        total_format_items = sum(count for _, count in stats['by_format'])
        for format_name, count in stats['by_format']:
            if total_format_items > 0:
                percent = (count / total_format_items) * 100
            else:
                percent = 0
            self.format_tree.insert('', 'end', values=(format_name, count, f"{percent:.1f}%"))

        # Заполняем таблицу состояний
        total_condition_items = sum(count for _, count in stats['by_condition'])
        for condition, count in stats['by_condition']:
            if total_condition_items > 0:
                percent = (count / total_condition_items) * 100
            else:
                percent = 0
            self.condition_tree.insert('', 'end', values=(condition, count, f"{percent:.1f}%"))

    def on_closing(self):
        if self.db:
            self.db.close()
        self.root.destroy()


def preview_release_data(self, entries, selected_artists, selected_genres, artists_list, genres_list):
    """Предпросмотр данных перед сохранением"""
    preview = "ПРЕДПРОСМОТР ДАННЫХ РЕЛИЗА:\n"
    preview += "=" * 40 + "\n\n"

    # Основные данные
    preview += "📋 ОСНОВНАЯ ИНФОРМАЦИЯ:\n"
    for label, entry in entries.items():
        value = entry.get()
        preview += f"  {label.replace(':', '')}: {value if value else 'Не указано'}\n"

    # Артисты
    preview += "\n👥 АРТИСТЫ:\n"
    if selected_artists:
        for artist_id in selected_artists:
            for artist in artists_list:
                if artist[0] == artist_id:
                    preview += f"  • {artist[1]}\n"
                    break
    else:
        preview += "  Не выбраны\n"

    # Жанры
    preview += "\n🏷️ ЖАНРЫ:\n"
    if selected_genres:
        for genre_id in selected_genres:
            for genre in genres_list:
                if genre[0] == genre_id:
                    preview += f"  • {genre[1]}\n"
                    break
    else:
        preview += "  Не выбраны\n"

    # Показываем в отдельном окне
    preview_dialog = tk.Toplevel(self.root)
    preview_dialog.title("Предпросмотр данных релиза")
    preview_dialog.geometry("500x600")
    preview_dialog.configure(bg=COLORS['background'])

    text_widget = scrolledtext.ScrolledText(preview_dialog,
                                            width=60,
                                            height=25,
                                            font=('Consolas', 10),
                                            bg=COLORS['secondary'],
                                            fg=COLORS['text'])
    text_widget.pack(padx=10, pady=10, fill='both', expand=True)
    text_widget.insert(1.0, preview)
    text_widget.config(state='disabled')

    ttk.Button(preview_dialog,
               text="Закрыть",
               command=preview_dialog.destroy).pack(pady=10)

# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = AudiotechApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
