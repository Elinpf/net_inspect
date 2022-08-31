from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Tuple

from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import column_index_from_string, get_column_letter
from openpyxl.workbook import Workbook

if TYPE_CHECKING:
    from openpyxl.worksheet.worksheet import Worksheet


class Excel():
    def __init__(self):
        self.wb, self.sheet = self.init_excel()
        self.next_row = 1  # table的起始行号

    def init_excel(self) -> Tuple[Workbook, Worksheet]:
        """初始化 Excel"""
        wb = Workbook()
        sheet = wb.active
        return wb, sheet

    def save(self, file_path: str):
        self.wb.save(file_path)

    def set_all_column_width(self, width: int, max_col: str = 'A'):
        """设置所有列的宽度"""
        for col in range(1, column_index_from_string(max_col) + 1):
            self.sheet.column_dimensions[get_column_letter(col)].width = width

    def write_rows(
        self,
        rows: List[List[CellContext]],
        merge: List[Tuple[str, str]] = None,
    ):
        """
        这个方法是按行来进行写入的, 并且合并操作是每行都会执行一次

        Args:
            - rows 每行数据的每个数据

        """

        # 获取要跳过的列
        skip_cols = []
        if merge:
            for merge_item in merge:
                start_col = column_index_from_string(merge_item[0]) + 1
                end_col = column_index_from_string(merge_item[1])
                if start_col == end_col:
                    skip_cols.append(start_col)
                else:
                    skip_cols.extend(range(start_col, end_col + 1))

        for i, row in enumerate(rows):
            col_i = 1
            while row:
                # 跳过合并过的单元格
                if col_i in skip_cols:
                    col_i += 1
                    continue

                current_row = self.next_row + i

                current_cell = self.sheet.cell(current_row, col_i)
                cell = row.pop(0)
                current_cell.value = cell.value
                current_cell.alignment = cell.align
                current_cell.border = cell.border
                current_cell.font = cell.font
                col_i += 1

            if merge is not None:  # 对每行进行合并
                for col_start, col_end in merge:
                    col_start = column_index_from_string(col_start)
                    col_end = column_index_from_string(col_end)
                    self.sheet.merge_cells(
                        start_row=self.next_row + i,
                        start_column=col_start,
                        end_row=self.next_row + i,
                        end_column=col_end
                    )
        self.next_row += len(rows)  # 更新行号


class CellContext():
    """对单元格设置进行集成"""

    @dataclass
    class Style():
        align: str = Alignment(horizontal='center', vertical='center')
        border: str = Border(
            left=Side(border_style='thin', color='000000'),
            right=Side(border_style='thin', color='000000'),
            top=Side(border_style='thin', color='000000'),
            bottom=Side(border_style='thin', color='000000'))
        font: str = Font(name='等线', size=10, bold=False,
                         italic=False, strike=False, color='000000')

    def __init__(self, value: str):
        self.value = value
        self.style = self.init_style()

    def init_style(self) -> Style:
        """初始化样式"""
        style = self.Style()
        return style

    @property
    def align(self) -> Alignment:
        return self.style.align

    def set_align(self, align: str) -> Style:
        """设置对齐方式"""
        self.style.align = Alignment(horizontal=align)
        return self

    @property
    def border(self) -> Border:
        return self.style.border

    def set_border(self, border: str) -> Style:
        """设置边框"""
        self.style.border = Border(border_style=border)
        return self

    @property
    def font(self) -> Font:
        return self.style.font

    def set_font(
        self,
        name: str = '等线',
        size: int = 10,
        bold: bool = False,
        italic: bool = False,
        strike: bool = False,
        color: str = '000000'
    ) -> Style:
        """设置字体"""
        self.style.font = Font(
            name=name, size=size, bold=bold, italic=italic, strike=strike, color=color)
        return self

    def get_style(self) -> Style:
        """获取样式"""
        return self.style
