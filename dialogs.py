# dialogs.py - исправленная версия
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional, Callable


class HoleDialog:
    """Диалоговое окно для добавления/редактирования отверстия"""
    
    def __init__(self, parent, hole_type, panel_thickness, 
                 hole_data=None, on_save=None, on_delete=None, title=None):
        self.parent = parent
        self.hole_type = hole_type
        self.panel_thickness = panel_thickness
        self.hole_data = hole_data or {}
        self.on_save = on_save
        self.on_delete = on_delete
        self.custom_title = title
        self.dialog = None
        self.entries = {}
        
        # КОНВЕРТИРУЕМ hole_type в type для совместимости с диалогом
        if 'hole_type' in self.hole_data:
            self.hole_data['type'] = self.hole_data['hole_type']
        
    def show(self):
        """Показ диалогового окна"""
        print(f"Создаем диалоговое окно с заголовком: {self.custom_title}")
        self.dialog = tk.Toplevel(self.parent)
        
        # Используем кастомный заголовок если есть
        if self.custom_title:
            self.dialog.title(self.custom_title)
        else:
            self.dialog.title("Редактировать отверстие" if self.hole_data else "Добавить отверстие")
            
        self.dialog.geometry("500x600")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Устанавливаем фокус на диалоге
        self.dialog.focus_set()
        
        print(f"Диалог создан: {self.dialog}")
        print(f"Данные отверстия: {self.hole_data}")
        
        # Привязываем горячие клавиши
        self.dialog.bind('<Return>', lambda event: self._save())
        self.dialog.bind('<Escape>', lambda event: self.dialog.destroy())
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Создание виджетов диалога"""
        # Определяем поля в зависимости от типа отверстия
        if self.hole_type == "top":
            fields = self._get_top_fields()
        else:
            fields = self._get_edge_fields()
        
        # Создаем поля ввода
        self.entries = {}
        for i, (label, key, default, validator) in enumerate(fields):
            ttk.Label(self.dialog, text=label).grid(
                row=i, column=0, padx=10, pady=8, sticky=tk.W
            )
            
            # Значение по умолчанию
            value = self.hole_data.get(key, default)
            
            # Для полей offset_x и offset_y используем offset_x_local и offset_y_local
            if key == 'offset_x' and 'offset_x_local' in self.hole_data:
                value = self.hole_data.get('offset_x_local', default)
            elif key == 'offset_y' and 'offset_y_local' in self.hole_data:
                value = self.hole_data.get('offset_y_local', default)
            
            # Для полей выражений, если есть локальное значение и нет выражения, используем локальное значение
            if key in ['x_expr', 'y_expr', 'z_expr'] and (not value or value == ''):
                local_key = key.replace('_expr', '_local')
                local_value = self.hole_data.get(local_key)
                if local_value is not None:
                    value = str(local_value)
            
            # ОСОБЫЙ СЛУЧАЙ: для поля 'type' используем значение из 'hole_type'
            if key == 'type' and 'hole_type' in self.hole_data:
                value = self.hole_data['hole_type']
            
            print(f"Создаем поле {key} со значением: {value} (тип: {type(value).__name__})")
            
            # Создаем поле ввода
            if validator == "int":
                entry = ttk.Spinbox(self.dialog, from_=1, to=1000, width=20)
                entry.set(value)
                entry.bind('<Return>', lambda event: self._save())
            elif validator == "float":
                entry = ttk.Entry(self.dialog, width=20)
                entry.insert(0, str(value))
                entry.bind('<Return>', lambda event: self._save())
            elif validator == "choice":
                entry = ttk.Combobox(self.dialog, width=18, state="readonly")
                if key == "corner":
                    entry['values'] = ["1 (ВЛ)", "2 (НЛ)", "3 (НП)", "4 (ВП)"]
                    # Преобразуем числовое значение в текстовое
                    if value == 1:
                        entry.set("1 (ВЛ)")
                    elif value == 2:
                        entry.set("2 (НЛ)")
                    elif value == 3:
                        entry.set("3 (НП)")
                    elif value == 4:
                        entry.set("4 (ВП)")
                    else:
                        entry.set(f"{value} ({self._corner_to_text(value)})")
                elif key == "edge":
                    entry['values'] = ["1 (Левая)", "2 (Нижняя)", "3 (Правая)", "4 (Верхняя)"]
                    # Преобразуем числовое значение в текстовое
                    if value == 1:
                        entry.set("1 (Левая)")
                    elif value == 2:
                        entry.set("2 (Нижняя)")
                    elif value == 3:
                        entry.set("3 (Правая)")
                    elif value == 4:
                        entry.set("4 (Верхняя)")
                    else:
                        entry.set(f"{value} ({self._edge_to_text(value)})")
                elif key == "type":
                    entry['values'] = ["1 (Глухое)", "2 (Сквозное)"]
                    # Преобразуем числовое значение в текстовое
                    if value == 1:
                        entry.set("1 (Глухое)")
                    elif value == 2:
                        entry.set("2 (Сквозное)")
                    else:
                        entry.set(f"{value} ({self._type_to_text(value)})")
                entry.bind('<Return>', lambda event: self._save())
            else:
                entry = ttk.Entry(self.dialog, width=20)
                entry.insert(0, str(value))
                entry.bind('<Return>', lambda event: self._save())
            
            entry.grid(row=i, column=1, padx=10, pady=8)
            self.entries[key] = (entry, validator)
        
        # Устанавливаем фокус на первое поле
        if self.entries:
            first_entry = list(self.entries.values())[0][0]
            first_entry.focus_set()
        
        # Подсказка о выражениях и значениях по умолчанию
        help_text = "Примеры выражений: 16/2, 300+8, 100-10, 50*2\n"
        help_text += f"По умолчанию: Z = {self.panel_thickness}/2 = {self.panel_thickness/2:.1f} мм\n"
        help_text += "Горячие клавиши: Enter - сохранить, Esc - отмена"
        
        ttk.Label(self.dialog, 
                 text=help_text, 
                 font=('Arial', 9), 
                 foreground='blue'
        ).grid(row=len(fields), column=0, columnspan=2, pady=10)
        
        ttk.Label(self.dialog, 
                 text=help_text, 
                 font=('Arial', 9), 
                 foreground='blue'
        ).grid(row=len(fields), column=0, columnspan=2, pady=10)
        
        # Кнопки
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=20)
        
        # Кнопка сохранения
        save_button = ttk.Button(button_frame, text="Сохранить (Enter)", 
                                command=self._save)
        save_button.pack(side=tk.LEFT, padx=5)
        
        # Показываем кнопку удаления только при редактировании существующего отверстия
        if self.on_delete and self.hole_data and 'id' in self.hole_data and self.hole_data['id'] > 0:
            ttk.Button(button_frame, text="Удалить",
                      command=self._delete).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Отмена (Esc)",
                  command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _get_top_fields(self):
        """Поля для отверстий в плоскости"""
        return [
            ("Базовый угол (1-4):", "corner", 1, "choice"),
            ("Базовая кромка (1-4):", "edge", 1, "choice"),
            ("Координата X (мм) или выражение:", "x_expr", "50", "float"),
            ("Координата Y (мм) или выражение:", "y_expr", "50", "float"),
            ("Диаметр (мм):", "diameter", 8, "int"),
            ("Глубина (мм):", "depth", 10, "float"),
            ("Тип отверстия (1=Глухое, 2=Сквозное):", "type", 1, "choice"),  # Изменено для ясности
            ("Количество повторов (RIP):", "repeats", 1, "int"),
            ("Смещение по X (OX) мм:", "offset_x", "0", "float"),
            ("Смещение по Y (OY) мм:", "offset_y", "0", "float")
        ]
    
    def _get_edge_fields(self):
        """Поля для отверстий в кромках"""
        z_default = str(round(self.panel_thickness / 2, 1))
        
        return [
            ("Базовый угол (1-4):", "corner", 1, "choice"),
            ("Базовая кромка (1-4):", "edge", 1, "choice"),
            ("Координата X (мм) или выражение:", "x_expr", "50", "float"),
            (f"Координата Z (мм) или выражение (0-{self.panel_thickness}):", 
             "z_expr", z_default, "float"),
            ("Диаметр (мм):", "diameter", 8, "int"),
            ("Глубина (мм):", "depth", 15, "float"),
            ("Тип отверстия (1=Глухое, 2=Сквозное):", "type", 1, "choice"),
            ("Количество повторов (RIP):", "repeats", 1, "int"),
            ("Смещение по X (OX) мм:", "offset_x", "0", "float"),
            ("Смещение по Y (OY) мм:", "offset_y", "0", "float")
        ]
    
    def _corner_to_text(self, value):
        """Преобразование номера угла в текст"""
        corners = {1: "ВЛ", 2: "НЛ", 3: "НП", 4: "ВП"}
        return corners.get(value, "")
    
    def _edge_to_text(self, value):
        """Преобразование номера кромки в текст"""
        edges = {1: "Левая", 2: "Нижняя", 3: "Правая", 4: "Верхняя"}
        return edges.get(value, "")
    
    def _type_to_text(self, value):
        """Преобразование типа отверстия в текст"""
        types = {1: "Глухое", 2: "Сквозное"}
        return types.get(value, "")
    
    def _parse_choice(self, value):
        """Парсинг значения из ComboBox"""
        if isinstance(value, str):
            # Извлекаем число из строки "1 (ВЛ)" или "1 (Глухое)"
            match = value.split()[0]
            try:
                return int(match)
            except:
                # Если не получилось, пробуем найти число в скобках
                import re
                numbers = re.findall(r'\d+', value)
                if numbers:
                    return int(numbers[0])
                return 1  # По умолчанию
        return value
    
    def _save(self, event=None):
        """Сохранение данных из диалога"""
        try:
            hole_data = {}
            
            for key, (entry, validator) in self.entries.items():
                value = entry.get()
                
                if validator == "choice":
                    parsed_value = self._parse_choice(value)
                    hole_data[key] = parsed_value
                    
                    # Отладочный вывод для типа отверстия
                    if key == 'type':
                        print(f"Парсим тип отверстия: '{value}' -> {parsed_value}")
                        
                elif validator == "int":
                    hole_data[key] = int(value) if value else 0
                elif validator == "float":
                    # Для координат сохраняем как строку (выражение)
                    hole_data[key] = value
            
            # Преобразуем ключи для совместимости с Hole классом
            if 'type' in hole_data:
                hole_data['hole_type'] = hole_data['type']
                del hole_data['type']
            
            print(f"Данные после парсинга: {hole_data}")
            
            # Вычисляем локальные координаты из выражений
            from geometry import evaluate_expression
            
            # Для x_expr
            if 'x_expr' in hole_data:
                x_expr = hole_data['x_expr']
                # Сохраняем выражение как строку
                if not isinstance(x_expr, str):
                    x_expr = str(x_expr) if x_expr is not None else ""
                hole_data['x_expr'] = x_expr
                # Вычисляем значение
                try:
                    hole_data['x_local'] = evaluate_expression(x_expr)
                except:
                    hole_data['x_local'] = 0.0
            
            # Для y_expr (только для отверстий в плоскости)
            if 'y_expr' in hole_data and self.hole_type == "top":
                y_expr = hole_data['y_expr']
                if not isinstance(y_expr, str):
                    y_expr = str(y_expr) if y_expr is not None else ""
                hole_data['y_expr'] = y_expr
                try:
                    hole_data['y_local'] = evaluate_expression(y_expr)
                except:
                    hole_data['y_local'] = 0.0
            elif 'y_expr' in hole_data:
                # Для отверстий в кромках y_expr не используется
                del hole_data['y_expr']
                hole_data['y_local'] = 0.0
            
            # Для z_expr (только для отверстий в кромках)
            if 'z_expr' in hole_data and self.hole_type == "edge":
                z_expr = hole_data['z_expr']
                if not isinstance(z_expr, str):
                    z_expr = str(z_expr) if z_expr is not None else ""
                hole_data['z_expr'] = z_expr
                try:
                    hole_data['z_local'] = evaluate_expression(z_expr)
                except:
                    hole_data['z_local'] = 0.0
            elif 'z_expr' in hole_data:
                # Для отверстий в плоскости z_expr не используется
                del hole_data['z_expr']
                hole_data['z_local'] = 0.0
            
            # Преобразуем depth в число
            if 'depth' in hole_data:
                try:
                    depth_value = hole_data['depth']
                    if isinstance(depth_value, str):
                        hole_data['depth'] = evaluate_expression(depth_value)
                    else:
                        hole_data['depth'] = float(depth_value)
                except:
                    hole_data['depth'] = 10.0 if self.hole_type == "top" else 15.0
            
            # Преобразуем смещения в числа
            if 'offset_x' in hole_data:
                try:
                    offset_x = hole_data['offset_x']
                    if isinstance(offset_x, str):
                        hole_data['offset_x_local'] = evaluate_expression(offset_x)
                    else:
                        hole_data['offset_x_local'] = float(offset_x)
                except:
                    hole_data['offset_x_local'] = 0.0
                del hole_data['offset_x']
            
            if 'offset_y' in hole_data:
                try:
                    offset_y = hole_data['offset_y']
                    if isinstance(offset_y, str):
                        hole_data['offset_y_local'] = evaluate_expression(offset_y)
                    else:
                        hole_data['offset_y_local'] = float(offset_y)
                except:
                    hole_data['offset_y_local'] = 0.0
                del hole_data['offset_y']
            
            # Если редактируем существующее отверстие, добавляем ID
            if self.hole_data and 'id' in self.hole_data:
                hole_data['id'] = self.hole_data['id']
            
            print(f"Сохраняем отверстие (после преобразования): {hole_data}")
            
            if self.on_save:
                self.on_save(hole_data)
            
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Ошибка в данных:\n{str(e)}")
            import traceback
            traceback.print_exc()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка:\n{str(e)}")
            import traceback
            traceback.print_exc()
        
    def _delete(self):
        """Удаление отверстия"""
        if self.on_delete and 'id' in self.hole_data:
            self.on_delete(self.hole_data['id'])
            self.dialog.destroy()

class HelpDialog:
    """Диалоговое окно справки"""
    
    def __init__(self, parent):
        self.parent = parent
        self.dialog = None
        
    def show(self):
        """Показ диалога справки"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Справка - Система нумерации")
        self.dialog.geometry("500x550")
        self.dialog.transient(self.parent)
        
        help_text = """Базовый угол:
1 - верхний левый (ВЛ)
2 - нижний левый (НЛ)
3 - нижний правый (НП)
4 - верхний правый (ВП)

Базовая кромка:
1 - левая сторона
2 - нижняя сторона
3 - правая сторона
4 - верхняя сторона

Тип отверстия:
1 - глухое (по умолчанию)
2 - сквозное

Оси координат:
Для отверстий в плоскости:
- X - горизонталь от угла
- Y - вертикаль от угла

Для отверстий в кромках:
- X - расстояние вдоль кромки от угла
- Z - глубина от верха панели
- Ориентация зависит от кромки

Нумерация:
Все отверстия имеют сквозную нумерацию
от 1 до N без пропусков.

Зеркалирование:
- По X: отражает отверстия относительно вертикальной оси
- По Y: отражает отверстия относительно горизонтальной оси

Арифметические выражения:
В полях координат можно использовать выражения:
- Примеры: 16/2, 300+8, 100-10, 50*2
- Поддерживаются: +, -, *, /, скобки ()
- Десятичные числа с точкой: 10.5
- При экспорте вычисляется результат

Файлы:
Сохранение и загрузка в формате присадочного станка (.anc).
По умолчанию:
- Размер панели: 1200x600x16 мм
- Тип отверстия: глухое (1)
- Наиболее используемые диаметры: 2,5,8,10,15,20,35 мм"""
        
        text_widget = tk.Text(self.dialog, wrap=tk.WORD, padx=10, pady=10, font=('Arial', 10))
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Button(self.dialog, text="Закрыть", command=self.dialog.destroy).pack(pady=10)