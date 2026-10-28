# file_handler.py
import re
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

from geometry import evaluate_expression
from hole_manager import Hole, HoleFactory, HoleManager, HoleType, Corner, Edge
from groove import Groove
from config import DEFAULT_PANEL, DEFAULT_GROOVE


class ANCFileHandler:
    """Обработчик файлов формата присадочного станка (.anc)"""
    
    def __init__(self):
        # Кодировка по умолчанию; при загрузке заменяется фактической кодировкой файла
        self.encoding = 'utf-8'
    
    def _detect_encoding(self, filename: str) -> str:
        """Определение кодировки файла .anc
        
        Порядок определения:
          1. BOM UTF-8 (EF BB BF)       -> 'utf-8-sig'
          2. Строгое декодирование UTF-8 -> 'utf-8'
          3. При UnicodeDecodeError      -> 'cp1251' (стандарт станочных файлов)
        
        Args:
            filename: Имя файла
        
        Returns:
            Название кодировки для открытия файла
        """
        try:
            with open(filename, 'rb') as f:
                raw = f.read()
        except Exception:
            return 'utf-8'
        
        # BOM UTF-8
        if raw.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-sig'
        
        # Строгая попытка UTF-8; при ошибке откат на cp1251
        try:
            raw.decode('utf-8')
            return 'utf-8'
        except UnicodeDecodeError:
            return 'cp1251'
    
    def save_to_file(
        self,
        filename: str,
        panel_data: Dict[str, float],
        holes: List[Hole],
        program_name: str = "DETAL",
        groove: Optional[Groove] = None  # Добавляем параметр паза
    ) -> bool:
        """
        Сохранение данных в формат .anc
         
        Args:
            filename: Имя файла для сохранения
            panel_data: Данные панели (ширина, высота, толщина)
            holes: Список отверстий
            program_name: Название программы
            groove: Параметры паза (фрезеровка)
             
        Returns:
            True если сохранение успешно
        """
        try:
            with open(filename, 'w', encoding=self.encoding) as f:
                # Заголовок файла с названием программы
                self._write_header(f, program_name)
                 
                # Секция параметров
                self._write_parameters(f, panel_data)
                 
                # Пустые секции
                self._write_empty_section(f, "UTENSILI01")
                
                # Секция контуров (паз), если он включён
                self._write_contornatura_section(f, groove)
                
                self._write_empty_section(f, "FORATURA01")
                 
                # Секция отверстий
                self._write_holes_section(f, holes)
                 
                # Остальные пустые секции
                self._write_empty_section(f, "LABELC01")
                self._write_empty_section(f, "LABELF01")
                self._write_empty_section(f, "CONFASSIST01")
                self._write_empty_section(f, "ATTREZZAGGIO01")
                self._write_empty_section(f, "CUSTOMSEZ01")
                self._write_empty_section(f, "SEIFERT01")
             
            return True
             
        except Exception as e:
            print(f"Ошибка при сохранении файла: {e}")
            return False
     
    def _write_contornatura_section(
        self,
        file_obj,
        groove: Optional[Groove] = None
    ) -> None:
        """
        Запись секции CONTORNATURA01 (паз)
        
        Args:
            file_obj: Файловый объект
            groove: Параметры паза; если None или выключен - пишется пустая секция
        """
        if not groove or not groove.enabled:
            self._write_empty_section(file_obj, "CONTORNATURA01")
            return
        
        file_obj.write("[CONTORNATURA01]\n")
        file_obj.write("; LPAZ - POLNAYA DLINA GOTOVOGO PAZA\n")
        file_obj.write("; WPAZ - POLNAYA SHIRINA GOTOVOGO PAZA\n")
        file_obj.write("; ZPAZ - GLUBINA PAZA\n")
        file_obj.write("; YPAZ - POLOZHENIE CENTRA PAZA PO Y\n")
        file_obj.write(
            f"N10 LPAZ={groove.length:.1f} WPAZ={groove.width:.1f} "
            f"ZPAZ={groove.depth:.1f} YPAZ={groove.y_pos:.1f} L=SPAZ-PRIS2\n"
        )
        file_obj.write("N20 L=POFF\n")
        file_obj.write("%\n\n")
    
    def load_from_file(self, filename: str) -> Tuple[Dict[str, float], List[Hole], str, Groove]:
        """
        Загрузка данных из файла .anc
         
        Args:
            filename: Имя файла для загрузки
             
        Returns:
            Кортеж (panel_data, holes, program_name, groove)
             
        Raises:
            Exception: При ошибке загрузки файла
        """
        # Определяем фактическую кодировку файла и запоминаем её,
        # чтобы последующее сохранение использовало ту же кодировку
        self.encoding = self._detect_encoding(filename)
        
        with open(filename, 'r', encoding=self.encoding) as f:
            content = f.read()
         
        # Парсинг данных
        panel_data = self._parse_panel_data(content)
        program_name = self._parse_program_name(content)  # Парсим название программы
        holes = self._parse_holes(content, panel_data['thickness'])
        # panel_data['width'] - длина детали (LX) для подстановки в LPX/LX
        groove = self._parse_groove(content, panel_data['width'])
         
        return panel_data, holes, program_name, groove
     
    def _parse_groove(self, content: str, panel_length: float) -> Groove:
        """
        Парсинг параметров паза из секции [CONTORNATURA01]
        
        Строка паза считается валидной, если:
          - не является закомментированной (не начинается с ';')
          - содержит вызов процедуры L=SPAZ-PRIS2
        
        Номер строки может быть любым (N10, N53 и т.д.), параметры
        могут идти в любом порядке. Отсутствующие параметры берутся
        из DEFAULT_GROOVE. Поддерживаются отрицательные значения
        и выражения с токеном LPX/LX (подставляется длина детали).
        
        Args:
            content: Содержимое файла
            panel_length: Длина детали (LX) для подстановки вместо LPX/LX
        
        Returns:
            Объект Groove (выключен по умолчанию, если валидная строка не найдена)
        """
        # Ищем секцию CONTORNATURA01
        cont_match = re.search(r'\[CONTORNATURA01\](.*?)%', content, re.DOTALL)
        if not cont_match:
            return Groove.from_dict(DEFAULT_GROOVE)
        
        cont_content = cont_match.group(1)
        
        for line in cont_content.splitlines():
            line = line.strip()
            # Пропускаем пустые и закомментированные строки
            if not line or line.startswith(';'):
                continue
            
            # Снимаем произвольный номер строки (N10, N53 и т.д.)
            line = re.sub(r'^N\d+\s*', '', line)
            
            # Строка должна содержать вызов процедуры фрезеровки паза
            if 'L=SPAZ-PRIS2' not in line:
                continue
            
            # Каждый параметр парсим независимо; отсутствующий - из DEFAULT_GROOVE
            data = {
                'enabled': True,
                'length': self._extract_param(line, 'LPAZ', DEFAULT_GROOVE['length'], panel_length),
                'width': self._extract_param(line, 'WPAZ', DEFAULT_GROOVE['width'], panel_length),
                'depth': self._extract_param(line, 'ZPAZ', DEFAULT_GROOVE['depth'], panel_length),
                'y_pos': self._extract_param(line, 'YPAZ', DEFAULT_GROOVE['y_pos'], panel_length)
            }
            
            return Groove.from_dict(data)
        
        return Groove.from_dict(DEFAULT_GROOVE)
    
    def _extract_param(self, line: str, key: str, default: float, panel_length: float) -> float:
        """
        Извлечение значения параметра из строки паза.
        
        Поддерживает отрицательные значения, целые/дробные числа и
        арифметические выражения с токеном LPX/LX (подставляется длина детали).
        
        Args:
            line: Строка без префикса номера строки
            key: Имя параметра (LPAZ, WPAZ, ZPAZ, YPAZ)
            default: Значение по умолчанию, если параметр отсутствует
            panel_length: Длина детали (LX) для подстановки вместо LPX/LX
        
        Returns:
            Числовое значение параметра либо default
        """
        match = re.search(rf'\b{re.escape(key)}=(\S+)', line)
        if not match:
            return float(default)
        value_str = match.group(1)
        # Подставляем длину детали вместо токенов (сначала LPX, т.к. содержит LX как подстроку)
        value_str = value_str.replace('LPX', str(panel_length)).replace('LX', str(panel_length))
        try:
            return evaluate_expression(value_str)
        except Exception:
            return float(default)
    
    def _write_header(self, file_obj, program_name: str = "DETAL") -> None:
        """Запись заголовка файла с указанным названием программы"""
        # Приводим название программы к верхнему регистру для единообразия
        program_name_upper = program_name.upper()
        
        file_obj.write("START\n")
        file_obj.write(f";({program_name_upper})\n")  # Комментарий с названием программы
        file_obj.write("[COMMENTO]\n")
        file_obj.write(f"{program_name_upper}\n\n")  # Название программы
        file_obj.write("[CENTRO01]\n\n")
        
        # Блоки с параметрами
        file_obj.write("PARAMETRI=000000246\n")
        file_obj.write("UTENSILI=000000404\n")
        file_obj.write("LABELF=000001271\n")
        file_obj.write("LABELC=000001236\n")
        file_obj.write("FORATURA=000001201\n")
        file_obj.write("CONTORNATURA=000000420\n")
        file_obj.write("TABELLEFORI=000001217\n")
        file_obj.write("CONFASSIST=000001285\n")
        file_obj.write("ATTREZZAGGIO=000001303\n\n")
    
    def _parse_program_name(self, content: str) -> str:
        """Парсинг названия программы из содержимого файла"""
        # Ищем строку с названием программы в секции COMMENTO
        # Формат: [COMMENTO]\nНАЗВАНИЕ_ПРОГРАММЫ\n
        commento_match = re.search(r'\[COMMENTO\](.*?)(?=\n\[|\n%|\Z)', content, re.DOTALL)
        
        if commento_match:
            commento_content = commento_match.group(1).strip()
            # Берем первую непустую строку после [COMMENTO]
            lines = commento_content.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith(';'):  # Пропускаем комментарии
                    # Удаляем возможные пробелы и лишние символы
                    program_name = line.split()[0] if line.split() else "DETAL"
                    return program_name.upper()  # Возвращаем в верхнем регистре
        
        # Если не нашли, проверяем комментарий в начале файла
        # Формат: ;(НАЗВАНИЕ_ПРОГРАММЫ)
        comment_match = re.search(r'^;\(([^)]+)\)', content, re.MULTILINE)
        if comment_match:
            program_name = comment_match.group(1).strip()
            return program_name.upper()  # Возвращаем в верхнем регистре
        
        # По умолчанию возвращаем DETAL
        return "DETAL"
    
    def _write_parameters(self, file_obj, panel_data: Dict[str, float]) -> None:
        """Запись секции параметров"""
        file_obj.write("[PARAMETRI01]\n")
        file_obj.write(
            f"N10 G71 HC=1 LX={panel_data['width']:.1f} "
            f"LY={panel_data['height']:.1f} "
            f"PLPZ={panel_data['thickness']:.1f} PCSG=0.0 "
            f"LZ={panel_data['thickness']:.1f} "
            f"PUOS=0 FIL=0 BLO=0 ACC=0 RUO=0 PRS=1 PRL=1 KA=0\n"
        )
        file_obj.write("%\n\n")
    
    def _write_empty_section(self, file_obj, section_name: str) -> None:
        """Запись пустой секции"""
        file_obj.write(f"[{section_name}]\n")
        file_obj.write("%\n\n")
    
    def _write_holes_section(self, file_obj, holes: List[Hole]) -> None:
        """Запись секции отверстий"""
        file_obj.write("[TABELLEFORI01]\n")
        
        # Номер строки начинается с 20
        line_number = 20
        
        # Сначала отверстия в плоскости
        for hole in holes:
            if hole.is_top_hole():
                line = self._format_top_hole_line(hole, line_number)
                if line:
                    file_obj.write(line)
                    line_number += 10
        
        # Затем отверстия в кромках
        for hole in holes:
            if hole.is_edge_hole():
                line = self._format_edge_hole_line(hole, line_number)
                if line:
                    file_obj.write(line)
                    line_number += 10
        
        file_obj.write("%\n\n")
    
    def _format_top_hole_line(self, hole: Hole, line_number: int) -> Optional[str]:
        """Форматирование строки для отверстия в плоскости"""
        try:
            # Используем выражение если есть, иначе вычисленное значение
            if hole.x_expr and hole.x_expr.strip():
                x_str = hole.x_expr
            else:
                x_str = f"{hole.x_local:.1f}"
                
            if hole.y_expr and hole.y_expr.strip():
                y_str = hole.y_expr
            else:
                y_str = f"{hole.y_local:.1f}"
            
            # Используем hole.hole_type.value вместо hole.type.value
            return (
                f"N{line_number} SPG={hole.corner.value} "
                f"X={x_str} Y={y_str} "
                f"PRF={hole.depth:.1f} DIA={hole.diameter} "
                f"TPF={hole.hole_type.value} TPI=0 RIP={hole.repeats} "  # Изменено здесь
                f"OX={hole.offset_x_local:.2f} OY={hole.offset_y_local:.2f} OV=V "
                f"ASID={hole.id}\n"
            )
        except Exception as e:
            print(f"Ошибка при форматировании отверстия {hole.id}: {e}")
            return None

    def _format_edge_hole_line(self, hole: Hole, line_number: int) -> Optional[str]:
        """Форматирование строки для отверстия в кромке"""
        try:
            # Используем выражение если есть, иначе вычисленное значение
            if hole.x_expr and hole.x_expr.strip():
                x_str = hole.x_expr
            else:
                x_str = f"{hole.x_local:.1f}"
                
            if hole.z_expr and hole.z_expr.strip():
                z_str = hole.z_expr
            else:
                z_str = f"{hole.z_local:.1f}"
            
            # Формируем строку в зависимости от кромки
            line = f"N{line_number} SPG={hole.corner.value} LAT={hole.edge.value} "
            
            if hole.edge.value in [1, 3]:  # Левая или правая кромка
                # Используем формат Y40.0 (без знака равенства)
                line += f"Y{x_str} Z={z_str} "
            else:  # Верхняя или нижняя кромка
                # Используем формат X40.0 (без знака равенства)
                line += f"X{x_str} Z={z_str} "
            
            # Используем hole.hole_type.value вместо hole.type.value
            line += (
                f"PRF={hole.depth:.1f} DIA={hole.diameter} "
                f"TPF={hole.hole_type.value} TPI=0 RIP={hole.repeats} "  # Изменено здесь
                f"OX={hole.offset_x_local:.2f} OY={hole.offset_y_local:.2f} OV=O "
                f"ASID={hole.id}\n"
            )
            
            return line
        except Exception as e:
            print(f"Ошибка при форматировании отверстия {hole.id}: {e}")
            return None
    
    def _parse_panel_data(self, content: str) -> Dict[str, float]:
        """Парсинг данных панели из содержимого файла"""
        # Значения по умолчанию
        panel_data = DEFAULT_PANEL.copy()
        
        # Ищем секцию PARAMETRI01
        param_match = re.search(r'\[PARAMETRI01\](.*?)%', content, re.DOTALL)
        if not param_match:
            return panel_data
        
        param_content = param_match.group(1)
        
        # Ищем параметры
        lx_match = re.search(r'LX=(\d+\.?\d*)', param_content)
        ly_match = re.search(r'LY=(\d+\.?\d*)', param_content)
        plpz_match = re.search(r'PLPZ=(\d+\.?\d*)', param_content)
        lz_match = re.search(r'LZ=(\d+\.?\d*)', param_content)
        
        if lx_match:
            panel_data['width'] = float(lx_match.group(1))
        if ly_match:
            panel_data['height'] = float(ly_match.group(1))
        
        # Используем PLPZ или LZ для толщины
        if plpz_match:
            panel_data['thickness'] = float(plpz_match.group(1))
        elif lz_match:
            panel_data['thickness'] = float(lz_match.group(1))
        
        return panel_data
    
    def _parse_holes(self, content: str, panel_thickness: float) -> List[Hole]:
        """Парсинг отверстий из содержимого файла"""
        holes = []
        
        # Ищем секцию TABELLEFORI01
        table_match = re.search(r'\[TABELLEFORI01\](.*?)%', content, re.DOTALL)
        if not table_match:
            return holes
        
        table_content = table_match.group(1)
        
        # Разбиваем на строки
        lines = table_content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            
            # Пропускаем номер строки
            if line.startswith('N'):
                line = re.sub(r'^N\d+\s*', '', line)
            
            # Парсим отверстие
            hole = self._parse_hole_line(line, panel_thickness)
            if hole:
                holes.append(hole)
        
        return holes
    
    def _parse_hole_line(self, line: str, panel_thickness: float) -> Optional[Hole]:
        """Парсинг строки с отверстием"""
        try:
            # НОВЫЙ ПОДХОД: Разбиваем строку на токены по пробелам
            # Каждый токен - это либо ключ=значение, либо координата (X, Y, Z) без знака равенства
            tokens = line.split()
            
            params = {}
            current_key = None
            
            for token in tokens:
                # Проверяем, содержит ли токен знак равенства
                if '=' in token:
                    # Токен в формате ключ=значение
                    parts = token.split('=', 1)  # Разделяем только по первому знаку равенства
                    if len(parts) == 2:
                        key, value = parts
                        params[key] = value
                        current_key = None
                else:
                    # Токен может быть координатой без знака равенства или продолжением предыдущего значения
                    # Проверяем, начинается ли токен с X, Y или Z
                    if token.startswith(('X', 'Y', 'Z')):
                        # Координата без знака равенства (например, X40.0)
                        # Извлекаем первую букву как ключ, остальное как значение
                        key = token[0]
                        value = token[1:]
                        params[key] = value
                        current_key = None
                    elif current_key is not None:
                        # Продолжение предыдущего значения (если выражение содержало пробелы)
                        # Но по нашему соглашению, выражения не содержат пробелов
                        # Поэтому просто пропускаем или объединяем
                        pass
            
            if 'ASID' not in params:
                return None
            
            # Функция для замены PLPZ в выражениях
            def replace_plpz_in_expression(expr: str) -> str:
                """Заменяет PLPZ на фактическое значение толщины панели"""
                if not expr:
                    return expr
                
                # Заменяем PLPZ на значение толщины
                expr = expr.replace('PLPZ', str(panel_thickness))
                
                # Также заменяем PLPZ/2, PLPZ*0.5 и т.д.
                expr = expr.replace('PLPZ/2', str(panel_thickness / 2))
                expr = expr.replace('PLPZ*0.5', str(panel_thickness / 2))
                expr = expr.replace('PLPZ*0.5', str(panel_thickness / 2))
                
                return expr
            
            # Базовые параметры
            hole_id = int(params.get('ASID', 0))
            corner = int(params.get('SPG', 1))
            edge = int(params.get('LAT', 1))
            diameter = int(float(params.get('DIA', 8)))
            
            # Обработка глубины (может быть выражением)
            depth_expr = params.get('PRF', '10')
            depth_expr = replace_plpz_in_expression(depth_expr)
            try:
                depth = evaluate_expression(depth_expr)
            except:
                depth = 10.0
            
            hole_type = int(params.get('TPF', 1))
            repeats = int(params.get('RIP', 1))
            offset_x = float(params.get('OX', 0))
            offset_y = float(params.get('OY', 0))
            
            # Определяем ориентацию
            orientation = params.get('OV', 'V')
            
            # Обработка координат с заменой PLPZ
            if orientation == 'V':  # Отверстие в плоскости
                # Получаем выражения для X и Y
                x_expr = params.get('X', '0')
                y_expr = params.get('Y', '0')
                
                # Заменяем PLPZ в выражениях
                x_expr = replace_plpz_in_expression(x_expr)
                y_expr = replace_plpz_in_expression(y_expr)
                
                # Вычисляем значения
                try:
                    x_local = evaluate_expression(x_expr)
                except:
                    x_local = 0.0
                    
                try:
                    y_local = evaluate_expression(y_expr)
                except:
                    y_local = 0.0
                    
                z_local = 0.0
                z_expr = ""
            else:  # Отверстие в кромке
                if edge in [1, 3]:  # Левая/правая кромка
                    # Y - координата вдоль кромки (в файле без знака равенства)
                    x_expr = params.get('Y', '0')
                    z_expr = params.get('Z', '0')
                else:  # Верхняя/нижняя кромка
                    # X - координата вдоль кромки (в файле без знака равенства)
                    x_expr = params.get('X', '0')
                    z_expr = params.get('Z', '0')
                
                y_expr = ""
                
                # Заменяем PLPZ в выражениях
                x_expr = replace_plpz_in_expression(x_expr)
                z_expr = replace_plpz_in_expression(z_expr)
                
                # Вычисляем значения
                try:
                    x_local = evaluate_expression(x_expr)
                except:
                    x_local = 0.0
                    
                try:
                    z_local = evaluate_expression(z_expr)
                except:
                    z_local = 0.0
                    
                y_local = 0.0
            
            # Создаем объект Hole с выражениями
            return Hole(
                id=hole_id,
                corner=corner,
                edge=edge,
                orientation=orientation,
                x_local=x_local,
                y_local=y_local,
                z_local=z_local,
                x_expr=x_expr,  # Сохраняем исходное выражение
                y_expr=y_expr,
                z_expr=z_expr,
                diameter=diameter,
                depth=depth,
                hole_type=hole_type,
                repeats=repeats,
                offset_x_local=offset_x,
                offset_y_local=offset_y
            )
            
        except Exception as e:
            print(f"Ошибка при парсинге строки: {line}")
            print(f"Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return None