# visualization.py
import tkinter as tk
from typing import Dict, List, Tuple, Optional, Callable, Any

from geometry import (
    get_absolute_coordinates_top,
    get_absolute_coordinates_edge,
    calculate_scale_and_offset,
    calculate_hole_position_for_canvas,
    local_to_absolute  # Добавляем эту строку
)

from hole_manager import Hole
from config import (
    PANEL_COLOR, EDGE_COLOR, HOLE_EDGE_COLOR, HIGHLIGHT_COLOR,
    GROOVE_COLOR,
    MARGIN, ARROW_LENGTH, ARROW_WIDTH, CORNER_MARKER_SIZE,
    EDGE_TEXT_OFFSET, HOLE_HIGHLIGHT_OFFSET,
    CORNER_NAMES, CORNER_ANCHORS, EDGE_NAMES, EDGE_POSITIONS,
    CORNER_ARROWS, ARROW_X_COLOR, ARROW_Y_COLOR,
    FONT_HEADER, FONT_NORMAL, FONT_BOLD, FONT_SMALL,
    TEXT_COLOR_CORNER, TEXT_COLOR_EDGE, TEXT_COLOR_HOLE,
    CANVAS_BG_COLOR, CANVAS_HIGHLIGHT_THICKNESS, CANVAS_HIGHLIGHT_COLOR
)


class PanelVisualizer:
    """Визуализатор панели с отверстиями"""
    
    def __init__(
        self,
        canvas: tk.Canvas,
        panel_color: str = PANEL_COLOR,
        edge_color: str = EDGE_COLOR,
        hole_edge_color: str = HOLE_EDGE_COLOR,
        diameter_colors: Optional[Dict[int, str]] = None,
        corner_anchors: Optional[Dict[int, str]] = None,
        edge_positions: Optional[Dict[int, Tuple[float, float]]] = None
    ):
        self.canvas = canvas
        self.panel_color = panel_color
        self.edge_color = edge_color
        self.hole_edge_color = hole_edge_color
        self.diameter_colors = diameter_colors or {}
        self.corner_anchors = corner_anchors or CORNER_ANCHORS
        self.edge_positions = edge_positions or EDGE_POSITIONS
        
        # Состояние
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.panel_width_scaled = 0
        self.panel_height_scaled = 0
        
        # Кэш для объектов canvas
        self.canvas_hole_items = {}  # hole_id -> [item_ids]
    
    def draw_panel(
        self,
        panel_data: Dict[str, float],
        holes: List[Hole],
        groove: Any = None,
        on_hole_click: Optional[Callable[[int], None]] = None,
        on_hole_right_click: Optional[Callable[[int], None]] = None
    ) -> None:
        """
        Отрисовка панели и отверстий
         
        Args:
            panel_data: Данные панели (ширина, высота, толщина)
            holes: Список отверстий
            groove: Параметры паза (объект Groove или None)
            on_hole_click: Функция обратного вызова при клике на отверстие
            on_hole_right_click: Функция обратного вызова при правом клике на отверстие
        """
        # Очистка canvas
        self.canvas.delete("all")
        self.canvas_hole_items.clear()
         
        # Получение размеров canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
         
        if canvas_width <= 10 or canvas_height <= 10:
            return
         
        # Вычисление масштаба и смещения
        self.scale, self.offset_x, self.offset_y, self.panel_width_scaled, self.panel_height_scaled = \
            calculate_scale_and_offset(
                panel_data['width'],
                panel_data['height'],
                canvas_width,
                canvas_height,
                MARGIN
            )
         
        # Рисование панели
        self._draw_panel_outline()
         
        # Обозначение углов
        #self._draw_corners()
         
        # Обозначение кромок
        self._draw_edges()
         
        # Рисование паза (если включён)
        self._draw_groove(groove, panel_data)
         
        # Рисование отверстий
        self._draw_holes(holes, panel_data, on_hole_click, on_hole_right_click)
         
        # Легенда осей координат
        self._draw_coordinate_legends()
     
    def _draw_groove(self, groove, panel_data: Dict[str, float]) -> None:
        """
        Условная отрисовка паза на схеме детали.
        Паз центрируется по ширине панели, центр Y = YPAZ от верха.

        Args:
            groove: Параметры паза (объект Groove) или None
            panel_data: Данные панели
        """
        if not groove or not groove.enabled:
            return
        
        try:
            panel_width = panel_data['width']
            
            # Центр паза по X - по середине ширины панели
            center_x = panel_width / 2.0
            # Центр паза по Y - от верха
            center_y = groove.y_pos
            
            # Габариты паза
            half_length = groove.length / 2.0
            half_width = groove.width / 2.0
            
            # Абсолютные координаты прямоугольника
            x1 = center_x - half_length
            y1 = center_y - half_width
            x2 = center_x + half_length
            y2 = center_y + half_width
            
            # Координаты на canvas
            c_x1 = self.offset_x + x1 * self.scale
            c_y1 = self.offset_y + y1 * self.scale
            c_x2 = self.offset_x + x2 * self.scale
            c_y2 = self.offset_y + y2 * self.scale
            
            # Отрисовка паза
            self.canvas.create_rectangle(
                c_x1, c_y1, c_x2, c_y2,
                fill=GROOVE_COLOR,
                outline=EDGE_COLOR,
                width=1,
                tags=("groove",)
            )
            
            # Подпись с размерами паза
            self.canvas.create_text(
                self.offset_x + center_x * self.scale,
                c_y1 - 8,
                text=f"Паз: L={groove.length:.0f} W={groove.width:.0f} "
                     f"Z={groove.depth:.0f} Y={groove.y_pos:.0f}",
                font=FONT_SMALL,
                fill=TEXT_COLOR_HOLE,
                anchor=tk.S,
                tags=("groove",)
            )
        except Exception as e:
            print(f"Ошибка при отрисовке паза: {e}")
    
    def _draw_panel_outline(self) -> None:
        """Отрисовка контура панели"""
        self.canvas.create_rectangle(
            self.offset_x,
            self.offset_y,
            self.offset_x + self.panel_width_scaled,
            self.offset_y + self.panel_height_scaled,
            fill=self.panel_color,
            outline=self.edge_color,
            width=3
        )
    
    def _draw_corners(self) -> None:
        """Отрисовка обозначений углов"""
        corners = [
            (self.offset_x, self.offset_y, 1),
            (self.offset_x, self.offset_y + self.panel_height_scaled, 2),
            (self.offset_x + self.panel_width_scaled,
             self.offset_y + self.panel_height_scaled, 3),
            (self.offset_x + self.panel_width_scaled,
             self.offset_y, 4)
        ]
        
        for x, y, corner_num in corners:
            anchor = self.corner_anchors.get(corner_num, "center")
            text = CORNER_NAMES.get(corner_num, f"Угол {corner_num}")
            
            self.canvas.create_text(
                x, y,
                text=text,
                font=FONT_BOLD,
                fill=TEXT_COLOR_CORNER,
                anchor=anchor
            )
    
    def _draw_edges(self) -> None:
        """Отрисовка обозначений кромок"""
        edges = [
            # Левая кромка
            ((self.offset_x, self.offset_y,
              self.offset_x, self.offset_y + self.panel_height_scaled), 1),
            # Нижняя кромка
            ((self.offset_x, self.offset_y + self.panel_height_scaled,
              self.offset_x + self.panel_width_scaled,
              self.offset_y + self.panel_height_scaled), 2),
            # Правая кромка
            ((self.offset_x + self.panel_width_scaled, self.offset_y,
              self.offset_x + self.panel_width_scaled,
              self.offset_y + self.panel_height_scaled), 3),
            # Верхняя кромка
            ((self.offset_x, self.offset_y,
              self.offset_x + self.panel_width_scaled, self.offset_y), 4)
        ]
        
        for (x1, y1, x2, y2), edge_num in edges:
            # Координаты середины кромки
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            
            # Получаем позицию текста относительно кромки
            pos_x, pos_y = self.edge_positions.get(edge_num, (0.5, 0.5))
            
            # Вычисляем смещение текста
            if edge_num == 1:  # Левая
                text_x = mid_x - EDGE_TEXT_OFFSET
                text_y = mid_y
                anchor = "e"
            elif edge_num == 2:  # Нижняя
                text_x = mid_x
                text_y = mid_y + EDGE_TEXT_OFFSET
                anchor = "n"
            elif edge_num == 3:  # Правая
                text_x = mid_x + EDGE_TEXT_OFFSET
                text_y = mid_y
                anchor = "w"
            else:  # Верхняя
                text_x = mid_x
                text_y = mid_y - EDGE_TEXT_OFFSET
                anchor = "s"
            
            text = EDGE_NAMES.get(edge_num, f"Кромка {edge_num}")
            
            self.canvas.create_text(
                text_x, text_y,
                text=text,
                font=FONT_NORMAL,
                fill=TEXT_COLOR_EDGE,
                anchor=anchor
            )
    
    def _draw_holes(
        self,
        holes: List[Hole],
        panel_data: Dict[str, float],
        on_hole_click: Optional[Callable[[int], None]] = None,
        on_hole_right_click: Optional[Callable[[int], None]] = None
    ) -> None:
        """Отрисовка отверстий"""
        for hole in holes:
            if hole.is_top_hole():
                self._draw_top_hole(hole, panel_data, on_hole_click, on_hole_right_click)
            else:
                self._draw_edge_hole(hole, panel_data, on_hole_click, on_hole_right_click)
    
    def _draw_top_hole(
        self,
        hole: Hole,
        panel_data: Dict[str, float],
        on_hole_click: Optional[Callable[[int], None]] = None,
        on_hole_right_click: Optional[Callable[[int], None]] = None
    ) -> None:
        """Отрисовка отверстия в плоскости с локальными координатами"""
        try:
            # Преобразуем значения к нужным типам
            x_local = float(hole.x_local) if not isinstance(hole.x_local, (int, float)) else float(hole.x_local)
            y_local = float(hole.y_local) if not isinstance(hole.y_local, (int, float)) else float(hole.y_local)
            
            # Получаем базовые координаты
            hole_dict = {
                'corner': hole.corner.value,
                'x': x_local,
                'y': y_local
            }
            
            abs_x, abs_y = get_absolute_coordinates_top(
                hole_dict,
                panel_data['width'],
                panel_data['height']
            )
            
            # Преобразуем смещения к числам
            offset_x_local = float(hole.offset_x_local) if not isinstance(hole.offset_x_local, (int, float)) else float(hole.offset_x_local)
            offset_y_local = float(hole.offset_y_local) if not isinstance(hole.offset_y_local, (int, float)) else float(hole.offset_y_local)
            
            # Создаем список всех позиций в массиве
            positions = []
            for i in range(hole.repeats):
                if i == 0:
                    positions.append((abs_x, abs_y))
                else:
                    # Применяем смещения
                    offset_x = offset_x_local * i
                    offset_y = offset_y_local * i
                    
                    # Для каждого угла по-разному применяем смещения
                    if hole.corner.value == 1:  # ВЛ
                        pos_x = abs_x + offset_x
                        pos_y = abs_y + offset_y
                    elif hole.corner.value == 2:  # НЛ
                        pos_x = abs_x + offset_x
                        pos_y = abs_y - offset_y  # Y вверх от нижнего края
                    elif hole.corner.value == 3:  # НП
                        pos_x = abs_x - offset_x  # X влево
                        pos_y = abs_y - offset_y  # Y вверх
                    elif hole.corner.value == 4:  # ВП
                        pos_x = abs_x - offset_x  # X влево
                        pos_y = abs_y + offset_y
                    else:
                        pos_x = abs_x + offset_x
                        pos_y = abs_y + offset_y
                    
                    positions.append((pos_x, pos_y))
            
            # Отрисовываем все отверстия в массиве
            for i, (pos_x, pos_y) in enumerate(positions):
                # Координаты на canvas
                x, y = calculate_hole_position_for_canvas(
                    pos_x, pos_y,
                    self.scale,
                    self.offset_x,
                    self.offset_y
                )
                
                # Диаметр на canvas
                diameter = hole.diameter * self.scale
                
                # Цвет отверстия
                color = self.diameter_colors.get(hole.diameter, "#888888")
                
                # ID для этого конкретного отверстия в массиве
                hole_instance_id = f"{hole.id}_{i}" if i > 0 else f"{hole.id}"
                
                # Отрисовка отверстия
                oval_id = self.canvas.create_oval(
                    x - diameter/2, y - diameter/2,
                    x + diameter/2, y + diameter/2,
                    fill=color,
                    outline=self.hole_edge_color,
                    width=1,
                    tags=(f"hole_{hole.id}", f"hole_instance_{hole_instance_id}", 
                          "hole", "top_hole", f"array_{hole.id}")
                )
                
                # Сохраняем ссылку на объект canvas
                if hole.id not in self.canvas_hole_items:
                    self.canvas_hole_items[hole.id] = []
                self.canvas_hole_items[hole.id].append(oval_id)
                
                # Номер отверстия (только для первого или если массив небольшой)
                if i == 0 or len(positions) <= 3:
                    text_offset = diameter/2 + 10
                    text_id = self.canvas.create_text(
                        x + text_offset, y,
                        text=str(hole.id) if i == 0 else f"{hole.id}.{i+1}",
                        font=FONT_BOLD,
                        fill=TEXT_COLOR_HOLE,
                        tags=(f"hole_{hole.id}", f"hole_instance_{hole_instance_id}", 
                              "hole_text", "top_hole")
                    )
                
                # Центральный крестик
                # cross_size = min(8, diameter/3)
                # cross1_id = self.canvas.create_line(
                    # x - cross_size, y,
                    # x + cross_size, y,
                    # fill='white',
                    # width=1,
                    # tags=(f"hole_{hole.id}", f"hole_instance_{hole_instance_id}", 
                          # "hole_cross", "top_hole")
                # )
                
                # Привязка события левого клика
                if on_hole_click:
                    self.canvas.tag_bind(
                        f"hole_instance_{hole_instance_id}",
                        "<Button-1>",
                        lambda e, h_id=hole.id: on_hole_click(h_id)
                    )
                
                # Привязка события правого клика
                if on_hole_right_click:
                    self.canvas.tag_bind(
                        f"hole_instance_{hole_instance_id}",
                        "<Button-3>",
                        lambda e, h_id=hole.id: on_hole_right_click(h_id)
                    )
                    
                    # Также для macOS
                    self.canvas.tag_bind(
                        f"hole_instance_{hole_instance_id}",
                        "<Button-2>",
                        lambda e, h_id=hole.id: on_hole_right_click(h_id)
                    )
        except Exception as e:
            print(f"Ошибка при отрисовке отверстия {hole.id}: {e}")
            import traceback
            traceback.print_exc()


    def _draw_edge_hole(
        self,
        hole: Hole,
        panel_data: Dict[str, float],
        on_hole_click: Optional[Callable[[int], None]],
        on_hole_right_click: Optional[Callable[[int], None]]  # Добавим параметр
    ) -> None:
        """Отрисовка отверстия в кромке (с поддержкой массива)"""
        try:
            # Преобразуем все значения к нужным типам
            depth = float(hole.depth) if not isinstance(hole.depth, (int, float)) else float(hole.depth)
            diameter = int(hole.diameter) if not isinstance(hole.diameter, int) else hole.diameter
            x_local = float(hole.x_local) if not isinstance(hole.x_local, (int, float)) else float(hole.x_local)
            z_local = float(hole.z_local) if not isinstance(hole.z_local, (int, float)) else float(hole.z_local)
            
            # Создаем словарь для передачи в get_absolute_coordinates_edge
            hole_dict = {
                'corner': hole.corner.value,
                'edge': hole.edge.value,
                'x': x_local,   # координата вдоль кромки
                'z': z_local,
                'depth': depth,
                'diameter': diameter
            }
            
            abs_x, abs_y, width, height, orientation, rect_x1, rect_y1, rect_x2, rect_y2 = \
                get_absolute_coordinates_edge(
                    hole_dict,
                    panel_data['width'],
                    panel_data['height'],
                    panel_data['thickness']
                )
            
            # Координаты прямоугольника на canvas
            rect_x1_scaled = self.offset_x + rect_x1 * self.scale
            rect_y1_scaled = self.offset_y + rect_y1 * self.scale
            rect_x2_scaled = self.offset_x + rect_x2 * self.scale
            rect_y2_scaled = self.offset_y + rect_y2 * self.scale
            
            # Центр отверстия на canvas
            x, y = calculate_hole_position_for_canvas(
                abs_x, abs_y,
                self.scale,
                self.offset_x,
                self.offset_y
            )
            
            # Цвет отверстия
            color = self.diameter_colors.get(diameter, "#888888")
            
            # Отрисовка прямоугольника
            rect_id = self.canvas.create_rectangle(
                rect_x1_scaled, rect_y1_scaled,
                rect_x2_scaled, rect_y2_scaled,
                fill=color,
                outline=self.hole_edge_color,
                width=1,
                tags=(f"hole_{hole.id}", "hole", "edge_hole", f"array_{hole.id}")
            )
            
            # Номер отверстия
            width_scaled = width * self.scale
            height_scaled = height * self.scale
            text_offset = max(width_scaled, height_scaled)/2 + 10
            
            if orientation == "vertical":
                text_x = x + text_offset
                text_y = y
            else:
                text_x = x
                text_y = y - text_offset
            
            # Добавляем информацию о массиве в подпись
            array_info = f" ×{hole.repeats}" if hole.repeats > 1 else ""
            
            text_id = self.canvas.create_text(
                text_x, text_y,
                text=f"{hole.id}{array_info}",
                font=FONT_BOLD,
                fill=TEXT_COLOR_HOLE,
                tags=(f"hole_{hole.id}", "hole_text", "edge_hole")
            )
            
            # Центральный крестик
            cross_size = min(8, min(width_scaled, height_scaled)/3)
            cross1_id = self.canvas.create_line(
                x - cross_size, y,
                x + cross_size, y,
                fill='white',
                width=1,
                tags=(f"hole_{hole.id}", "hole_cross", "edge_hole")
            )
            
            # Привязка события левого клика
            if on_hole_click:
                self.canvas.tag_bind(
                    f"hole_{hole.id}",
                    "<Button-1>",
                    lambda e, h_id=hole.id: on_hole_click(h_id)
                )
            
            # Привязка события правого клика
            if on_hole_right_click:
                self.canvas.tag_bind(
                    f"hole_{hole.id}",
                    "<Button-3>",
                    lambda e, h_id=hole.id: on_hole_right_click(h_id)
                )
        except Exception as e:
            print(f"Ошибка при отрисовке отверстия в кромке {hole.id}: {e}")
            import traceback
            traceback.print_exc()
    
# visualization.py - обновим метод _draw_coordinate_legends

# visualization.py - упрощенная версия без фона

    def _draw_coordinate_legends(self) -> None:
        """Отрисовка текстовых подписей для каждого угла (без графических стрелок)"""
        from config import CORNER_TEXTS
        
        for corner_num, corner_info in CORNER_TEXTS.items():
            # Координаты угла панели
            if corner_num == 1:  # Верхний левый
                x = self.offset_x 
                y = self.offset_y - 15  # Над панелью
            elif corner_num == 2:  # Нижний левый
                x = self.offset_x 
                y = self.offset_y + self.panel_height_scaled + 15  # Под панелью
            elif corner_num == 3:  # Нижний правый
                x = self.offset_x + self.panel_width_scaled 
                y = self.offset_y + self.panel_height_scaled + 15  # Под панелью
            else:  # corner_num == 4 - Верхний правый
                x = self.offset_x + self.panel_width_scaled 
                y = self.offset_y - 15  # Над панелью
            
            # Получаем текст и якорь из конфигурации
            display_text = corner_info["text"]
            text_anchor = corner_info["anchor"]
            
            # Текст подписи угла
            self.canvas.create_text(
                x, y,
                text=display_text,
                font=FONT_SMALL,
                fill='darkblue',  # Можно изменить цвет
                anchor=text_anchor,
                tags="coordinate_legend"
            )
    
# visualization.py - добавьте эти методы в класс PanelVisualizer

    def highlight_hole(self, hole_id: int) -> None:
        """
        Подсветка отверстия на схеме
        
        Args:
            hole_id: ID отверстия для подсветки
        """
        # Удаляем предыдущее выделение
        self.clear_highlights()
        
        # Получаем отверстие из менеджера (нужно передать его или получить доступ)
        # Для этого метода потребуется доступ к списку отверстий
        # Вместо этого будем использовать find_withtag для поиска всех отверстий с данным ID
        
        # Ищем все объекты с тегом hole_{hole_id}
        hole_tag = f"hole_{hole_id}"
        hole_items = self.canvas.find_withtag(hole_tag)
        
        # Также ищем отверстия массива, если они есть
        array_tag = f"array_{hole_id}"
        array_items = self.canvas.find_withtag(array_tag)
        
        # Объединяем все объекты для подсветки
        all_items = list(hole_items) + list(array_items)
        
        if not all_items:
            return
        
        # Подсвечиваем каждый объект
        for item_id in all_items:
            # Получаем тип объекта
            item_type = self.canvas.type(item_id)
            
            # Получаем координаты
            coords = self.canvas.coords(item_id)
            
            if len(coords) == 4:  # Прямоугольник или овал
                x1, y1, x2, y2 = coords
                
                # Создаем подсветку вокруг объекта
                if item_type == "oval":
                    # Для круга
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    radius = (x2 - x1) / 2
                    
                    self.canvas.create_oval(
                        center_x - radius - HOLE_HIGHLIGHT_OFFSET,
                        center_y - radius - HOLE_HIGHLIGHT_OFFSET,
                        center_x + radius + HOLE_HIGHLIGHT_OFFSET,
                        center_y + radius + HOLE_HIGHLIGHT_OFFSET,
                        outline=HIGHLIGHT_COLOR,
                        width=3,
                        tags=("highlight", f"highlight_hole_{hole_id}")
                    )
                elif item_type == "rectangle":
                    # Для прямоугольника
                    self.canvas.create_rectangle(
                        x1 - HOLE_HIGHLIGHT_OFFSET,
                        y1 - HOLE_HIGHLIGHT_OFFSET,
                        x2 + HOLE_HIGHLIGHT_OFFSET,
                        y2 + HOLE_HIGHLIGHT_OFFSET,
                        outline=HIGHLIGHT_COLOR,
                        width=3,
                        tags=("highlight", f"highlight_hole_{hole_id}")
                    )

    def highlight_array(self, base_hole_id: int) -> None:
        """
        Подсветка всего массива отверстий
        
        Args:
            base_hole_id: Базовый ID массива отверстий
        """
        # Удаляем предыдущее выделение
        self.clear_highlights()
        
        # Ищем все объекты с тегом array_{base_hole_id}
        array_tag = f"array_{base_hole_id}"
        array_items = self.canvas.find_withtag(array_tag)
        
        if not array_items:
            # Если не нашли массив, подсвечиваем просто отверстие
            self.highlight_hole(base_hole_id)
            return
        
        # Подсвечиваем каждый объект массива
        for item_id in array_items:
            # Получаем тип объекта
            item_type = self.canvas.type(item_id)
            
            # Получаем координаты
            coords = self.canvas.coords(item_id)
            
            if len(coords) == 4:  # Прямоугольник или овал
                x1, y1, x2, y2 = coords
                
                # Создаем подсветку вокруг объекта
                if item_type == "oval":
                    # Для круга
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    radius = (x2 - x1) / 2
                    
                    self.canvas.create_oval(
                        center_x - radius - HOLE_HIGHLIGHT_OFFSET,
                        center_y - radius - HOLE_HIGHLIGHT_OFFSET,
                        center_x + radius + HOLE_HIGHLIGHT_OFFSET,
                        center_y + radius + HOLE_HIGHLIGHT_OFFSET,
                        outline=HIGHLIGHT_COLOR,
                        width=3,
                        tags=("highlight", f"highlight_array_{base_hole_id}")
                    )
                elif item_type == "rectangle":
                    # Для прямоугольника
                    self.canvas.create_rectangle(
                        x1 - HOLE_HIGHLIGHT_OFFSET,
                        y1 - HOLE_HIGHLIGHT_OFFSET,
                        x2 + HOLE_HIGHLIGHT_OFFSET,
                        y2 + HOLE_HIGHLIGHT_OFFSET,
                        outline=HIGHLIGHT_COLOR,
                        width=3,
                        tags=("highlight", f"highlight_array_{base_hole_id}")
                    )

    def clear_highlights(self) -> None:
        """Очистка всех выделений"""
        self.canvas.delete("highlight")
    

    
    def get_hole_at_position(self, x: float, y: float) -> Optional[int]:
        """
        Получение ID отверстия в заданной позиции
        
        Args:
            x: Координата X на canvas
            y: Координата Y на canvas
            
        Returns:
            ID отверстия или None
        """
        # Находим все объекты в заданной позиции
        items = self.canvas.find_overlapping(x, y, x, y)
        
        # Ищем отверстия среди найденных объектов
        for item_id in items:
            tags = self.canvas.gettags(item_id)
            
            # Ищем тег отверстия
            for tag in tags:
                if tag.startswith("hole_"):
                    # Извлекаем ID из тега
                    try:
                        return int(tag.split("_")[1])
                    except (IndexError, ValueError):
                        continue
        
        return None