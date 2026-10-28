# config.py
from typing import Dict, Tuple, List
from dataclasses import dataclass
import colorsys

# Цвета для панели
PANEL_COLOR = "#F0F0F0"
EDGE_COLOR = "#333333"
HOLE_EDGE_COLOR = "#000000"
HIGHLIGHT_COLOR = "yellow"
HIGHLIGHT_WIDTH = 3  # Толщина линии выделения
GROOVE_COLOR = "#E67E22"  # Цвет паза (оранжевый)

# Предопределенные цвета для диаметров
DIAMETER_COLORS: Dict[int, str] = {
    2: "#FF6B6B",    # красный
    5: "#4ECDC4",    # бирюзовый
    8: "#FFD166",    # желтый
    10: "#06D6A0",   # зеленый
    15: "#118AB2",   # синий
    20: "#7209B7",   # фиолетовый
    25: "#F72585",   # розовый
    30: "#3A86FF",   # голубой
    35: "#FB5607",   # оранжевый
}

# Параметры панели по умолчанию
DEFAULT_PANEL = {
    'width': 1200,
    'height': 600,
    'thickness': 16
}

# Параметры паза по умолчанию
DEFAULT_GROOVE = {
    'enabled': False,
    'length': 1200,   # LPAZ - полная длина паза
    'width': 6.5,     # WPAZ - полная ширина паза
    'depth': 6.0,      # ZPAZ - глубина паза
    'y_pos': 18.0      # YPAZ - положение центра паза по Y от верха
}

DEFAULT_PROGRAM_NAME = "DETAL"

# Ограничения для размеров
MIN_PANEL_WIDTH = 50
MAX_PANEL_WIDTH = 3500
MIN_PANEL_HEIGHT = 50
MAX_PANEL_HEIGHT = 3500
MIN_PANEL_THICKNESS = 4
MAX_PANEL_THICKNESS = 100

# Параметры отображения
MARGIN = 80  # Отступы на canvas
ARROW_LENGTH = 50  # Длина стрелок осей
ARROW_WIDTH = 2
CORNER_MARKER_SIZE = 20
EDGE_TEXT_OFFSET = 15
HOLE_HIGHLIGHT_OFFSET = 8

# Настройки для углов
CORNER_NAMES = {
    1: "1 (ВЛ)",
    2: "2 (НЛ)",
    3: "3 (НП)",
    4: "4 (ВП)"
}

CORNER_ANCHORS = {
    1: "nw",  # верхний левый
    2: "sw",  # нижний левый
    3: "se",  # нижний правый
    4: "ne"   # верхний правый
}

# Настройки для кромок
EDGE_NAMES = {
    1: "1 Левая",
    2: "2 Нижняя",
    3: "3 Правая",
    4: "4 Верхняя"
}

EDGE_POSITIONS = {
    1: (0, 0.5),      # левая - середина по высоте
    2: (0.5, 1),      # нижняя - середина по ширине
    3: (1, 0.5),      # правая - середина по высоте
    4: (0.5, 0)       # верхняя - середина по ширине
}

# config.py - обновим CORNER_ARROWS

# Настройки текстовых подписей для каждого угла
CORNER_TEXTS = {
    1: {"text": "Угол 1: X→, Y↓", "position": "above", "anchor": "nw"},
    2: {"text": "Угол 2: X→, Y↑", "position": "below", "anchor": "sw"},
    3: {"text": "Угол 3: X←, Y↑", "position": "below", "anchor": "se"},
    4: {"text": "Угол 4: X←, Y↓", "position": "above", "anchor": "ne"}
}

# Удалим старый CORNER_ARROWS или закомментируем его
CORNER_ARROWS = [
    # (x_offset, y_offset, x_direction, corner_num, label)
    (50, 50, 1, 1, "Угол 1: X→, Y↓"),
    (50, -50, 1, 2, "Угол 2: X→, Y↑"),
    (-50, -50, -1, 3, "Угол 3: X←, Y↑"),
    (-50, 50, -1, 4, "Угол 4: X←, Y↓")
]

# Цвета для стрелок
ARROW_X_COLOR = "red"
ARROW_Y_COLOR = "green"

# Настройки шрифтов
FONT_HEADER = ('Arial', 12, 'bold')
FONT_NORMAL = ('Arial', 10)
FONT_BOLD = ('Arial', 10, 'bold')
FONT_SMALL = ('Arial', 9)

# Цвета текста
TEXT_COLOR_CORNER = "red"
TEXT_COLOR_EDGE = "blue"
TEXT_COLOR_HOLE = "black"

# Параметры для таблиц
TABLE_ROW_HEIGHT = 25
TABLE_COLUMN_WIDTHS = {
    'id': 20,
    'corner': 20,
    'edge': 20,
    'x': 80,
    'y': 80,
    'z': 80,
    'diameter': 80,
    'depth': 100,
    'type': 80
}

# Параметры для отверстий
DEFAULT_HOLE_DIAMETER = 8
DEFAULT_HOLE_DEPTH = 11
MAX_HOLE_DEPTH = 50

# Типы отверстий
HOLE_TYPE_NAMES = {
    1: "Глухое",
    2: "Сквозное"
}

# Настройки Canvas
CANVAS_BG_COLOR = "white"
CANVAS_HIGHLIGHT_THICKNESS = 1
CANVAS_HIGHLIGHT_COLOR = "#CCCCCC"

# Цвета для легенды
LEGEND_ITEM_WIDTH = 45
LEGEND_CIRCLE_SIZE = 20

# Настройки для файлов
ANC_FILE_EXTENSION = ".anc"
ANC_FILE_TYPES = [
    ("Файлы присадки", "*.anc"),
    ("Текстовые файлы", "*.txt"),
    ("Все файлы", "*.*")
]

# Разрешенные символы для арифметических выражений
ALLOWED_EXPRESSION_CHARS = set('0123456789.+-*/() ')

@dataclass
class PanelDimensions:
    """Класс для хранения размеров панели"""
    width: float
    height: float
    thickness: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'width': self.width,
            'height': self.height,
            'thickness': self.thickness
        }


def generate_color(existing_colors: Dict[int, str]) -> str:
    """
    Генерация нового цвета для диаметра
    
    Args:
        existing_colors: Словарь существующих цветов
    
    Returns:
        Новый HEX-цвет
    """
    # Предопределенная палитра красивых цветов
    color_palette = [
        '#FF6B6B', '#4ECDC4', '#FFD166', '#06D6A0', '#118AB2',
        '#7209B7', '#F72585', '#3A86FF', '#FB5607', '#8338EC',
        '#3A86FF', '#FF006E', '#FB5607', '#FFBE0B', '#3A86FF',
        '#8338EC', '#FF006E', '#FFBE0B', '#FB5607', '#06D6A0'
    ]
    
    # Пробуем найти цвет из палитры, который еще не используется
    used_colors = set(existing_colors.values())
    for color in color_palette:
        if color not in used_colors:
            return color
    
    # Если все цвета из палитры использованы, генерируем случайный
    import random
    while True:
        # Генерируем яркие, насыщенные цвета
        hue = random.random()
        saturation = 0.7 + random.random() * 0.3
        value = 0.7 + random.random() * 0.3
        
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        color = f"#{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"
        
        if color not in used_colors:
            return color


def get_diameter_color(diameter: int, diameter_colors: Dict[int, str]) -> str:
    """
    Получение цвета для диаметра
    
    Args:
        diameter: Диаметр отверстия
        diameter_colors: Словарь цветов для диаметров
    
    Returns:
        HEX-цвет
    """
    return diameter_colors.get(diameter, "#888888")  # Серый по умолчанию


def validate_panel_dimensions(width: float, height: float, thickness: float) -> bool:
    """
    Проверка корректности размеров панели
    
    Args:
        width: Ширина панели
        height: Высота панели
        thickness: Толщина панели
    
    Returns:
        True если размеры корректны
    """
    return (
        MIN_PANEL_WIDTH <= width <= MAX_PANEL_WIDTH and
        MIN_PANEL_HEIGHT <= height <= MAX_PANEL_HEIGHT and
        MIN_PANEL_THICKNESS <= thickness <= MAX_PANEL_THICKNESS
    )


def get_corner_name(corner: int) -> str:
    """Получение текстового названия угла"""
    return CORNER_NAMES.get(corner, f"Угол {corner}")


def get_edge_name(edge: int) -> str:
    """Получение текстового названия кромки"""
    return EDGE_NAMES.get(edge, f"Кромка {edge}")


def get_hole_type_name(hole_type: int) -> str:
    """Получение текстового названия типа отверстия"""
    return HOLE_TYPE_NAMES.get(hole_type, "Неизвестно")