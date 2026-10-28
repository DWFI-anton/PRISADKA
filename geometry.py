# geometry.py
import re
import math
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from config import ALLOWED_EXPRESSION_CHARS


class Corner(Enum):
    """Перечисление для углов"""
    TOP_LEFT = 1
    BOTTOM_LEFT = 2
    BOTTOM_RIGHT = 3
    TOP_RIGHT = 4


class Edge(Enum):
    """Перечисление для кромок"""
    LEFT = 1
    BOTTOM = 2
    RIGHT = 3
    TOP = 4


@dataclass
class Point:
    """Класс для представления точки в 2D пространстве"""
    x: float
    y: float
    
    def __add__(self, other: 'Point') -> 'Point':
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Point') -> 'Point':
        return Point(self.x - other.x, self.y - other.y)
    
    def scale(self, factor: float) -> 'Point':
        return Point(self.x * factor, self.y * factor)
    
    def translate(self, dx: float, dy: float) -> 'Point':
        return Point(self.x + dx, self.y + dy)


@dataclass
class Rectangle:
    """Класс для представления прямоугольника"""
    x: float
    y: float
    width: float
    height: float
    
    @property
    def left(self) -> float:
        return self.x
    
    @property
    def right(self) -> float:
        return self.x + self.width
    
    @property
    def top(self) -> float:
        return self.y
    
    @property
    def bottom(self) -> float:
        return self.y + self.height
    
    @property
    def center(self) -> Point:
        return Point(self.x + self.width/2, self.y + self.height/2)


def evaluate_expression(expr_str: Union[str, int, float, None]) -> float:
    """
    Безопасное вычисление арифметического выражения
    
    Args:
        expr_str: Строка с выражением или число
        
    Returns:
        Результат вычисления
        
    Raises:
        ValueError: Если выражение некорректно
    """
    if expr_str is None:
        return 0
    
    # Если уже число, возвращаем его
    if isinstance(expr_str, (int, float)):
        return float(expr_str)
    
    expr = str(expr_str).strip()
    
    if expr == "":
        return 0
    
    # Заменяем запятые на точки для десятичных чисел
    expr = expr.replace(',', '.')
    
    # Проверяем, что выражение содержит только разрешенные символы
    if not all(c in ALLOWED_EXPRESSION_CHARS for c in expr):
        raise ValueError(f"Выражение содержит недопустимые символы: {expr}")
    
    try:
        # Вычисляем выражение в безопасном контексте
        result = eval(expr, {"__builtins__": {}}, {
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "pi": math.pi,
            "e": math.e
        })
        
        # Проверяем, что результат - число
        if isinstance(result, (int, float)):
            return float(result)
        else:
            raise ValueError(f"Результат не является числом: {result}")
        
    except ZeroDivisionError:
        raise ValueError(f"Деление на ноль в выражении: {expr}")
    except Exception as e:
        raise ValueError(f"Ошибка вычисления выражения '{expr}': {str(e)}")


def calculate_scale_and_offset(
    panel_width: float,
    panel_height: float,
    canvas_width: float,
    canvas_height: float,
    margin: float = 80
) -> Tuple[float, float, float, float]:
    """
    Вычисление масштаба и смещения для отрисовки панели на canvas
    
    Args:
        panel_width: Ширина панели
        panel_height: Высота панели
        canvas_width: Ширина canvas
        canvas_height: Высота canvas
        margin: Отступ от краев
        
    Returns:
        (scale, offset_x, offset_y, panel_width_scaled, panel_height_scaled)
    """
    if canvas_width <= 10 or canvas_height <= 10:
        return 1.0, 0, 0, panel_width, panel_height
    
    # Сохранение пропорций панели
    panel_ratio = panel_width / panel_height
    canvas_ratio = canvas_width / canvas_height
    
    if panel_ratio > canvas_ratio:
        # Ограничение по ширине
        scale = (canvas_width - 2 * margin) / panel_width
        panel_width_scaled = panel_width * scale
        panel_height_scaled = panel_height * scale
    else:
        # Ограничение по высоте
        scale = (canvas_height - 2 * margin) / panel_height
        panel_width_scaled = panel_width * scale
        panel_height_scaled = panel_height * scale
    
    # Центрирование
    offset_x = (canvas_width - panel_width_scaled) / 2
    offset_y = (canvas_height - panel_height_scaled) / 2
    
    return scale, offset_x, offset_y, panel_width_scaled, panel_height_scaled


def local_to_absolute(
    corner: int,
    edge: int,
    x_local: float,
    y_local: float,
    z_local: float,
    panel_width: float,
    panel_height: float,
    is_edge_hole: bool = False
) -> Dict[str, float]:
    """
    Преобразование локальных координат в абсолютные (для отображения)
    
    Args:
        corner: Базовый угол (1-4)
        edge: Базовая кромка (1-4)
        x_local: Локальная координата X
        y_local: Локальная координата Y
        z_local: Локальная координата Z
        panel_width: Ширина панели
        panel_height: Высота панели
        is_edge_hole: True для отверстий в кромках
        
    Returns:
        Словарь с абсолютными координатами
    """
    if is_edge_hole:
        # Для отверстий в кромках преобразуем отдельно
        return _local_to_absolute_edge(corner, edge, x_local, z_local, panel_width, panel_height)
    else:
        # Для отверстий в плоскости
        return _local_to_absolute_top(corner, x_local, y_local, panel_width, panel_height)


def _local_to_absolute_top(
    corner: int,
    x_local: float,
    y_local: float,
    panel_width: float,
    panel_height: float
) -> Dict[str, float]:
    """Преобразование для отверстий в плоскости"""
    if corner == 1:  # ВЛ
        return {'x': x_local, 'y': y_local}
    elif corner == 2:  # НЛ
        return {'x': x_local, 'y': panel_height - y_local}
    elif corner == 3:  # НП
        return {'x': panel_width - x_local, 'y': panel_height - y_local}
    elif corner == 4:  # ВП
        return {'x': panel_width - x_local, 'y': y_local}
    else:
        return {'x': x_local, 'y': y_local}


def _local_to_absolute_edge(
    corner: int,
    edge: int,
    x_local: float,  # Координата вдоль кромки
    z_local: float,  # Глубина от верха
    panel_width: float,
    panel_height: float
) -> Dict[str, float]:
    """Преобразование для отверстий в кромках"""
    # Базовая логика такая же, но нужно учитывать кромку
    if edge == 1:  # Левая кромка
        if corner == 1:  # От ВЛ
            return {'x': 0, 'y': x_local, 'z': z_local}
        elif corner == 2:  # От НЛ
            return {'x': 0, 'y': panel_height - x_local, 'z': z_local}
    elif edge == 2:  # Нижняя кромка
        if corner == 2:  # От НЛ
            return {'x': x_local, 'y': panel_height, 'z': z_local}
        elif corner == 3:  # От НП
            return {'x': panel_width - x_local, 'y': panel_height, 'z': z_local}
    elif edge == 3:  # Правая кромка
        if corner == 3:  # От НП
            return {'x': panel_width, 'y': panel_height - x_local, 'z': z_local}
        elif corner == 4:  # От ВП
            return {'x': panel_width, 'y': x_local, 'z': z_local}
    elif edge == 4:  # Верхняя кромка
        if corner == 4:  # От ВП
            return {'x': panel_width - x_local, 'y': 0, 'z': z_local}
        elif corner == 1:  # От ВЛ
            return {'x': x_local, 'y': 0, 'z': z_local}
    
    return {'x': 0, 'y': 0, 'z': z_local}

def get_absolute_coordinates_top(
    hole: Dict[str, Any],
    panel_width: float,
    panel_height: float
) -> Tuple[float, float]:
    """
    Преобразование координат для отверстий в плоскости
    
    Args:
        hole: Данные отверстия
        panel_width: Ширина панели
        panel_height: Высота панели
        
    Returns:
        Абсолютные координаты (x, y)
    """
    corner = hole.get("corner", 1)
    
    try:
        x_expr = hole.get("x_expr", hole.get("x", 0))
        y_expr = hole.get("y_expr", hole.get("y", 0))
        
        x = evaluate_expression(x_expr)
        y = evaluate_expression(y_expr)
    except ValueError:
        x = hole.get("x", 0)
        y = hole.get("y", 0)
    
    if corner == 1:  # Верхний левый
        abs_x = x
        abs_y = y
    elif corner == 2:  # Нижний левый
        abs_x = x
        abs_y = panel_height - y
    elif corner == 3:  # Нижний правый
        abs_x = panel_width - x
        abs_y = panel_height - y
    elif corner == 4:  # Верхний правый
        abs_x = panel_width - x
        abs_y = y
    else:
        abs_x = 0
        abs_y = 0
        
    return abs_x, abs_y


def get_absolute_coordinates_edge(
    hole: Dict[str, Any],
    panel_width: float,
    panel_height: float,
    panel_thickness: float
) -> Tuple[float, float, float, float, str, float, float, float, float]:
    """
    Преобразование координат для отверстий в кромках
    
    Args:
        hole: Данные отверстия
        panel_width: Ширина панели
        panel_height: Высота панели
        panel_thickness: Толщина панели (не используется для ограничения глубины)
        
    Returns:
        (abs_x, abs_y, width, height, orientation, rect_x1, rect_y1, rect_x2, rect_y2)
    """
    edge = hole.get("edge", 1)
    corner = hole.get("corner", 1)
    
    try:
        x_expr = hole.get("x_expr", hole.get("x", 0))
        z_expr = hole.get("z_expr", hole.get("z", 0))
        
        x = evaluate_expression(x_expr)
        z = evaluate_expression(z_expr)
    except ValueError:
        x = hole.get("x", 0)
        z = hole.get("z", 0)
    
    # Глубина отверстия - без ограничений, может быть любой
    depth = hole.get("depth", 10)
    diameter = hole.get("diameter", 8)
    
    # Для отрисовки ограничиваем видимую глубину толщиной панели,
    # но в данных сохраняется полная глубина
    draw_depth = min(depth, panel_thickness * 2)  # Можно показывать чуть больше толщины для наглядности
    
    # Определяем начальную точку и направление
    if edge == 1:  # Левая кромка
        if corner == 1:  # От верхнего левого угла
            abs_x = 0
            abs_y = x  # Отсчет сверху вниз
            width = draw_depth  # Глубина вправо (X-направление) для отрисовки
            height = diameter
            orientation = "vertical"
            rect_x1 = 0
            rect_y1 = abs_y - height/2
            rect_x2 = width
            rect_y2 = abs_y + height/2
        elif corner == 2:  # От нижнего левого угла
            abs_x = 0
            abs_y = panel_height - x  # Отсчет снизу вверх
            width = draw_depth
            height = diameter
            orientation = "vertical"
            rect_x1 = 0
            rect_y1 = abs_y - height/2
            rect_x2 = width
            rect_y2 = abs_y + height/2
            
    elif edge == 2:  # Нижняя кромка
        if corner == 2:  # От нижнего левого угла
            abs_x = x  # Отсчет слева направо
            abs_y = panel_height
            width = diameter
            height = draw_depth  # Глубина вверх (Y-направление) для отрисовки
            orientation = "horizontal"
            rect_x1 = abs_x - width/2
            rect_y1 = panel_height - height
            rect_x2 = abs_x + width/2
            rect_y2 = panel_height
        elif corner == 3:  # От нижнего правого угла
            abs_x = panel_width - x  # Отсчет справа налево
            abs_y = panel_height
            width = diameter
            height = draw_depth
            orientation = "horizontal"
            rect_x1 = abs_x - width/2
            rect_y1 = panel_height - height
            rect_x2 = abs_x + width/2
            rect_y2 = panel_height
            
    elif edge == 3:  # Правая кромка
        if corner == 3:  # От нижнего правого угла
            abs_x = panel_width
            abs_y = panel_height - x  # Отсчет снизу вверх
            width = draw_depth  # Глубина влево (X-направление) для отрисовки
            height = diameter
            orientation = "vertical"
            rect_x1 = panel_width - width
            rect_y1 = abs_y - height/2
            rect_x2 = panel_width
            rect_y2 = abs_y + height/2
        elif corner == 4:  # От верхнего правого угла
            abs_x = panel_width
            abs_y = x  # Отсчет сверху вниз
            width = draw_depth
            height = diameter
            orientation = "vertical"
            rect_x1 = panel_width - width
            rect_y1 = abs_y - height/2
            rect_x2 = panel_width
            rect_y2 = abs_y + height/2
            
    elif edge == 4:  # Верхняя кромка
        if corner == 4:  # От верхнего правого угла
            abs_x = panel_width - x  # Отсчет справа налево
            abs_y = 0
            width = diameter
            height = draw_depth  # Глубина вниз (Y-направление) для отрисовки
            orientation = "horizontal"
            rect_x1 = abs_x - width/2
            rect_y1 = 0
            rect_x2 = abs_x + width/2
            rect_y2 = height
        elif corner == 1:  # От верхнего левого угла
            abs_x = x  # Отсчет слева направо
            abs_y = 0
            width = diameter
            height = draw_depth
            orientation = "horizontal"
            rect_x1 = abs_x - width/2
            rect_y1 = 0
            rect_x2 = abs_x + width/2
            rect_y2 = height
            
    else:
        abs_x = 0
        abs_y = 0
        width = 0
        height = 0
        orientation = "horizontal"
        rect_x1 = 0
        rect_y1 = 0
        rect_x2 = 0
        rect_y2 = 0
        
    return abs_x, abs_y, width, height, orientation, rect_x1, rect_y1, rect_x2, rect_y2


def is_edge_hole(hole: Dict[str, Any]) -> bool:
    """
    Определение, является ли отверстие отверстием в кромке
    
    Args:
        hole: Данные отверстия
        
    Returns:
        True если отверстие в кромке, False если в плоскости
    """
    # Проверяем наличие явного признака отверстия в кромке - наличие координаты Z
    has_z_expr = "z_expr" in hole and hole["z_expr"] != ""
    has_z_value = "z" in hole and hole["z"] != 0
    
    # Проверяем наличие координаты Y для отверстий в плоскости
    has_y_expr = "y_expr" in hole and hole["y_expr"] != ""
    has_y_value = "y" in hole and hole["y"] != 0
    
    # Если есть координата Z (выражение или значение), то это отверстие в кромке
    if has_z_expr or has_z_value:
        return True
    
    # Если есть координата Y, то это отверстие в плоскости
    if has_y_expr or has_y_value:
        return False
    
    # По умолчанию считаем отверстием в плоскости
    return False


def mirror_holes_x(
    holes: List[Dict[str, Any]],
    panel_width: float,
    panel_height: float
) -> List[Dict[str, Any]]:
    """
    Зеркальное отражение всех отверстий по оси X
    """
    mirrored_holes = []
    
    for hole in holes:
        new_hole = hole.copy()
        
        # Меняем угол
        corner = hole.get("corner", 1)
        if corner == 1:
            new_hole["corner"] = 4  # ВЛ → ВП
        elif corner == 2:
            new_hole["corner"] = 3  # НЛ → НП
        elif corner == 3:
            new_hole["corner"] = 2  # НП → НЛ
        elif corner == 4:
            new_hole["corner"] = 1  # ВП → ВЛ
        
        # Для отверстий в кромках меняем кромку
        if "edge" in hole:
            edge = hole.get("edge", 1)
            if edge == 1:  # Левая → правая
                new_hole["edge"] = 3
            elif edge == 3:  # Правая → левая
                new_hole["edge"] = 1
            # Верхняя и нижняя остаются теми же
        
        # Не меняем знак смещений! Они остаются положительными в локальной системе нового угла
        
        mirrored_holes.append(new_hole)
    
    return mirrored_holes


def mirror_holes_y(
    holes: List[Dict[str, Any]],
    panel_width: float,
    panel_height: float
) -> List[Dict[str, Any]]:
    """
    Зеркальное отражение всех отверстий по оси Y
    """
    mirrored_holes = []
    
    for hole in holes:
        new_hole = hole.copy()
        
        # Меняем угол
        corner = hole.get("corner", 1)
        if corner == 1:
            new_hole["corner"] = 2  # ВЛ → НЛ
        elif corner == 2:
            new_hole["corner"] = 1  # НЛ → ВЛ
        elif corner == 3:
            new_hole["corner"] = 4  # НП → ВП
        elif corner == 4:
            new_hole["corner"] = 3  # ВП → НП
        
        # Для отверстий в кромках меняем кромку
        if "edge" in hole:
            edge = hole.get("edge", 1)
            if edge == 2:  # Нижняя → верхняя
                new_hole["edge"] = 4
            elif edge == 4:  # Верхняя → нижняя
                new_hole["edge"] = 2
            # Левая и правая остаются теми же
        
        # Не меняем знак смещений! Они остаются положительными в локальной системе нового угла
        
        mirrored_holes.append(new_hole)
    
    return mirrored_holes


def calculate_hole_position_for_canvas(
    abs_x: float,
    abs_y: float,
    scale: float,
    offset_x: float,
    offset_y: float
) -> Tuple[float, float]:
    """
    Вычисление позиции отверстия на canvas
    
    Args:
        abs_x: Абсолютная координата X
        abs_y: Абсолютная координата Y
        scale: Масштаб
        offset_x: Смещение по X
        offset_y: Смещение по Y
        
    Returns:
        Координаты на canvas
    """
    x = offset_x + abs_x * scale
    y = offset_y + abs_y * scale
    return x, y


def is_point_inside_hole(
    point_x: float,
    point_y: float,
    hole: Dict[str, Any],
    scale: float,
    offset_x: float,
    offset_y: float,
    panel_width: float,
    panel_height: float,
    panel_thickness: float
) -> bool:
    """
    Проверка, находится ли точка внутри отверстия
    
    Args:
        point_x: Координата X точки
        point_y: Координата Y точки
        hole: Данные отверстия
        scale: Масштаб
        offset_x: Смещение по X
        offset_y: Смещение по Y
        panel_width: Ширина панели
        panel_height: Высота панели
        panel_thickness: Толщина панели
        
    Returns:
        True если точка внутри отверстия
    """
    # Проверяем тип отверстия
    if "y_expr" in hole or "y" in hole:  # Отверстие в плоскости
        abs_x, abs_y = get_absolute_coordinates_top(hole, panel_width, panel_height)
        diameter = hole.get("diameter", 8)
        
        # Координаты на canvas
        x, y = calculate_hole_position_for_canvas(abs_x, abs_y, scale, offset_x, offset_y)
        radius = diameter * scale / 2
        
        # Проверяем расстояние до центра
        distance = math.sqrt((point_x - x)**2 + (point_y - y)**2)
        return distance <= radius
    else:  # Отверстие в кромке
        abs_x, abs_y, width, height, orientation, rect_x1, rect_y1, rect_x2, rect_y2 = \
            get_absolute_coordinates_edge(hole, panel_width, panel_height, panel_thickness)
        
        # Координаты прямоугольника на canvas
        rect_x1_scaled = offset_x + rect_x1 * scale
        rect_y1_scaled = offset_y + rect_y1 * scale
        rect_x2_scaled = offset_x + rect_x2 * scale
        rect_y2_scaled = offset_y + rect_y2 * scale
        
        # Проверяем, находится ли точка внутри прямоугольника
        return (rect_x1_scaled <= point_x <= rect_x2_scaled and 
                rect_y1_scaled <= point_y <= rect_y2_scaled)


def validate_hole_parameters(hole_data: Dict[str, Any]) -> bool:
    """
    Проверка корректности параметров отверстия
    
    Args:
        hole_data: Данные отверстия
        
    Returns:
        True если параметры корректны
    """
    # Проверяем обязательные поля
    required_fields = ['corner', 'edge', 'diameter', 'depth', 'type']
    for field in required_fields:
        if field not in hole_data:
            return False
    
    # Проверяем диапазоны значений
    if not (1 <= hole_data['corner'] <= 4):
        return False
    
    if not (1 <= hole_data['edge'] <= 4):
        return False
    
    if hole_data['diameter'] <= 0:
        return False
    
    if hole_data['depth'] <= 0:
        return False
    
    if hole_data['type'] not in [1, 2]:
        return False
    
    return True
    
def local_to_absolute(
    corner: int,
    edge: int,
    x_local: float,
    y_local: float,
    z_local: float,
    panel_width: float,
    panel_height: float,
    is_edge_hole: bool = False
) -> Dict[str, float]:
    """
    Преобразование локальных координат в абсолютные (для отображения)
    
    Args:
        corner: Базовый угол (1-4)
        edge: Базовая кромка (1-4)
        x_local: Локальная координата X
        y_local: Локальная координата Y
        z_local: Локальная координата Z
        panel_width: Ширина панели
        panel_height: Высота панели
        is_edge_hole: True для отверстий в кромках
        
    Returns:
        Словарь с абсолютными координатами
    """
    if is_edge_hole:
        # Для отверстий в кромках преобразуем отдельно
        return _local_to_absolute_edge(corner, edge, x_local, z_local, panel_width, panel_height)
    else:
        # Для отверстий в плоскости
        return _local_to_absolute_top(corner, x_local, y_local, panel_width, panel_height)


def _local_to_absolute_top(
    corner: int,
    x_local: float,
    y_local: float,
    panel_width: float,
    panel_height: float
) -> Dict[str, float]:
    """Преобразование для отверстий в плоскости"""
    if corner == 1:  # ВЛ
        return {'x': x_local, 'y': y_local}
    elif corner == 2:  # НЛ
        return {'x': x_local, 'y': panel_height - y_local}
    elif corner == 3:  # НП
        return {'x': panel_width - x_local, 'y': panel_height - y_local}
    elif corner == 4:  # ВП
        return {'x': panel_width - x_local, 'y': y_local}
    else:
        return {'x': x_local, 'y': y_local}


def _local_to_absolute_edge(
    corner: int,
    edge: int,
    x_local: float,  # Координата вдоль кромки
    z_local: float,  # Глубина от верха
    panel_width: float,
    panel_height: float
) -> Dict[str, float]:
    """Преобразование для отверстий в кромках"""
    # Базовая логика такая же, но нужно учитывать кромку
    if edge == 1:  # Левая кромка
        if corner == 1:  # От ВЛ
            return {'x': 0, 'y': x_local, 'z': z_local}
        elif corner == 2:  # От НЛ
            return {'x': 0, 'y': panel_height - x_local, 'z': z_local}
    elif edge == 2:  # Нижняя кромка
        if corner == 2:  # От НЛ
            return {'x': x_local, 'y': panel_height, 'z': z_local}
        elif corner == 3:  # От НП
            return {'x': panel_width - x_local, 'y': panel_height, 'z': z_local}
    elif edge == 3:  # Правая кромка
        if corner == 3:  # От НП
            return {'x': panel_width, 'y': panel_height - x_local, 'z': z_local}
        elif corner == 4:  # От ВП
            return {'x': panel_width, 'y': x_local, 'z': z_local}
    elif edge == 4:  # Верхняя кромка
        if corner == 4:  # От ВП
            return {'x': panel_width - x_local, 'y': 0, 'z': z_local}
        elif corner == 1:  # От ВЛ
            return {'x': x_local, 'y': 0, 'z': z_local}
    
    return {'x': 0, 'y': 0, 'z': z_local}