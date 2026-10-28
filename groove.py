# groove.py
from dataclasses import dataclass
from typing import Dict, Any

from config import DEFAULT_GROOVE


@dataclass
class Groove:
    """Параметры фрезерования паза (секция CONTORNATURA01)"""
    enabled: bool = False          # Делать паз или нет
    length: float = 150.0          # LPAZ - полная длина паза
    width: float = 14.0            # WPAZ - полная ширина паза
    depth: float = 4.0             # ZPAZ - глубина паза
    y_pos: float = 20.0            # YPAZ - положение центра паза по Y от верха

    def __post_init__(self):
        """Нормализация типов"""
        try:
            self.length = float(self.length)
        except (TypeError, ValueError):
            self.length = float(DEFAULT_GROOVE['length'])

        try:
            self.width = float(self.width)
        except (TypeError, ValueError):
            self.width = float(DEFAULT_GROOVE['width'])

        try:
            self.depth = float(self.depth)
        except (TypeError, ValueError):
            self.depth = float(DEFAULT_GROOVE['depth'])

        try:
            self.y_pos = float(self.y_pos)
        except (TypeError, ValueError):
            self.y_pos = float(DEFAULT_GROOVE['y_pos'])

        self.enabled = bool(self.enabled)

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            'enabled': self.enabled,
            'length': self.length,
            'width': self.width,
            'depth': self.depth,
            'y_pos': self.y_pos
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Groove':
        """Создание Groove из словаря"""
        if not data:
            return cls()
        return cls(
            enabled=data.get('enabled', DEFAULT_GROOVE['enabled']),
            length=data.get('length', DEFAULT_GROOVE['length']),
            width=data.get('width', DEFAULT_GROOVE['width']),
            depth=data.get('depth', DEFAULT_GROOVE['depth']),
            y_pos=data.get('y_pos', DEFAULT_GROOVE['y_pos'])
        )

    def mirror_y(self, panel_height: float) -> None:
        """
        Пересчёт положения паза при зеркалировании по Y.
        Паз центрируется по ширине, меняется только положение по Y от верха.

        Args:
            panel_height: Высота панели
        """
        self.y_pos = panel_height - self.y_pos