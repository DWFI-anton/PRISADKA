# ui_components.py
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Tuple, Optional, Callable, Any

from config import (
    TABLE_ROW_HEIGHT, TABLE_COLUMN_WIDTHS,
    LEGEND_ITEM_WIDTH, LEGEND_CIRCLE_SIZE,
    MIN_PANEL_WIDTH, MAX_PANEL_WIDTH,
    MIN_PANEL_HEIGHT, MAX_PANEL_HEIGHT,
    MIN_PANEL_THICKNESS, MAX_PANEL_THICKNESS,
    FONT_NORMAL, FONT_BOLD, FONT_SMALL,
    DEFAULT_PANEL,
    DEFAULT_GROOVE
)


class TableComponent:
    """Компонент таблицы отверстий"""
    
    def __init__(
        self,
        parent: ttk.Frame,
        hole_type: str,
        columns: List[Tuple[str, int]],
        on_select: Optional[Callable] = None,
        on_double_click: Optional[Callable] = None,
        on_right_click: Optional[Callable] = None  # Добавим параметр для правого клика
    ):
        """
        Инициализация компонента таблицы
        
        Args:
            parent: Родительский фрейм
            hole_type: Тип отверстий ("top" или "edge")
            columns: Список колонок (название, ширина)
            on_select: Функция обратного вызова при выборе строки
            on_double_click: Функция обратного вызова при двойном клике
        """
        self.parent = parent
        self.hole_type = hole_type
        self.columns = columns
        self.on_select = on_select
        self.on_double_click = on_double_click
        self.on_right_click = on_right_click
        
                # Добавляем колонки для массива
        if hole_type == "top":
            columns = [
                ("№", 20),
                ("Угол", 20),
                ("Кромка", 20),
                ("X (мм)", 50),
                ("Y (мм)", 50),
                ("Ø (мм)", 40),
                ("Глубина (мм)", 40),
                ("Тип", 40),
                ("Повторы", 40),
                ("OX", 30),
                ("OY", 30)
            ]
        else:
            columns = [
                ("№", 20),
                ("Угол", 20),
                ("Кромка", 20),
                ("X (мм)", 50),
                ("Z (мм)", 50),
                ("Ø (мм)", 40),
                ("Глубина (мм)", 40),
                ("Тип", 40),
                ("Повторы", 40),
                ("OX", 30),
                ("OY", 30)
            ]
        
        # Создание контейнера для таблицы и скроллбаров
        self.container = ttk.Frame(parent)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Создание Treeview
        column_names = [col[0].lower().replace(" ", "_").replace("(", "").replace(")", "") 
                       for col in columns]
        self.tree = ttk.Treeview(
            self.container,
            columns=column_names,
            show="headings",
            height=8  # Уменьшили с 8 до 6 строк
        )
        
        # Настройка колонок
        for i, (text, width) in enumerate(columns):
            col_id = column_names[i]
            self.tree.heading(col_id, text=text)
            self.tree.column(col_id, width=width, anchor=tk.CENTER, minwidth=width)
        
        # Создание скроллбаров
        self.v_scrollbar = ttk.Scrollbar(
            self.container,
            orient=tk.VERTICAL,
            command=self.tree.yview
        )
        self.h_scrollbar = ttk.Scrollbar(
            self.container,
            orient=tk.HORIZONTAL,
            command=self.tree.xview
        )
        
        # Настройка Treeview
        self.tree.configure(yscrollcommand=self.v_scrollbar.set)
        self.tree.configure(xscrollcommand=self.h_scrollbar.set)
        
        # Размещение виджетов
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Настройка весов grid
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        # Привязка событий
        if on_select:
            self.tree.bind('<<TreeviewSelect>>', self._on_select)
        
        if on_double_click:
            self.tree.bind('<Double-Button-1>', self._on_double_click)
                    
        # Привязка событий правого клика
        if on_right_click:
            self.tree.bind("<Button-3>", self._on_right_click)
    
    def _on_select(self, event: tk.Event) -> None:
        """Обработка выбора строки"""
        if self.on_select:
            self.on_select(event)
    
    def _on_double_click(self, event: tk.Event) -> None:
        """Обработка двойного клика"""
        print(f"Двойной клик: {event}")  # Отладочный вывод
        if self.on_double_click:
            self.on_double_click(event)
            
    def _on_right_click(self, event: tk.Event) -> None:
        """Обработка правого клика на таблице"""
        # Определяем строку, по которой кликнули
        item = self.tree.identify_row(event.y)
        if item:
            # Выделяем строку
            self.tree.selection_set(item)
            
            # Вызываем обработчик выбора, чтобы обновить выделение на схеме
            if self.on_select:
                self.on_select(event)
            
            # Вызываем обработчик правого клика для открытия окна редактирования
            if self.on_right_click:
                self.on_right_click(event)
    
    def add_row(self, values: List[Any]) -> None:
        """
        Добавление строки в таблицу
        
        Args:
            values: Значения для строки
        """
        self.tree.insert("", tk.END, values=values)
    
    def clear(self) -> None:
        """Очистка таблицы"""
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    def get_selected(self) -> Optional[List[Any]]:
        """
        Получение выбранной строки
        
        Returns:
            Список значений выбранной строки или None
        """
        selection = self.tree.selection()
        print(f"Treeview selection: {selection}")  # Добавьте эту строку
        
        if selection:
            values = self.tree.item(selection[0])['values']
            print(f"Treeview values: {values}")  # Добавьте эту строку
            return values
        return None
    
    def select_row_by_hole_id(self, hole_id: int) -> bool:
        """
        Выбор строки по ID отверстия
        
        Args:
            hole_id: ID отверстия
            
        Returns:
            True если строка найдена и выбрана
        """
        for child in self.tree.get_children():
            values = self.tree.item(child)['values']
            if values and values[0]:
                # Извлекаем числовой ID из строки
                id_str = str(values[0])
                if '×' in id_str:
                    current_id = int(id_str.split('×')[0])
                else:
                    try:
                        current_id = int(id_str)
                    except ValueError:
                        continue
                
                if current_id == hole_id:
                    self.tree.selection_set(child)
                    self.tree.see(child)
                    return True
        return False
    
    def get_all_rows(self) -> List[List[Any]]:
        """
        Получение всех строк таблицы
        
        Returns:
            Список всех строк
        """
        rows = []
        for child in self.tree.get_children():
            values = self.tree.item(child)['values']
            if values:
                rows.append(values)
        return rows

class SizeControls:
    """Компонент управления размерами панели"""
    
    def __init__(
        self,
        parent: ttk.Frame,
        on_size_change: Optional[Callable] = None
    ):
        """
        Инициализация компонента
        
        Args:
            parent: Родительский фрейм
            on_size_change: Функция обратного вызова при изменении размеров
        """
        self.parent = parent
        self.on_size_change = on_size_change
        
        # Переменные для хранения последних корректных значений
        self.last_valid_width = DEFAULT_PANEL['width']
        self.last_valid_height = DEFAULT_PANEL['height']
        self.last_valid_thickness = DEFAULT_PANEL['thickness']
        self.last_valid_program_name = ""  # Значение по умолчанию
        
        # Флаг для отслеживания процесса валидации
        self._validating = False
        
        # Создание элементов управления
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Создание виджетов"""
        # Название программы
        name_frame = ttk.Frame(self.parent)
        name_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(name_frame, text="Название программы:", width=15).pack(side=tk.LEFT)
        
        # Валидационная функция для имени программы
        name_vcmd = (self.parent.register(self._validate_program_name), '%P')
        
        self.name_entry = ttk.Entry(name_frame, width=15, validate="key", validatecommand=name_vcmd)
        self.name_entry.pack(side=tk.RIGHT)
        self.name_entry.insert(0, self.last_valid_program_name)
        
        # Привязываем события для названия программы
        self.name_entry.bind('<Return>', self._on_enter_pressed)
        self.name_entry.bind('<FocusOut>', self._on_focus_out)
        
        # Ширина
        width_frame = ttk.Frame(self.parent)
        width_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(width_frame, text="Ширина (мм):", width=15).pack(side=tk.LEFT)
        
        self.width_entry = ttk.Entry(width_frame, width=15)
        self.width_entry.pack(side=tk.RIGHT)
        self.width_entry.insert(0, str(self.last_valid_width))
        
        # Привязываем события для ширины
        self.width_entry.bind('<Return>', self._on_enter_pressed)
        self.width_entry.bind('<FocusOut>', self._on_focus_out)
        
        # Высота
        height_frame = ttk.Frame(self.parent)
        height_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(height_frame, text="Высота (мм):", width=15).pack(side=tk.LEFT)
        
        self.height_entry = ttk.Entry(height_frame, width=15)
        self.height_entry.pack(side=tk.RIGHT)
        self.height_entry.insert(0, str(self.last_valid_height))
        
        # Привязываем события для высоты
        self.height_entry.bind('<Return>', self._on_enter_pressed)
        self.height_entry.bind('<FocusOut>', self._on_focus_out)
        
        # Толщина
        thickness_frame = ttk.Frame(self.parent)
        thickness_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(thickness_frame, text="Толщина (мм):", width=15).pack(side=tk.LEFT)
        
        self.thickness_entry = ttk.Entry(thickness_frame, width=15)
        self.thickness_entry.pack(side=tk.RIGHT)
        self.thickness_entry.insert(0, str(self.last_valid_thickness))
        
        # Привязываем события для толщины
        self.thickness_entry.bind('<Return>', self._on_enter_pressed)
        self.thickness_entry.bind('<FocusOut>', self._on_focus_out)
    
    def _validate_program_name(self, value: str) -> bool:
        """Валидация названия программы: только латинские символы, цифры, - и _"""
        if value == "":
            return False  # Не разрешаем пустое название
        
        # Проверяем каждый символ
        for char in value:
            if not (char.isalpha() and char.isascii() and char.islower() or 
                    char.isalpha() and char.isascii() and char.isupper() or
                    char.isdigit() or 
                    char in ['-', '_']):
                return False
        return True
    
    def _validate_and_update_program_name(self) -> None:
        """Валидация и обновление названия программы"""
        try:
            self._validating = True
            text = self.name_entry.get()
            
            # Проверяем, что текст не пустой и соответствует требованиям
            if text and all(char.isalnum() or char in ['-', '_'] for char in text):
                # Сохраняем в верхнем регистре для единообразия
                value = text.upper()
                self.last_valid_program_name = value
                
                # Обновляем поле только если значение изменилось
                if text != value:
                    self.name_entry.delete(0, tk.END)
                    self.name_entry.insert(0, value)
            else:
                # Восстанавливаем последнее корректное значение
                self.name_entry.delete(0, tk.END)
                self.name_entry.insert(0, self.last_valid_program_name)
        finally:
            self._validating = False
    
    def _on_enter_pressed(self, event: tk.Event) -> None:
        """Обработка нажатия Enter в любом поле ввода"""
        widget = event.widget
        
        # Валидируем и обновляем значение
        if widget == self.name_entry:
            self._validate_and_update_program_name()
        elif widget == self.width_entry:
            self._validate_and_update_width()
        elif widget == self.height_entry:
            self._validate_and_update_height()
        elif widget == self.thickness_entry:
            self._validate_and_update_thickness()
        
        # Запускаем обновление панели (для размеров)
        if widget != self.name_entry and self.on_size_change:
            self.parent.after(50, self.on_size_change)
        
        return "break"
    
    def _on_focus_out(self, event: tk.Event) -> None:
        """Обработка потери фокуса полем ввода"""
        if self._validating:
            return
            
        widget = event.widget
        
        # Отложенная валидация поля
        self.parent.after(100, lambda: self._delayed_validate_field(widget))
    
    def _delayed_validate_field(self, widget: tk.Widget) -> None:
        """Отложенная валидация поля"""
        if self._validating:
            return
            
        try:
            self._validating = True
            
            if widget == self.name_entry:
                self._validate_and_update_program_name()
            elif widget == self.width_entry:
                self._validate_and_update_width()
                if self.on_size_change:
                    self.on_size_change()
            elif widget == self.height_entry:
                self._validate_and_update_height()
                if self.on_size_change:
                    self.on_size_change()
            elif widget == self.thickness_entry:
                self._validate_and_update_thickness()
                if self.on_size_change:
                    self.on_size_change()
        finally:
            self._validating = False
    
    def _validate_and_update_width(self) -> None:
        """Валидация и обновление ширины"""
        try:
            text = self.width_entry.get()
            if text == "":
                value = self.last_valid_width
            else:
                value = int(float(text))
            
            # Проверяем границы
            if value < MIN_PANEL_WIDTH:
                value = MIN_PANEL_WIDTH
            elif value > MAX_PANEL_WIDTH:
                value = MAX_PANEL_WIDTH
            
            # Обновляем значение
            self.last_valid_width = value
            
            # Обновляем поле только если значение изменилось
            if text != str(value):
                self.width_entry.delete(0, tk.END)
                self.width_entry.insert(0, str(value))
                
        except (ValueError, tk.TclError):
            # Восстанавливаем последнее корректное значение
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, str(self.last_valid_width))
    
    def _validate_and_update_height(self) -> None:
        """Валидация и обновление высоты"""
        try:
            text = self.height_entry.get()
            if text == "":
                value = self.last_valid_height
            else:
                value = int(float(text))
            
            # Проверяем границы
            if value < MIN_PANEL_HEIGHT:
                value = MIN_PANEL_HEIGHT
            elif value > MAX_PANEL_HEIGHT:
                value = MAX_PANEL_HEIGHT
            
            # Обновляем значение
            self.last_valid_height = value
            
            # Обновляем поле только если значение изменилось
            if text != str(value):
                self.height_entry.delete(0, tk.END)
                self.height_entry.insert(0, str(value))
                
        except (ValueError, tk.TclError):
            # Восстанавливаем последнее корректное значение
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(self.last_valid_height))
    
    def _validate_and_update_thickness(self) -> None:
        """Валидация и обновление толщины"""
        try:
            text = self.thickness_entry.get()
            if text == "":
                value = self.last_valid_thickness
            else:
                value = int(float(text))
            
            # Проверяем границы
            if value < MIN_PANEL_THICKNESS:
                value = MIN_PANEL_THICKNESS
            elif value > MAX_PANEL_THICKNESS:
                value = MAX_PANEL_THICKNESS
            
            # Обновляем значение
            self.last_valid_thickness = value
            
            # Обновляем поле только если значение изменилось
            if text != str(value):
                self.thickness_entry.delete(0, tk.END)
                self.thickness_entry.insert(0, str(value))
                
        except (ValueError, tk.TclError):
            # Восстанавливаем последнее корректное значение
            self.thickness_entry.delete(0, tk.END)
            self.thickness_entry.insert(0, str(self.last_valid_thickness))
    
    def _validate_all_fields(self) -> None:
        """Валидация всех полей"""
        self._validate_and_update_program_name()
        self._validate_and_update_width()
        self._validate_and_update_height()
        self._validate_and_update_thickness()
    
    def set_values(
        self,
        width: int,
        height: int,
        thickness: int,
        program_name: str = "DETAL"
    ) -> None:
        """
        Установка значений размеров и названия программы
        
        Args:
            width: Ширина панели
            height: Высота панели
            thickness: Толщина панели
            program_name: Название программы
        """
        # Обновляем последние корректные значения
        self.last_valid_width = width
        self.last_valid_height = height
        self.last_valid_thickness = thickness
        self.last_valid_program_name = program_name.upper() if program_name else "DETAL"
        
        # Отключаем валидацию на время обновления значений
        old_state = self.width_entry.cget('validate')
        self.width_entry.configure(validate='none')
        self.height_entry.configure(validate='none')
        self.thickness_entry.configure(validate='none')
        self.name_entry.configure(validate='none')
        
        try:
            # Устанавливаем значения в поля
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, str(width))
            
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(height))
            
            self.thickness_entry.delete(0, tk.END)
            self.thickness_entry.insert(0, str(thickness))
            
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, self.last_valid_program_name)
        finally:
            # Восстанавливаем валидацию
            self.width_entry.configure(validate=old_state)
            self.height_entry.configure(validate=old_state)
            self.thickness_entry.configure(validate=old_state)
            self.name_entry.configure(validate='key')
    
    def get_values(self) -> Dict[str, Any]:
        """
        Получение значений размеров и названия программы
        
        Returns:
            Словарь с размерами и названием
        """
        # Валидируем все поля
        self._validate_all_fields()
        
        return {
            'width': self.last_valid_width,
            'height': self.last_valid_height,
            'thickness': self.last_valid_thickness,
            'program_name': self.last_valid_program_name
        }


class LegendPanel:
    """Компонент легенды диаметров"""
    
    def __init__(
        self,
        parent: ttk.Frame,
        diameter_colors: Dict[int, str]
    ):
        """
        Инициализация компонента
        
        Args:
            parent: Родительский фрейм
            diameter_colors: Словарь цветов для диаметров
        """
        self.parent = parent
        self.diameter_colors = diameter_colors
        
        # Создание контейнера
        legend_frame = ttk.LabelFrame(parent, text="Цвета диаметров (мм)", padding=8)
        legend_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Canvas для легенды
        self.canvas = tk.Canvas(
            legend_frame,
            height=30,
            bg='white',
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.X)
        
        # Инициализация легенды
        self.update_legend(diameter_colors)
    
    def update_legend(self, diameter_colors: Dict[int, str]) -> None:
        """
        Обновление легенды
        
        Args:
            diameter_colors: Словарь цветов для диаметров
        """
        self.diameter_colors = diameter_colors
        self.canvas.delete("all")
        
        # Отсортированные диаметры
        diameters = sorted(diameter_colors.keys())
        
        # Отображение только наиболее часто используемых диаметров
        common_diameters = [d for d in diameters if d in [2, 5, 8, 10, 15, 20, 35]]
        
        # Если есть другие диаметры, показываем только первые 6
        if len(diameters) > 7:
            display_diameters = common_diameters[:6]
            has_more = True
        else:
            display_diameters = diameters[:7]
            has_more = False
        
        # Отрисовка элементов легенды
        x_pos = 10
        for diameter in display_diameters:
            color = self.diameter_colors.get(diameter, "#888888")
            
            # Круг цвета
            self.canvas.create_oval(
                x_pos, 10,
                x_pos + LEGEND_CIRCLE_SIZE,
                10 + LEGEND_CIRCLE_SIZE,
                fill=color,
                outline='black'
            )
            
            # Текст диаметра
            self.canvas.create_text(
                x_pos + LEGEND_CIRCLE_SIZE + 5,
                10 + LEGEND_CIRCLE_SIZE // 2,
                text=str(diameter),
                anchor=tk.W,
                font=FONT_SMALL
            )
            
            x_pos += LEGEND_ITEM_WIDTH
        
        # Отображение "и другие" если есть
        if has_more:
            self.canvas.create_text(
                x_pos + 5,
                10 + LEGEND_CIRCLE_SIZE // 2,
                text="и др.",
                anchor=tk.W,
                font=FONT_SMALL
            )


class ControlPanel:
    """Панель управления отверстиями"""
    
    def __init__(
        self,
        parent: ttk.Frame,
        on_add: Callable,
        on_copy: Callable,
        on_delete: Callable,
        on_edit: Callable
    ):
        """
        Инициализация панели управления
        
        Args:
            parent: Родительский фрейм
            on_add: Функция для добавления отверстия
            on_copy: Функция для копирования отверстия
            on_delete: Функция для удаления отверстия
            on_edit: Функция для редактирования отверстия
        """
        self.parent = parent
        self.on_add = on_add
        self.on_copy = on_copy
        self.on_delete = on_delete
        self.on_edit = on_edit
        
        # Создание контейнера
        button_frame = ttk.LabelFrame(parent, text="Управление отверстиями", padding=10)
        button_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Создание кнопок
        self._create_buttons(button_frame)
    
    def _create_buttons(self, parent: ttk.Frame) -> None:
        """Создание кнопок управления"""
        # Первый ряд кнопок
        top_button_frame = ttk.Frame(parent)
        top_button_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(
            top_button_frame,
            text="Добавить",
            command=self.on_add
        ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        ttk.Button(
            top_button_frame,
            text="Копировать (F3)",
            command=lambda: print("Копировать нажата") or self.on_copy()
        ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Второй ряд кнопок
        bottom_button_frame = ttk.Frame(parent)
        bottom_button_frame.pack(fill=tk.X)
        
        ttk.Button(
            bottom_button_frame,
            text="Редактировать",
            command=self.on_edit
        ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        ttk.Button(
            bottom_button_frame,
            text="Удалить",
            command=self.on_delete
        ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)


class MirrorButtons:
    """Компонент кнопок зеркалирования"""
    
    def __init__(
        self,
        parent: ttk.Frame,
        on_mirror_x: Callable,
        on_mirror_y: Callable
    ):
        """
        Инициализация компонента
        
        Args:
            parent: Родительский фрейм
            on_mirror_x: Функция для зеркалирования по X
            on_mirror_y: Функция для зеркалирования по Y
        """
        self.parent = parent
        self.on_mirror_x = on_mirror_x
        self.on_mirror_y = on_mirror_y
        
        # Создание контейнера
        mirror_frame = ttk.LabelFrame(parent, text="Зеркалирование отверстий", padding=10)
        mirror_frame.pack(fill=tk.X, padx=15, pady=(10, 15))
        
        # Создание кнопок
        self._create_buttons(mirror_frame)
    
    def _create_buttons(self, parent: ttk.Frame) -> None:
        """Создание кнопок зеркалирования"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="Зеркало по X",
            command=self.on_mirror_x
        ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        ttk.Button(
            button_frame,
            text="Зеркало по Y",
            command=self.on_mirror_y
        ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)


class FileButtons:
    """Компонент кнопок работы с файлами"""
    
    def __init__(
        self,
        parent: ttk.Frame,
        on_new: Callable,
        on_save: Callable,
        on_load: Callable
    ):
        """
        Инициализация компонента
        
        Args:
            parent: Родительский фрейм
            on_new: Функция для создания нового файла
            on_save: Функция для сохранения файла
            on_load: Функция для загрузки файла
        """
        self.parent = parent
        self.on_new = on_new
        self.on_save = on_save
        self.on_load = on_load
        
        # Создание контейнера
        file_frame = ttk.LabelFrame(parent, text="Файл (.anc)", padding=10)
        file_frame.pack(fill=tk.X, padx=15, pady=(10, 15))
        
        # Создание кнопок
        self._create_buttons(file_frame)
    
    def _create_buttons(self, parent: ttk.Frame) -> None:
        """Создание кнопок работы с файлами"""
        # Верхний ряд кнопок
        top_button_frame = ttk.Frame(parent)
        top_button_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(
            top_button_frame,
            text="Новый файл",
            command=self.on_new
        ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        ttk.Button(
            top_button_frame,
            text="Сохранить",
            command=self.on_save
        ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Нижний ряд кнопок
        bottom_button_frame = ttk.Frame(parent)
        bottom_button_frame.pack(fill=tk.X)
        
        ttk.Button(
            bottom_button_frame,
            text="Загрузить",
            command=self.on_load
        ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)


class HelpButton:
    """Компонент кнопки справки"""
    
    def __init__(
        self,
        parent: ttk.Frame,
        on_help: Callable
    ):
        """
        Инициализация компонента
         
        Args:
            parent: Родительский фрейм
            on_help: Функция для показа справки
        """
        self.parent = parent
        self.on_help = on_help
        
        # Создание кнопки
        self.button = ttk.Button(
            parent,
            text="?",
            width=3,
            command=self.on_help
        )
        self.button.pack(side=tk.LEFT, padx=(0, 10))


class GrooveTab:
    """Компонент вкладки параметров паза (фрезеровка)"""

    def __init__(
        self,
        parent: ttk.Frame,
        on_change: Optional[Callable] = None,
        on_toggle: Optional[Callable] = None
    ):
        """
        Инициализация компонента

        Args:
            parent: Родительский фрейм
            on_change: Функция обратного вызова при изменении параметров
            on_toggle: Функция обратного вызова при сворачивании/разворачивании блока
        """
        self.parent = parent
        self.on_change = on_change
        self.on_toggle = on_toggle

        # Флаг состояния сворачивания (True - блок свёрнут)
        self._collapsed = False

        # Текущие значения
        self.enabled_var = tk.BooleanVar(value=DEFAULT_GROOVE['enabled'])
        self.length_var = tk.StringVar(value=str(DEFAULT_GROOVE['length']))
        self.width_var = tk.StringVar(value=str(DEFAULT_GROOVE['width']))
        self.depth_var = tk.StringVar(value=str(DEFAULT_GROOVE['depth']))
        self.y_pos_var = tk.StringVar(value=str(DEFAULT_GROOVE['y_pos']))

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Создание виджетов"""
        # Шапка блока: кнопка сворачивания и чекбокс включения паза
        header_frame = ttk.Frame(self.parent)
        header_frame.pack(fill=tk.X, pady=(5, 10))

        # Кнопка-переключатель сворачивания
        self.toggle_btn = ttk.Button(
            header_frame,
            text="▾",
            width=3,
            command=self._toggle_collapsed
        )
        self.toggle_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.enabled_check = ttk.Checkbutton(
            header_frame,
            text="Фрезеровать паз",
            variable=self.enabled_var,
            command=self._on_change
        )
        self.enabled_check.pack(side=tk.LEFT, anchor=tk.W)

        # Контейнер со сворачиваемыми полями параметров
        self.content = ttk.Frame(self.parent)
        self.content.pack(fill=tk.X)

        # Поля параметров
        fields = [
            ("Длина (LPAZ, мм):", self.length_var, "length"),
            ("Ширина (WPAZ, мм):", self.width_var, "width"),
            ("Глубина (ZPAZ, мм):", self.depth_var, "depth"),
            ("Положение центра по Y от верха (YPAZ, мм):", self.y_pos_var, "y_pos")
        ]

        for i, (label, var, key) in enumerate(fields):
            frame = ttk.Frame(self.content)
            frame.pack(fill=tk.X, pady=4)

            ttk.Label(frame, text=label, width=32, anchor=tk.W).pack(side=tk.LEFT)

            entry = ttk.Entry(frame, width=12, textvariable=var)
            entry.pack(side=tk.RIGHT)
            entry.bind('<KeyRelease>', self._on_change)
            entry.bind('<Return>', self._on_change)

        ttk.Label(
            self.content,
            text="Паз центрируется по ширине панели.",
            font=FONT_SMALL,
            foreground='gray'
        ).pack(anchor=tk.W, pady=(10, 0))

    def _toggle_collapsed(self) -> None:
        """Сворачивание/разворачивание блока параметров паза"""
        if self._collapsed:
            # Разворачиваем блок
            self.content.pack(fill=tk.X)
            self.toggle_btn.configure(text="▾")
            self._collapsed = False
        else:
            # Сворачиваем блок
            self.content.pack_forget()
            self.toggle_btn.configure(text="▸")
            self._collapsed = True

        # Уведомляем о изменении размера блока (для пересчёта скроллбара)
        if self.on_toggle:
            self.on_toggle()

    def _on_change(self, event=None) -> None:
        """Обработчик изменения параметров"""
        if self.on_change:
            self.on_change()

    def get_values(self) -> Dict[str, Any]:
        """
        Получение значений параметров паза

        Returns:
            Словарь с параметрами паза
        """
        def _to_float(var: tk.StringVar, default: float) -> float:
            try:
                return float(var.get().replace(',', '.'))
            except (ValueError, tk.TclError):
                return default

        return {
            'enabled': self.enabled_var.get(),
            'length': _to_float(self.length_var, DEFAULT_GROOVE['length']),
            'width': _to_float(self.width_var, DEFAULT_GROOVE['width']),
            'depth': _to_float(self.depth_var, DEFAULT_GROOVE['depth']),
            'y_pos': _to_float(self.y_pos_var, DEFAULT_GROOVE['y_pos'])
        }

    def set_values(self, groove_data: Dict[str, Any]) -> None:
        """
        Установка значений параметров паза

        Args:
            groove_data: Словарь с параметрами паза
        """
        data = groove_data or DEFAULT_GROOVE

        self.enabled_var.set(bool(data.get('enabled', DEFAULT_GROOVE['enabled'])))
        self.length_var.set(str(data.get('length', DEFAULT_GROOVE['length'])))
        self.width_var.set(str(data.get('width', DEFAULT_GROOVE['width'])))
        self.depth_var.set(str(data.get('depth', DEFAULT_GROOVE['depth'])))
        self.y_pos_var.set(str(data.get('y_pos', DEFAULT_GROOVE['y_pos'])))