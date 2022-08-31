from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Tuple

from ..domain import OutputPluginAbstract
from ..third_party.excel import CellContext, Excel

if TYPE_CHECKING:
    from ..domain import Device


class OutputPluginWithExcelReport(OutputPluginAbstract):
    """Microsoft Excel 巡检报告"""

    base_info_keys = [
        ('hostname', '设备名称'),
        ('ip', 'IP'),
        ('vendor', '厂商'),
        ('model', '型号'),
        ('version', '软件版本'),
        ('uptime', '启动时长')
    ]

    status_info_keys = [
        ('cpu_usage', 'CPU利用率'),
        ('memory_usage', '内存利用率'),
        ('analysis.fan', '风扇状态'),
        ('analysis.power', '电源状态'),
    ]

    @dataclass
    class Values:
        max_column: int = 'F'  # 最大列
        column_width: int = 17  # 列宽
        header_title: str = '现场巡检报告'  # 标题
        header_font: str = '等线'  # 标题字体
        header_font_size: int = 28  # 标题字体大小
        body_font: str = '等线'  # 内容字体
        body_font_size: int = 14  # 内容字体大小
        sn_lines: int = 10  # 序列号至少行数

    def __init__(self):
        self.excel = Excel()
        self.next_row = 1  # table的起始行号

        self.values = self.Values()

    def main(self):
        """主程序"""
        self.set_values()
        self.set_excel()

        for device in self.args.devices:
            self.report(device)
        self.excel.save(self.args.path)

    def set_values(self):
        """可以用于重载设置Value值"""
        pass

    def set_excel(self):
        """对表格的设置"""
        self.excel.set_all_column_width(
            self.values.column_width, self.values.max_column)

    def report(self, device: Device):
        """单一报告生成流程"""
        self.report_header(device)
        self.report_body(device)
        self.report_serial_number(device)
        self.report_status(device)

    def report_header(self, device: Device):
        """生成报告头"""
        cell = CellContext(self.values.header_title
                           ).set_font(name=self.values.header_font,
                                      size=self.values.header_font_size)
        self.excel.write_rows(
            rows=[[cell]],
            merge=[('A', self.values.max_column)]
        )

    def report_body(self, device: Device):
        """生成报告体"""
        self.report_body_baseinfo(device)

    def report_title(self, title: str):
        """生成标题头"""
        cell = CellContext(title).set_font(name=self.values.body_font,
                                           size=self.values.body_font_size)
        self.excel.write_rows(
            rows=[[cell]],
            merge=[('A', self.values.max_column)]
        )

    def report_body_baseinfo(self, device: Device):
        """生成基本信息"""
        self.report_title('1. 基本信息')
        rows = self._mulit_keys(self.base_info_keys, device, 2)

        self.excel.write_rows(
            rows=rows,
            merge=[('B', 'C'), ('E', self.values.max_column)]
        )

    def report_serial_number(self, device: Device):
        """生成序列号"""
        self.report_title('2. 序列号')

        sn_list = device.info.sn
        if self.values.sn_lines > len(sn_list):
            for _ in range(self.values.sn_lines - len(sn_list)):
                sn_list.append(('', ''))

        for pid, sn in sn_list:
            self.excel.write_rows(
                rows=[[CellContext(pid), CellContext(sn)]],
                merge=[('A', 'B'), ('C', self.values.max_column)]
            )

    def report_status(self, device: Device):
        """生成状态信息"""
        self.report_title('3. 状态信息')
        rows = self._mulit_keys(self.status_info_keys, device, 2)
        self.excel.write_rows(
            rows=rows,
            merge=[('B', 'C'), ('E', self.values.max_column)]
        )

    def _mulit_keys(self, keys: List[Tuple[str, str]], device: Device, num: int) -> List[List[CellContext]]:
        """
        每行写入多个值
            Args:
                - keys: 写入的值列表
                - device: 设备对象
                - num: 每行写入的数量

            Return:
                - rows: 写入的值列表
        """
        info = device.info
        rows = []
        for idx, key_tup in enumerate(keys):
            title = CellContext(key_tup[1]).set_font(bold=True)

            # 当遇到analysis.fan这种类型的时候，循环获取analysis.fan的值，并转换为字符串
            if '.' in key_tup[0]:
                key_list = key_tup[0].split('.')
                _value = getattr(info, key_list.pop(0))
                for key in key_list:
                    _value = getattr(_value, key)

                # 如果是bool类型，则显示正常还是异常
                if isinstance(_value, bool):
                    _value = '正常' if _value else '异常'

                value = CellContext(str(_value))
            else:
                value = CellContext(getattr(info, key_tup[0]))

            # 每行写入的数量
            if idx % num == 0:
                rows.append([title, value])
            else:
                rows[-1].extend([title, value])

        return rows
