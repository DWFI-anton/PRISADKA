# hole_manager.py
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import copy


class HoleType(Enum):
    """Типы отверстий"""
    BLIND = 1    # Глухое
    THROUGH = 2  # Сквозное


class Corner(Enum):
    """Углы панели"""
    TOP_LEFT = 1      # Верхний левый
    BOTTOM_LEFT = 2   # Нижний левый
    BOTTOM_RIGHT = 3  # Нижний правый
    TOP_RIGHT = 4     # Верхний правый


class Edge(Enum):
    """Кромки панели"""
    LEFT = 1     # Левая
    BOTTOM = 2   # Нижняя
    RIGHT = 3    # Правая
    TOP = 4      # Верхняя


# В hole_manager.py
@dataclass
class Hole:
    """Класс для представления отверстия с хранением в локальных координатах"""
    id: int = 0
    corner: Corner = Corner.TOP_LEFT      # SPG (1-4)
    edge: Edge = Edge.LEFT                # LAT (1-4)
    orientation: str = 'V'                # OV: 'V' для плоскости, 'O' для кромки
    
    # Локальные координаты (в системе базового угла)
    x_local: float = 0.0                  # X координата от угла
    y_local: float = 0.0                  # Y координата от угла
    z_local: float = 0.0                  # Z координата от верха (для кромок)
    
    # Параметры отверстия
    diameter: float = 8.0                 # DIA
    depth: float = 10.0                   # PRF
    hole_type: HoleType = HoleType.BLIND  # TPF (1 или 2) - переименовано с 'type'
    
    # Параметры массива (в локальных координатах)
    repeats: int = 1                      # RIP
    offset_x_local: float = 0.0           # OX (в локальных координатах)
    offset_y_local: float = 0.0           # OY (в локальных координатах)
    
    # Выражения для пользовательского ввода
    x_expr: str = ""
    y_expr: str = ""
    z_expr: str = ""
    
    def __post_init__(self):
        """Инициализация после создания объекта"""
        # Конвертируем значения, если они переданы как int
        if isinstance(self.corner, int):
            self.corner = Corner(self.corner)
        if isinstance(self.edge, int):
            self.edge = Edge(self.edge)
        if isinstance(self.hole_type, int):
            self.hole_type = HoleType(self.hole_type)
        
        # Убедимся, что выражения - строки
        if not isinstance(self.x_expr, str):
            self.x_expr = str(self.x_expr) if self.x_expr is not None else ""
        if not isinstance(self.y_expr, str):
            self.y_expr = str(self.y_expr) if self.y_expr is not None else ""
        if not isinstance(self.z_expr, str):
            self.z_expr = str(self.z_expr) if self.z_expr is not None else ""
        
        # Приводим числовые поля к правильным типам
        try:
            self.depth = float(self.depth) if not isinstance(self.depth, (int, float)) else float(self.depth)
        except:
            self.depth = 10.0 if self.is_top_hole() else 15.0
        
        try:
            self.diameter = int(self.diameter) if not isinstance(self.diameter, int) else self.diameter
        except:
            self.diameter = 8
        
        try:
            self.x_local = float(self.x_local) if not isinstance(self.x_local, (int, float)) else float(self.x_local)
        except:
            self.x_local = 0.0
        
        try:
            self.y_local = float(self.y_local) if not isinstance(self.y_local, (int, float)) else float(self.y_local)
        except:
            self.y_local = 0.0
        
        try:
            self.z_local = float(self.z_local) if not isinstance(self.z_local, (int, float)) else float(self.z_local)
        except:
            self.z_local = 0.0
        
        try:
            self.offset_x_local = float(self.offset_x_local) if not isinstance(self.offset_x_local, (int, float)) else float(self.offset_x_local)
        except:
            self.offset_x_local = 0.0
        
        try:
            self.offset_y_local = float(self.offset_y_local) if not isinstance(self.offset_y_local, (int, float)) else float(self.offset_y_local)
        except:
            self.offset_y_local = 0.0
        
        # Автоматически определяем ориентацию
        if self.is_edge_hole():
            self.orientation = 'O'
        else:
            self.orientation = 'V'
        
        # Автоматически определяем, является ли это массивом
        self.is_array = self.repeats > 1
    
    def is_edge_hole(self) -> bool:
        """Проверка, является ли отверстие отверстием в кромке"""
        # Проверяем z_local (число)
        has_z = self.z_local != 0
        
        # Проверяем z_expr (строка) - безопасно
        has_z_expr = False
        if isinstance(self.z_expr, str):
            # Удаляем пробелы и проверяем, не пустая ли строка
            cleaned = self.z_expr.strip()
            has_z_expr = cleaned != "" and cleaned != "0"
        elif isinstance(self.z_expr, (int, float)):
            # Если по какой-то причине z_expr все еще число
            has_z_expr = self.z_expr != 0 and self.z_expr != 0.0
            # Конвертируем в строку для хранения
            self.z_expr = str(self.z_expr) if self.z_expr is not None else ""
        
        # Проверяем ориентацию, если установлена
        if hasattr(self, 'orientation'):
            return has_z or has_z_expr or self.orientation == 'O'
        
        return has_z or has_z_expr
    
    def is_top_hole(self) -> bool:
        """Проверка, является ли отверстие отверстием в плоскости"""
        return not self.is_edge_hole()
    
    def get_local_positions(self) -> List[Dict[str, float]]:
        """Получение всех позиций массива в локальных координатах"""
        positions = []
        for i in range(self.repeats):
            positions.append({
                'x': self.x_local + i * self.offset_x_local,
                'y': self.y_local + i * self.offset_y_local,
                'z': self.z_local
            })
        return positions
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            'id': self.id,
            'corner': self.corner.value,
            'edge': self.edge.value,
            'orientation': self.orientation,
            'x_local': self.x_local,
            'y_local': self.y_local,
            'z_local': self.z_local,
            'diameter': self.diameter,
            'depth': self.depth,
            'hole_type': self.hole_type.value,  # Используем 'hole_type' вместо 'type'
            'repeats': self.repeats,
            'offset_x_local': self.offset_x_local,
            'offset_y_local': self.offset_y_local,
            'x_expr': self.x_expr,
            'y_expr': self.y_expr,
            'z_expr': self.z_expr
        }
    
    def update(self, **kwargs) -> None:
        """Обновление параметров отверстия"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                if key == 'corner' and isinstance(value, int):
                    setattr(self, key, Corner(value))
                elif key == 'edge' and isinstance(value, int):
                    setattr(self, key, Edge(value))
                elif key in ['hole_type', 'type'] and isinstance(value, int):
                    # Обрабатываем и 'hole_type' и 'type'
                    setattr(self, 'hole_type', HoleType(value))
                else:
                    setattr(self, key, value)
        
        # Обновляем ориентацию
        if self.is_edge_hole():
            self.orientation = 'O'
        else:
            self.orientation = 'V'


class HoleFactory:
    """Фабрика для создания отверстий"""
    
    @staticmethod
    def create_hole(**kwargs) -> Hole:
        """
        Создание нового отверстия
        """
        # Обработка параметров
        processed_kwargs = {}
        
        for key, value in kwargs.items():
            # Преобразуем Enum если передано число
            if key == 'corner' and isinstance(value, int):
                processed_kwargs[key] = Corner(value)
            elif key == 'edge' and isinstance(value, int):
                processed_kwargs[key] = Edge(value)
            elif key == 'hole_type' and isinstance(value, int):
                processed_kwargs[key] = HoleType(value)
            elif key == 'type' and isinstance(value, int):
                processed_kwargs['hole_type'] = HoleType(value)
            # Убедимся, что выражения - строки
            elif key in ['x_expr', 'y_expr', 'z_expr']:
                if not isinstance(value, str):
                    processed_kwargs[key] = str(value) if value is not None else ""
                else:
                    processed_kwargs[key] = value
            else:
                processed_kwargs[key] = value
        
        return Hole(**processed_kwargs)
    
    @staticmethod
    def create_top_hole(
        corner: Union[Corner, int],
        edge: Union[Edge, int],
        x_expr: str,
        y_expr: str,
        diameter: float,
        depth: float,
        hole_type: Union[HoleType, int] = HoleType.BLIND,
        repeats: int = 1,
        offset_x: float = 0.0,
        offset_y: float = 0.0
    ) -> Hole:
        """Создание отверстия в плоскости"""
        return HoleFactory.create_hole(
            corner=corner,
            edge=edge,
            x_expr=x_expr,
            y_expr=y_expr,
            diameter=diameter,
            depth=depth,
            type=hole_type,
            repeats=repeats,
            offset_x=offset_x,
            offset_y=offset_y
        )
    
    @staticmethod
    def create_edge_hole(
        corner: Union[Corner, int],
        edge: Union[Edge, int],
        x_expr: str,
        z_expr: str,
        diameter: float,
        depth: float,
        hole_type: Union[HoleType, int] = HoleType.BLIND,
        repeats: int = 1,
        offset_x: float = 0.0,
        offset_y: float = 0.0
    ) -> Hole:
        """Создание отверстия в кромке"""
        return HoleFactory.create_hole(
            corner=corner,
            edge=edge,
            x_expr=x_expr,
            z_expr=z_expr,
            diameter=diameter,
            depth=depth,
            type=hole_type,
            repeats=repeats,
            offset_x=offset_x,
            offset_y=offset_y
        )
    
    @staticmethod
    def create_from_anc_data(anc_data: Dict[str, Any]) -> Hole:
        """
        Создание отверстия из данных ANC формата
        Args:
            anc_data: Данные в формате ANC
        Returns:
            Созданное отверстие
        """
        # Определяем тип отверстия по OV
        orientation = anc_data.get('OV', 'V')
        
        if orientation == 'V':
            return HoleFactory.create_top_hole_from_anc(anc_data)
        else:
            return HoleFactory.create_edge_hole_from_anc(anc_data)
    
    @staticmethod
    def create_top_hole_from_anc(anc_data: Dict[str, Any]) -> Hole:
        """Создание отверстия в плоскости из ANC данных"""
        return Hole(
            id=anc_data.get('ASID', 0),
            corner=anc_data.get('SPG', 1),
            edge=anc_data.get('LAT', 1),  # Для отверстий в плоскости LAT не используется, но сохраним
            x=float(anc_data.get('X', 0)),
            y=float(anc_data.get('Y', 0)),
            z=0,
            diameter=float(anc_data.get('DIA', 8)),
            depth=float(anc_data.get('PRF', 10)),
            type=anc_data.get('TPF', 1),
            repeats=anc_data.get('RIP', 1),
            offset_x=float(anc_data.get('OX', 0)),
            offset_y=float(anc_data.get('OY', 0)),
            orientation='V',
            is_array=anc_data.get('RIP', 1) > 1
        )
    
    @staticmethod
    def create_edge_hole_from_anc(anc_data: Dict[str, Any]) -> Hole:
        """Создание отверстия в кромке из ANC данных"""
        edge = anc_data.get('LAT', 1)
        corner = anc_data.get('SPG', 1)
        
        # Определяем координаты в зависимости от кромки
        if edge in [1, 3]:  # Левая или правая кромка
            x = float(anc_data.get('Y', 0))  # Y - координата вдоль кромки
            y = 0  # Не используется для кромок
            z = float(anc_data.get('Z', 0))
        else:  # Верхняя или нижняя кромка
            x = float(anc_data.get('X', 0))  # X - координата вдоль кромки
            y = 0  # Не используется для кромок
            z = float(anc_data.get('Z', 0))
        
        return Hole(
            id=anc_data.get('ASID', 0),
            corner=corner,
            edge=edge,
            x=x,
            y=y,
            z=z,
            diameter=float(anc_data.get('DIA', 8)),
            depth=float(anc_data.get('PRF', 10)),
            type=anc_data.get('TPF', 1),
            repeats=anc_data.get('RIP', 1),
            offset_x=float(anc_data.get('OX', 0)),
            offset_y=float(anc_data.get('OY', 0)),
            orientation='O',
            is_array=anc_data.get('RIP', 1) > 1
        )


class HoleManager:
    """Менеджер для работы с отверстиями"""
    
    def __init__(self):
        self.holes: List[Hole] = []
        self._next_id = 1
    
    def add_hole(self, hole: Hole) -> None:
        """
        Добавление нового отверстия
        
        Args:
            hole: Отверстие для добавления
        """
        # Присваиваем ID если его нет
        if hole.id == 0:
            hole.id = self._get_next_id()
        
        self.holes.append(hole)
    
    def remove_hole(self, hole_id: int) -> bool:
        """
        Удаление отверстия по ID
        
        Args:
            hole_id: ID отверстия
            
        Returns:
            True если отверстие было удалено
        """
        for i, hole in enumerate(self.holes):
            if hole.id == hole_id:
                self.holes.pop(i)
                return True
        return False
    
   
    
    def get_hole_by_id(self, hole_id: int) -> Optional[Hole]:
        """
        Поиск отверстия по ID
        
        Args:
            hole_id: ID отверстия
            
        Returns:
            Найденное отверстие или None
        """
        for hole in self.holes:
            if hole.id == hole_id:
                return hole
        return None
    
    def get_all_holes(self) -> List[Hole]:
        """
        Получение всех отверстий
        
        Returns:
            Список всех отверстий
        """
        return self.holes.copy()
    
    def get_top_holes(self) -> List[Hole]:
        """
        Получение отверстий в плоскости
        
        Returns:
            Список отверстий в плоскости
        """
        return [hole for hole in self.holes if hole.is_top_hole()]
    
    def get_edge_holes(self) -> List[Hole]:
        """
        Получение отверстий в кромках
        
        Returns:
            Список отверстий в кромках
        """
        return [hole for hole in self.holes if hole.is_edge_hole()]
    
    def update_hole(self, hole_data: Dict[str, Any]) -> bool:
        """
        Обновление отверстия
        
        Args:
            hole_data: Новые данные отверстия
            
        Returns:
            True если отверстие было обновлено
        """
        hole_id = hole_data.get('id')
        if not hole_id:
            return False
        
        hole = self.get_hole_by_id(hole_id)
        if not hole:
            return False
        
        # Обновляем параметры
        hole.update(**hole_data)
        return True
    
    def renumber_holes(self) -> None:
        """Перенумерация всех отверстий по порядку"""
        # Сортируем отверстия: сначала в плоскости, затем в кромках
        top_holes = self.get_top_holes()
        edge_holes = self.get_edge_holes()
        
        # Присваиваем новые номера
        new_id = 1
        for hole in top_holes:
            hole.id = new_id
            new_id += 1
        
        for hole in edge_holes:
            hole.id = new_id
            new_id += 1
        
        # Обновляем общий список
        self.holes = top_holes + edge_holes
        self._next_id = new_id
    
    # def adjust_depths_to_thickness(self, panel_thickness: float) -> None:
        # """
        # Корректировка глубин отверстий в соответствии с толщиной панели
        
        # Args:
            # panel_thickness: Толщина панели
        # """
        # for hole in self.holes:
            # if hole.depth > panel_thickness:
                # hole.depth = panel_thickness
    
    def clear(self) -> None:
        """Очистка всех отверстий"""
        self.holes.clear()
        self._next_id = 1
    
    def set_holes(self, holes: List[Hole]) -> None:
        """
        Установка нового списка отверстий
        
        Args:
            holes: Новый список отверстий
        """
        self.holes = holes.copy()
        self._renumber_holes()
    
    def _get_next_id(self) -> int:
        """Получение следующего свободного ID"""
        if not self.holes:
            return 1
        max_id = max(hole.id for hole in self.holes)
        return max_id + 1
    
    def _renumber_holes(self) -> None:
        """Внутренняя перенумерация отверстий"""
        self.renumber_holes()
        self._next_id = len(self.holes) + 1 if self.holes else 1
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Конвертация всех отверстий в список словарей
        
        Returns:
            Список словарей с данными отверстий
        """
        return [hole.to_dict() for hole in self.holes]
    
    @classmethod
    def from_dict_list(cls, holes_data: List[Dict[str, Any]]) -> 'HoleManager':
        """
        Создание HoleManager из списка словарей
        
        Args:
            holes_data: Список словарей с данными отверстий
            
        Returns:
            Созданный HoleManager
        """
        manager = cls()
        for hole_data in holes_data:
            hole = HoleFactory.create_hole(**hole_data)
            manager.add_hole(hole)
        return manager