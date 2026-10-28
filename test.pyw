# test.py - исправленная версия метода create_widgets
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Tuple

# Импорт модулей из библиотек
from geometry import evaluate_expression
from file_handler import ANCFileHandler
from hole_manager import HoleManager, Hole, HoleType, Corner, Edge, HoleFactory
from groove import Groove
from visualization import PanelVisualizer
from ui_components import (
    TableComponent,
    ControlPanel,
    MirrorButtons,
    FileButtons,
    SizeControls,
    LegendPanel,
    GrooveTab
)
from config import (
    DIAMETER_COLORS,
    DEFAULT_PANEL,
    DEFAULT_GROOVE,
    PANEL_COLOR,
    EDGE_COLOR,
    HOLE_EDGE_COLOR,
    CORNER_ANCHORS,
    EDGE_POSITIONS
)


class PanelHoleVisualizer:
    """Главный класс приложения для визуализации отверстий на панели"""
    
    def __init__(self, root: tk.Tk):
        """
        Инициализация приложения
        
        Args:
            root: Главное окно Tkinter
        """
        self.root = root
        self.root.title("Визуализация отверстий на панели")
        self.root.state('zoomed')  # Полноэкранный режим
        
        # Инициализация менеджера отверстий
        self.hole_manager = HoleManager()
        
        # Инициализация обработчика файлов
        self.file_handler = ANCFileHandler()
        
        # Инициализация визуализатора
        self.canvas = None
        self.visualizer = None
        
        # Параметры панели
        self.panel_data = {
            'width': DEFAULT_PANEL['width'],
            'height': DEFAULT_PANEL['height'],
            'thickness': DEFAULT_PANEL['thickness']
        }
        
        # Параметры паза (фрезеровка)
        self.groove = Groove.from_dict(DEFAULT_GROOVE)
         
        # Название программы
        self.program_name = "DETAL"
        
        # Цвета для диаметров (копируем из конфигурации)
        self.diameter_colors = DIAMETER_COLORS.copy()
        
        # Ссылки на компоненты UI
        self.ui_components: Dict[str, object] = {}
        
        # Создание интерфейса
        self.create_widgets()
        
        # Привязка событий
        self.root.bind("<Configure>", lambda e: self.draw_panel())
        
        # Привязка горячих клавиш
        self._bind_hotkeys()
        
        # Инициальная отрисовка
        self.draw_panel()
        
    def _bind_hotkeys(self) -> None:
        """Привязка горячих клавиш"""
        # Удаление отверстия - клавиша Delete
        self.root.bind('<Delete>', lambda event: self.delete_hole())
        
        # Копирование отверстия - F3
        def on_f3(event):
            print("F3 обрабатывается")
            # Вызываем метод напрямую, без задержки
            self.copy_hole()
            return "break"  # Предотвращаем дальнейшую обработку
        
        self.root.bind('<F3>', on_f3)
        
        # Также можно добавить другие горячие клавиши
        self.root.bind('<Control-n>', lambda event: self.new_file())
        self.root.bind('<Control-s>', lambda event: self.save_to_file())
        self.root.bind('<Control-o>', lambda event: self.load_from_file())
        
    def create_widgets(self) -> None:
        """Создание всех виджетов интерфейса"""
        # Основное разделение на левую и правую части
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Левая часть - схема детали
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Заголовок для схемы
        ttk.Label(left_frame, text="Схематическое изображение детали", 
                 font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Canvas для рисования детали
        self.canvas = tk.Canvas(left_frame, bg='white', highlightthickness=1, 
                               highlightbackground="#CCCCCC")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Инициализация визуализатора
        self.visualizer = PanelVisualizer(
            canvas=self.canvas,
            panel_color=PANEL_COLOR,
            edge_color=EDGE_COLOR,
            hole_edge_color=HOLE_EDGE_COLOR,
            diameter_colors=self.diameter_colors,
            corner_anchors=CORNER_ANCHORS,
            edge_positions=EDGE_POSITIONS
        )
        
        # Правая часть - параметры и таблица (в контейнере с прокруткой)
        self._create_scrollable_right_panel(main_frame)
        
        # Разделитель между левой и правой частями
        ttk.Separator(main_frame, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=5
        )
    
    def _create_scrollable_right_panel(self, main_frame: ttk.Frame) -> None:
        """Создание правой панели с вертикальной прокруткой, которая активируется только при необходимости"""
        # Создаем контейнер для правой панели
        right_container = ttk.Frame(main_frame, width=500)
        right_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        right_container.pack_propagate(False)
        
        # Создаем Canvas для прокрутки
        canvas = tk.Canvas(right_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(right_container, orient="vertical", command=canvas.yview)
        
        # Создаем фрейм для содержимого, который будет прокручиваться
        self.right_content = ttk.Frame(canvas)
        
        # Привязываем изменение размера содержимого к обновлению области прокрутки
        def configure_scroll_region(event=None):
            # Обновляем область прокрутки
            canvas.configure(scrollregion=canvas.bbox("all"))
            
            # Проверяем, нужно ли включать скроллбар
            bbox = canvas.bbox("all")
            if bbox:
                # Высота содержимого
                content_height = bbox[3] - bbox[1]
                # Высота видимой области
                canvas_height = canvas.winfo_height()
                
                # Если содержимое выше видимой области, включаем скроллбар
                if content_height > canvas_height:
                    scrollbar.configure(command=canvas.yview)
                    canvas.configure(yscrollcommand=scrollbar.set)
                else:
                    # Если все помещается, отключаем скроллбар
                    scrollbar.configure(command=lambda *args: None)
                    canvas.configure(yscrollcommand=None)
            else:
                # Если содержимого нет, отключаем скроллбар
                scrollbar.configure(command=lambda *args: None)
                canvas.configure(yscrollcommand=None)
        
        self.right_content.bind("<Configure>", configure_scroll_region)
        
        # Создаем окно в Canvas для содержимого
        window_id = canvas.create_window((0, 0), window=self.right_content, anchor="nw", width=500)
        
        # Функция для обновления ширины содержимого при изменении размера Canvas
        def update_window_width(event):
            canvas.itemconfig(window_id, width=canvas.winfo_width())
            # Обновляем состояние скроллбара после изменения размера
            configure_scroll_region()
        
        canvas.bind("<Configure>", update_window_width)
        
        # Упаковываем Canvas и скроллбар (скроллбар всегда виден)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Отключаем прокрутку колесом мыши и другими способами
        # 1. Отключаем прокрутку колесом мыши
        def block_mousewheel(event):
            # Блокируем прокрутку колесом мыши
            return "break"
        
        canvas.bind_all("<MouseWheel>", block_mousewheel)
        canvas.bind_all("<Button-4>", block_mousewheel)  # Для Linux
        canvas.bind_all("<Button-5>", block_mousewheel)  # Для Linux
        
        # 2. Отключаем клавиши прокрутки
        def block_scroll_keys(event):
            # Блокируем клавиши прокрутки
            if event.keysym in ('Up', 'Down', 'Prior', 'Next', 'Home', 'End'):
                return "break"
            return None
        
        canvas.bind_all("<KeyPress>", block_scroll_keys)
        
        # 3. Отключаем перетаскивание для прокрутки
        canvas.bind("<ButtonPress-1>", lambda e: "break")
        canvas.bind("<B1-Motion>", lambda e: "break")
        
        # Изначально отключаем скроллбар
        scrollbar.configure(command=lambda *args: None)
        canvas.configure(yscrollcommand=None)
        
        # Привязываем обновление состояния скроллбара при изменении содержимого
        def on_content_change():
            # Обновляем состояние скроллбара после изменения содержимого
            canvas.after(100, configure_scroll_region)
        
        # Создаем содержимое правой панели
        self._create_right_panel_content()
        
        # Назначаем функцию для обновления состояния скроллбара
        self.update_scrollbar_state = configure_scroll_region
        
        # Вызываем проверку после создания всего содержимого
        canvas.after(200, configure_scroll_region)

    def update_scrollbar(self) -> None:
        """Обновление состояния скроллбара"""
        if hasattr(self, 'update_scrollbar_state'):
            self.update_scrollbar_state()    
    
    def _create_right_panel_content(self) -> None:
        """Создание содержимого правой панели"""
        # Блок с размерами детали
        size_frame = ttk.LabelFrame(self.right_content, text="Размеры детали (мм)", padding=15)
        size_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Поля для размеров
        self.ui_components['size_controls'] = SizeControls(
            parent=size_frame,
            on_size_change=self.update_panel_size
        )
        
        # Установка начальных значений
        self.ui_components['size_controls'].set_values(
            width=self.panel_data['width'],
            height=self.panel_data['height'],
            thickness=self.panel_data['thickness']
        )
        
        # Блок с кнопкой справки и легендой диаметров
        top_right_frame = ttk.Frame(self.right_content)
        top_right_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Кнопка справки
        help_button = ttk.Button(top_right_frame, text="?", width=3, 
                                command=self.show_help)
        help_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Легенда диаметров
        self.ui_components['legend'] = LegendPanel(
            parent=top_right_frame,
            diameter_colors=self.diameter_colors
        )
        
        # Вкладки для таблиц отверстий
        self.create_holes_tabs(self.right_content)
        
        # Блок параметров паза (фрезеровка)
        groove_frame = ttk.LabelFrame(self.right_content, text="Паз (фрезеровка)", padding=15)
        groove_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.ui_components['groove_tab'] = GrooveTab(
            parent=groove_frame,
            on_change=self._on_groove_change,
            on_toggle=self.update_scrollbar
        )
        
        # Установка начальных значений
        self.ui_components['groove_tab'].set_values(self.groove.to_dict())
         
        # Кнопки управления
        self.ui_components['controls'] = ControlPanel(
            parent=self.right_content,
            on_add=self.add_hole,
            on_copy=self.copy_hole,
            on_delete=self.delete_hole,
            on_edit=self.edit_hole
        )
        
        # Кнопки зеркалирования
        self.ui_components['mirror'] = MirrorButtons(
            parent=self.right_content,
            on_mirror_x=self.mirror_x,
            on_mirror_y=self.mirror_y
        )
        
        # Кнопки работы с файлами
        self.ui_components['file_buttons'] = FileButtons(
            parent=self.right_content,
            on_new=self.new_file,
            on_save=self.save_to_file,
            on_load=self.load_from_file
        )
    
    def create_holes_tabs(self, parent: ttk.Frame) -> None:
        """Создание вкладок с таблицами отверстий"""
        # Создаем Notebook для вкладок
        tabs_frame = ttk.LabelFrame(parent, text="Отверстия", padding=15)
        tabs_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.ui_components['notebook'] = ttk.Notebook(tabs_frame)
        self.ui_components['notebook'].pack(fill=tk.BOTH, expand=True)
        
        # Вкладка 1: Отверстия в плоскости
        top_tab = ttk.Frame(self.ui_components['notebook'])
        self.ui_components['notebook'].add(top_tab, text="В плоскости")
        
        # Таблица отверстий в плоскости
        self.ui_components['top_table'] = TableComponent(
            parent=top_tab,
            hole_type="top",
            columns=[
                ("№", 20),
                ("Угол", 20),
                ("Кромка", 20),
                ("X (мм)", 80),
                ("Y (мм)", 80),
                ("Ø (мм)", 80),
                ("Глубина (мм)", 100),
                ("Тип", 80)
            ],
            on_select=self.on_hole_select,
            on_double_click=self.edit_hole,
            on_right_click=self.on_table_right_click
        )
        
        # Вкладка 2: Отверстия в кромках
        edge_tab = ttk.Frame(self.ui_components['notebook'])
        self.ui_components['notebook'].add(edge_tab, text="В кромках")
        
        # Таблица отверстий в кромках
        self.ui_components['edge_table'] = TableComponent(
            parent=edge_tab,
            hole_type="edge",
            columns=[
                ("№", 20),
                ("Угол", 20),
                ("Кромка", 20),
                ("X (мм)", 80),
                ("Z (мм)", 80),
                ("Ø (мм)", 80),
                ("Глубина (мм)", 100),
                ("Тип", 80)
            ],
            on_select=self.on_hole_select,
            on_double_click=self.edit_hole,
            on_right_click=self.on_table_right_click
        )

    def get_active_tab(self) -> str:
        """Получение активной вкладки"""
        tab_index = self.ui_components['notebook'].index(
            self.ui_components['notebook'].select()
        )
        return "top" if tab_index == 0 else "edge"
    
    def get_active_table(self) -> TableComponent:
        """Получение активной таблицы"""
        tab_type = self.get_active_tab()
        return self.ui_components[f"{tab_type}_table"]
    
    def update_panel_size(self) -> None:
        """Обновление размеров панели и названия программы"""
        values = self.ui_components['size_controls'].get_values()
        
        # Проверяем, изменились ли значения
        if (values['width'] != self.panel_data['width'] or 
            values['height'] != self.panel_data['height'] or 
            values['thickness'] != self.panel_data['thickness']):
            
            self.panel_data['width'] = values['width']
            self.panel_data['height'] = values['height']
            self.panel_data['thickness'] = values['thickness']
            
            # Перерисовываем панель
            self.draw_panel()
            self.update_tables()
            
            # Обновляем состояние скроллбара
            if hasattr(self, 'update_scrollbar'):
                self.update_scrollbar()
        
        # Обновляем название программы (всегда)
        self.program_name = values.get('program_name', 'DETAL')
    
    def _on_groove_change(self) -> None:
        """Обработчик изменения параметров паза"""
        if 'groove_tab' not in self.ui_components:
            return
        
        # Считываем параметры паза из вкладки
        groove_values = self.ui_components['groove_tab'].get_values()
        self.groove = Groove.from_dict(groove_values)
        
        # Перерисовываем панель с новым пазом
        self.draw_panel()
        self.update_scrollbar()
    
# test.py - исправленная версия метода draw_panel

    def draw_panel(self) -> None:
        """Отрисовка панели и отверстий"""
        if self.visualizer:
            self.visualizer.draw_panel(
                panel_data=self.panel_data,
                holes=self.hole_manager.get_all_holes(),
                groove=self.groove,
                on_hole_click=self.on_canvas_hole_click,
                on_hole_right_click=self.on_canvas_hole_right_click  # Добавим обработчик правого клика
            )
    
    def update_tables(self) -> None:
        """Обновление таблиц отверстий"""
        # Очищаем обе таблицы
        self.ui_components['top_table'].clear()
        self.ui_components['edge_table'].clear()
        
        # Заполняем таблицы данными
        for hole in self.hole_manager.get_all_holes():
            # Добавляем информацию о массиве в отображение
            array_info = f"×{hole.repeats}" if hole.repeats > 1 else ""
            
            if hole.is_top_hole():
                # Отверстие в плоскости
                try:
                    x = evaluate_expression(hole.x_expr) if hole.x_expr else hole.x_local
                    y = evaluate_expression(hole.y_expr) if hole.y_expr else hole.y_local
                except ValueError:
                    x = hole.x_local
                    y = hole.y_local
                
                # Безопасное форматирование
                try:
                    x_val = float(x) if isinstance(x, (int, float)) else 0.0
                    y_val = float(y) if isinstance(y, (int, float)) else 0.0
                    depth_val = float(hole.depth) if isinstance(hole.depth, (int, float)) else 10.0
                    offset_x_val = float(hole.offset_x_local) if isinstance(hole.offset_x_local, (int, float)) else 0.0
                    offset_y_val = float(hole.offset_y_local) if isinstance(hole.offset_y_local, (int, float)) else 0.0
                    
                    self.ui_components['top_table'].add_row([
                        f"{hole.id}{array_info}",
                        hole.corner.value,
                        hole.edge.value,
                        f"{x_val:.1f}",
                        f"{y_val:.1f}",
                        hole.diameter,
                        f"{depth_val:.1f}",
                        "Сквоз" if hole.hole_type == HoleType.THROUGH else "Глух",
                        hole.repeats,
                        f"{offset_x_val:.1f}",
                        f"{offset_y_val:.1f}"
                    ])
                except Exception as e:
                    print(f"Ошибка при форматировании отверстия {hole.id}: {e}")
                    self.ui_components['top_table'].add_row([
                        f"{hole.id}{array_info}",
                        hole.corner.value,
                        hole.edge.value,
                        "ошибка",
                        "ошибка",
                        str(hole.diameter),
                        str(hole.depth),
                        "Сквоз" if hole.hole_type == HoleType.THROUGH else "Глух",
                        str(hole.repeats),
                        str(hole.offset_x_local),
                        str(hole.offset_y_local)
                    ])
            else:
                # Отверстие в кромке
                try:
                    x = evaluate_expression(hole.x_expr) if hole.x_expr else hole.x_local
                    z = evaluate_expression(hole.z_expr) if hole.z_expr else hole.z_local
                except ValueError:
                    x = hole.x_local
                    z = hole.z_local
                
                # Безопасное форматирование
                try:
                    x_val = float(x) if isinstance(x, (int, float)) else 0.0
                    z_val = float(z) if isinstance(z, (int, float)) else 0.0
                    depth_val = float(hole.depth) if isinstance(hole.depth, (int, float)) else 15.0
                    offset_x_val = float(hole.offset_x_local) if isinstance(hole.offset_x_local, (int, float)) else 0.0
                    offset_y_val = float(hole.offset_y_local) if isinstance(hole.offset_y_local, (int, float)) else 0.0
                    
                    self.ui_components['edge_table'].add_row([
                        f"{hole.id}{array_info}",
                        hole.corner.value,
                        hole.edge.value,
                        f"{x_val:.1f}",
                        f"{z_val:.1f}",
                        hole.diameter,
                        f"{depth_val:.1f}",
                        "Сквоз" if hole.hole_type == HoleType.THROUGH else "Глух",
                        hole.repeats,
                        f"{offset_x_val:.1f}",
                        f"{offset_y_val:.1f}"
                    ])
                except Exception as e:
                    print(f"Ошибка при форматировании отверстия {hole.id}: {e}")
                    self.ui_components['edge_table'].add_row([
                        f"{hole.id}{array_info}",
                        hole.corner.value,
                        hole.edge.value,
                        "ошибка",
                        "ошибка",
                        str(hole.diameter),
                        str(hole.depth),
                        "Сквоз" if hole.hole_type == HoleType.THROUGH else "Глух",
                        str(hole.repeats),
                        str(hole.offset_x_local),
                        str(hole.offset_y_local)
                    ])
        
        # Обновляем легенду
        self.ui_components['legend'].update_legend(self.diameter_colors)
            
        # Обновляем состояние скроллбара
        if hasattr(self, 'update_scrollbar'):
            self.update_scrollbar()
    
# В методе on_canvas_hole_click в test.py обновим:

    def on_table_right_click(self, event=None) -> None:
        """Обработка правого клика на таблице - открытие окна редактирования"""
        # Просто вызываем метод редактирования отверстия
        # Строка уже выделена в TableComponent._on_right_click
        self.edit_selected_hole()

    def on_canvas_hole_right_click(self, hole_id: int) -> None:
        """Обработка правого клика по отверстию на схеме - открытие окна редактирования"""
        # Если hole_id составной (например, "1_2"), берем только базовую часть
        if isinstance(hole_id, str) and '_' in hole_id:
            base_hole_id = int(hole_id.split('_')[0])
        else:
            base_hole_id = hole_id
        
        hole = self.hole_manager.get_hole_by_id(base_hole_id)
        if not hole:
            return
        
        # Подсвечиваем отверстие
        if self.visualizer:
            if hole.repeats > 1:
                self.visualizer.highlight_array(base_hole_id)
            else:
                self.visualizer.highlight_hole(base_hole_id)
        
        # Определяем тип отверстия и переключаем вкладку
        if hole.is_top_hole():
            self.ui_components['notebook'].select(0)
            table = self.ui_components['top_table']
        else:
            self.ui_components['notebook'].select(1)
            table = self.ui_components['edge_table']
        
        # Выделяем строку в таблице
        found = False
        for child in table.tree.get_children():
            values = table.tree.item(child)['values']
            if values and str(values[0]).startswith(str(base_hole_id)):
                table.tree.selection_set(child)
                table.tree.see(child)
                found = True
                break
        
        if not found:
            table.select_row_by_hole_id(base_hole_id)
        
        # Открываем окно редактирования
        self.edit_selected_hole()

    def on_canvas_hole_click(self, hole_id: int) -> None:
        """Обработка клика по отверстию на схеме"""
        # Если hole_id составной (например, "1_2"), берем только базовую часть
        if isinstance(hole_id, str) and '_' in hole_id:
            base_hole_id = int(hole_id.split('_')[0])
        else:
            base_hole_id = hole_id
        
        hole = self.hole_manager.get_hole_by_id(base_hole_id)
        if not hole:
            return
        
        # Определяем, нужно ли выделять весь массив
        if hole.repeats > 1:
            # Выделяем весь массив
            if self.visualizer:
                self.visualizer.highlight_array(base_hole_id)
        else:
            # Выделяем одно отверстие
            if self.visualizer:
                self.visualizer.highlight_hole(base_hole_id)
        
        # Определяем тип отверстия и переключаем вкладку
        if hole.is_top_hole():
            self.ui_components['notebook'].select(0)
            table = self.ui_components['top_table']
        else:
            self.ui_components['notebook'].select(1)
            table = self.ui_components['edge_table']
        
        # Выделяем строку в таблице
        found = False
        for child in table.tree.get_children():
            values = table.tree.item(child)['values']
            if values and str(values[0]).startswith(str(base_hole_id)):
                table.tree.selection_set(child)
                table.tree.see(child)
                found = True
                break
        
        if not found:
            # Если не нашли, просто выбираем первую строку с таким ID
            table.select_row_by_hole_id(base_hole_id)

    # Обновим метод on_hole_select в test.py:

    def on_hole_select(self, event=None) -> None:
        """Обработка выбора отверстия в таблице"""
        table = self.get_active_table()
        selected = table.get_selected()
        
        if selected:
            hole_id_str = selected[0]  # Первый столбец - ID отверстия
            
            # Извлекаем базовый ID (удаляем информацию о массиве)
            if isinstance(hole_id_str, str) and '×' in hole_id_str:
                base_hole_id = int(hole_id_str.split('×')[0])
            else:
                try:
                    base_hole_id = int(hole_id_str)
                except ValueError:
                    return
            
            # Получаем отверстие
            hole = self.hole_manager.get_hole_by_id(base_hole_id)
            if not hole:
                return
            
            # Определяем, нужно ли выделять весь массив
            if hole.repeats > 1:
                # Выделяем весь массив
                if self.visualizer:
                    self.visualizer.highlight_array(base_hole_id)
            else:
                # Выделяем одно отверстие
                if self.visualizer:
                    self.visualizer.highlight_hole(base_hole_id)
    
    def clear_selection(self) -> None:
        """Снятие выделения"""
        # Очищаем выделение на схеме
        if self.visualizer:
            self.visualizer.clear_highlights()
        
        # Очищаем выделение в таблицах
        self.ui_components['top_table'].tree.selection_remove(
            self.ui_components['top_table'].tree.selection()
        )
        self.ui_components['edge_table'].tree.selection_remove(
            self.ui_components['edge_table'].tree.selection()
        )

                # Вызывайте этот метод при:
                # - создании нового файла
                # - загрузке файла
                # - удалении всех отверстий
                # - когда нужно снять выделение
    
    def add_hole(self) -> None:
        """Добавление нового отверстия"""
        hole_type = self.get_active_tab()
        
        # Создаем диалоговое окно для добавления отверстия
        from dialogs import HoleDialog
        
        dialog = HoleDialog(
            parent=self.root,
            hole_type=hole_type,
            panel_thickness=self.panel_data['thickness'],
            on_save=self._save_hole
        )
        
        dialog.show()
    
    def copy_hole(self, event=None) -> None:
        """Копирование выбранного отверстия через диалог редактирования"""
        print("=== copy_hole вызван ===")
        
        table = self.get_active_table()
        selected = table.get_selected()
        
        if not selected:
            messagebox.showinfo("Информация", "Выберите отверстие для копирования")
            return
        
        # Извлекаем ID отверстия из первого столбца
        hole_id_str = str(selected[0])
        
        # Удаляем информацию о массиве (×3) если есть
        if '×' in hole_id_str:
            hole_id = int(hole_id_str.split('×')[0])
        else:
            try:
                hole_id = int(hole_id_str)
            except ValueError:
                messagebox.showerror("Ошибка", f"Некорректный ID отверстия: {hole_id_str}")
                return
        
        hole = self.hole_manager.get_hole_by_id(hole_id)
        
        if not hole:
            messagebox.showerror("Ошибка", f"Отверстие с ID {hole_id} не найдено")
            return
        
        # Определяем тип отверстия
        hole_type = "top" if hole.is_top_hole() else "edge"
        
        # Создаем копию данных отверстия с новым ID
        hole_data = hole.to_dict()
        hole_data['id'] = 0  # Сбрасываем ID для создания нового отверстия
        
        # Создаем диалоговое окно для копирования отверстия
        # Импортируем здесь, чтобы избежать циклических зависимостей
        from dialogs import HoleDialog
        
        dialog = HoleDialog(
            parent=self.root,
            hole_type=hole_type,
            panel_thickness=self.panel_data['thickness'],
            hole_data=hole_data,
            on_save=self._save_hole,
            title="Копировать отверстие"
        )
        
        dialog.show()
        
    def _show_copy_dialog(self, hole_type, hole_data):
        """Показ диалога копирования (вызывается через after)"""
        # Импортируем здесь, чтобы избежать циклических зависимостей
        from dialogs import HoleDialog
        
        dialog = HoleDialog(
            parent=self.root,
            hole_type=hole_type,
            panel_thickness=self.panel_data['thickness'],
            hole_data=hole_data,
            on_save=self._save_hole,
            title="Копировать отверстие"
        )
        
        print("Показываем диалог...")
        dialog.show()
        print("Диалог показан")

    def edit_selected_hole(self) -> None:
        """Редактирование выбранного отверстия (общая функция для разных способов вызова)"""
        table = self.get_active_table()
        
        # Проверяем, есть ли выделенные строки
        selection = table.tree.selection()
        if not selection:
            # Если ничего не выделено, попробуем выделить строку под курсором
            # (для случая, когда обработчик вызван не через UI)
            return
        
        # Получаем данные выделенной строки
        selected_item = selection[0]
        values = table.tree.item(selected_item)['values']
        
        if not values:
            return
        
        # Извлекаем ID отверстия из первого столбца
        hole_id_str = str(values[0])
        
        # Удаляем информацию о массиве (×3) если есть
        if '×' in hole_id_str:
            hole_id = int(hole_id_str.split('×')[0])
        else:
            try:
                hole_id = int(hole_id_str)
            except ValueError:
                return
        
        hole = self.hole_manager.get_hole_by_id(hole_id)
        
        if not hole:
            return
        
        # Определяем тип отверстия
        hole_type = "top" if hole.is_top_hole() else "edge"
        
        # Получаем полные данные отверстия
        hole_data = hole.to_dict()
        
        # Создаем диалоговое окно для редактирования
        from dialogs import HoleDialog
        
        dialog = HoleDialog(
            parent=self.root,
            hole_type=hole_type,
            panel_thickness=self.panel_data['thickness'],
            hole_data=hole_data,
            on_save=self._save_hole,
            on_delete=self._delete_hole
        )
        
        dialog.show()

    
    def edit_hole(self, event=None) -> None:
        """Редактирование выбранного отверстия (вызывается по двойному клику или кнопке)"""
        self.edit_selected_hole()
    
    def _save_hole(self, hole_data: Dict) -> None:
        """Сохранение отверстия (для добавления, редактирования и копирования)"""
        try:
            print(f"Сохраняем отверстие (после преобразования в _save_hole):")
            for key, value in hole_data.items():
                print(f"  {key}: {repr(value)} (тип: {type(value).__name__})")    
            
            # Если отверстие новое (id=0) или его нет в данных
            hole_id = hole_data.get('id', 0)
            
            if hole_id == 0:
                # Создаем новое отверстие
                new_hole = HoleFactory.create_hole(**hole_data)
                self.hole_manager.add_hole(new_hole)
            else:
                # Обновляем существующее отверстие
                self.hole_manager.update_hole(hole_data)
            
            # Добавляем цвет для нового диаметра, если его нет
            if 'diameter' in hole_data and hole_data['diameter'] not in self.diameter_colors:
                from config import generate_color
                self.diameter_colors[hole_data['diameter']] = generate_color(
                    self.diameter_colors
                )
            
            # Обновляем интерфейс
            self.hole_manager.renumber_holes()
            self.update_tables()
            self.draw_panel()
            self.update_scrollbar()
            
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении отверстия:\n{str(e)}")
            import traceback
            traceback.print_exc()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def delete_hole(self, event=None) -> None:
        """Удаление выбранного отверстия без подтверждения"""
        table = self.get_active_table()
        selected = table.get_selected()
        
        if not selected:
            return
        
        hole_id = selected[0]
        self._delete_hole(hole_id)
    
    def _delete_hole(self, hole_id: int) -> None:
        """Удаление отверстия без подтверждения"""
        # Удаление из общего списка
        self.hole_manager.remove_hole(hole_id)
        
        # Перенумеровываем все отверстия
        self.hole_manager.renumber_holes()
        
        # Обновляем таблицы и схему
        self.update_tables()
        self.draw_panel()
        self.update_scrollbar()
    
    def mirror_x(self) -> None:
        """Зеркальное отражение всех отверстий по оси X"""
        if not self.hole_manager.get_all_holes():
            messagebox.showinfo("Информация", "Нет отверстий для зеркалирования")
            return
        
        # Зеркалируем отверстия
        from geometry import mirror_holes_x
        mirrored_holes = mirror_holes_x(
            [h.to_dict() for h in self.hole_manager.get_all_holes()],
            self.panel_data['width'],
            self.panel_data['height']
        )
        
        # Заменяем отверстия
        from hole_manager import HoleFactory
        new_holes = [HoleFactory.create_hole(**h) for h in mirrored_holes]
        self.hole_manager.set_holes(new_holes)
        self.hole_manager.renumber_holes()
        
        # Обновляем интерфейс
        self.update_tables()
        self.draw_panel()
        self.update_scrollbar()
    
    def mirror_y(self) -> None:
        """Зеркальное отражение всех отверстий по оси Y"""
        if not self.hole_manager.get_all_holes():
            messagebox.showinfo("Информация", "Нет отверстий для зеркалирования")
            return
        
        # Зеркалируем отверстия
        from geometry import mirror_holes_y
        mirrored_holes = mirror_holes_y(
            [h.to_dict() for h in self.hole_manager.get_all_holes()],
            self.panel_data['width'],
            self.panel_data['height']
        )
        
        # Заменяем отверстия
        from hole_manager import HoleFactory
        new_holes = [HoleFactory.create_hole(**h) for h in mirrored_holes]
        self.hole_manager.set_holes(new_holes)
        self.hole_manager.renumber_holes()
        
        # Пересчитываем положение паза при зеркалировании по Y
        self.groove.mirror_y(self.panel_data['height'])
        if 'groove_tab' in self.ui_components:
            self.ui_components['groove_tab'].set_values(self.groove.to_dict())
         
        # Обновляем интерфейс
        self.update_tables()
        self.draw_panel()
        self.update_scrollbar()
     
    def new_file(self) -> None:
        """Создание нового файла"""
        if self.hole_manager.get_all_holes():
            if not messagebox.askyesno("Новый файл", 
                                      "Все текущие данные будут удалены. Продолжить?"):
                return
        
        # Сбрасываем к значениям по умолчанию
        self.hole_manager.clear()
        self.panel_data = DEFAULT_PANEL.copy()
        self.program_name = "DETAL"
        
        # Сбрасываем параметры паза к значениям по умолчанию
        self.groove = Groove.from_dict(DEFAULT_GROOVE)
        if 'groove_tab' in self.ui_components:
            self.ui_components['groove_tab'].set_values(self.groove.to_dict())
         
        # Обновляем поля ввода
        self.ui_components['size_controls'].set_values(
            width=self.panel_data['width'],
            height=self.panel_data['height'],
            thickness=self.panel_data['thickness'],
            program_name=self.program_name
        )
         
        # Сбрасываем цвета к значениям по умолчанию
        self.diameter_colors = DIAMETER_COLORS.copy()
         
        # Обновляем интерфейс
        self.update_tables()
        self.draw_panel()
        self.ui_components['legend'].update_legend(self.diameter_colors)
         
        messagebox.showinfo("Новый файл", "Создан новый файл с параметрами по умолчанию")
    
    def save_to_file(self) -> None:
        """Сохранение данных в файл .anc"""
        from tkinter import filedialog
        
        # Получаем текущие значения (включая название программы)
        values = self.ui_components['size_controls'].get_values()
        self.program_name = values.get('program_name', 'DETAL')
        
        # Предлагаем имя файла по умолчанию на основе названия программы
        default_filename = f"{self.program_name}.anc"
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".anc",
            initialfile=default_filename,  # Подставляем название программы
            filetypes=[
                ("Файлы присадки", "*.anc"),
                ("Текстовые файлы", "*.txt"),
                ("Все файлы", "*.*")
            ],
            title="Сохранить файл присадки"
        )
        
        if not filename:
            return
        
        try:
            # Сохраняем параметры паза
            if 'groove_tab' in self.ui_components:
                groove_values = self.ui_components['groove_tab'].get_values()
                self.groove = Groove.from_dict(groove_values)
            
            success = self.file_handler.save_to_file(
                filename=filename,
                panel_data=self.panel_data,
                holes=self.hole_manager.get_all_holes(),
                program_name=self.program_name,  # Передаем название программы
                groove=self.groove  # Передаем параметры паза
            )
             
            if success:
                messagebox.showinfo("Сохранение", f"Файл успешно сохранен:\n{filename}")
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить файл")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении файла:\n{str(e)}")
    
    def load_from_file(self) -> None:
        """Загрузка данных из файла .anc"""
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            filetypes=[
                ("Файлы присадки", "*.anc"),
                ("Текстовые файлы", "*.txt"),
                ("Все файлы", "*.*")
            ],
            title="Загрузить файл присадки"
        )
        
        if not filename:
            return
        
        try:
            # Загружаем данные из файла - теперь четыре значения
            panel_data, holes, loaded_program_name, loaded_groove = self.file_handler.load_from_file(filename)
             
            # Обновляем данные
            self.panel_data = panel_data
            self.program_name = loaded_program_name if loaded_program_name else "DETAL"
            self.hole_manager.clear()
            
            # Восстанавливаем параметры паза
            if loaded_groove is not None:
                self.groove = loaded_groove
            else:
                self.groove = Groove.from_dict(DEFAULT_GROOVE)
            if 'groove_tab' in self.ui_components:
                self.ui_components['groove_tab'].set_values(self.groove.to_dict())
             
            # Добавляем все отверстия
            for hole in holes:
                # Устанавливаем значения по умолчанию для новых полей
                if not hasattr(hole, 'repeats'):
                    hole.repeats = 1
                if not hasattr(hole, 'offset_x'):
                    hole.offset_x = 0
                if not hasattr(hole, 'offset_y'):
                    hole.offset_y = 0
                 
                self.hole_manager.add_hole(hole)
             
            # Обновляем поля ввода
            self.ui_components['size_controls'].set_values(
                width=panel_data['width'],
                height=panel_data['height'],
                thickness=panel_data['thickness'],
                program_name=self.program_name
            )
             
            # Обновляем цвета диаметров
            self._update_diameter_colors_from_holes(holes)
             
            # Обновляем интерфейс
            self.hole_manager.renumber_holes()
            self.update_tables()
            self.draw_panel()
            self.ui_components['legend'].update_legend(self.diameter_colors)
             
            messagebox.showinfo("Загрузка", f"Файл успешно загружен:\n{filename}")
             
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке файла:\n{str(e)}")
            import traceback
            traceback.print_exc()
        
    def _update_diameter_colors_from_holes(self, holes: List[Hole]) -> None:
        """Обновление цветов для диаметров на основе загруженных отверстий"""
        from config import generate_color
        
        # Получаем все уникальные диаметры
        diameters = set(hole.diameter for hole in holes)
        
        # Для каждого диаметра, которого нет в стандартных цветах, генерируем новый
        for diameter in diameters:
            if diameter not in self.diameter_colors:
                self.diameter_colors[diameter] = generate_color(self.diameter_colors)
    
    def show_help(self) -> None:
        """Показ справки"""
        from dialogs import HelpDialog
        
        help_dialog = HelpDialog(parent=self.root)
        help_dialog.show()


def main():
    """Главная функция приложения"""
    root = tk.Tk()
    app = PanelHoleVisualizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()