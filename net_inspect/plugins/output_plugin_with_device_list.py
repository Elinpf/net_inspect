from rich import print
from rich.table import Table
from ..domain import OutputPluginAbstract


class OutputPluginWithDeviceList(OutputPluginAbstract):
    """
    输出设备列表信息
    """

    def main(self):
        table = Table(title='设备列表')
        columns = ['设备名称', '厂商', '型号', 'IP', 'CPU %', 'Mem %']
        for col in columns:
            table.add_column(col, justify='center')
        table.row_styles = ['green']

        for device in self.args.devices:
            info = device.info
            row = [
                info.hostname,
                info.vendor,
                info.model,
                info.ip,
                info.cpu_usage,
                info.memory_usage,
            ]
            table.add_row(*row)

        print(table)
        print('total devices:', len(self.args.devices))
