from rich import print
from rich.table import Table
from ..domain import OutputPluginAbstract


class OutputPluginWithDeviceList(OutputPluginAbstract):
    """
    输出设备列表信息
    """

    def main(self):
        table = Table(title='设备列表')
        columns = ['设备名称', '厂商', '型号', 'IP']
        for col in columns:
            table.add_column(col)

        for device in self.args.devices:
            row = [
                device.info.hostname,
                device.info.vendor,
                device.info.model,
                device.info.ip
            ]
            table.add_row(*row)

        print(table)
