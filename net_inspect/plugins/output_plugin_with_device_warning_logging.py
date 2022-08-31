from rich import print
from ..domain import OutputPluginAbstract


class OutputPluginWithDeviceWarningLogging(OutputPluginAbstract):
    """
    以漂亮的格式输出所有设备的告警信息
    """

    def main(self):
        for device in self.args.devices:
            for warn in device.analysis_result:
                if warn.above_focus:
                    print(f"[green]%s[/] -- [{'red' if warn.is_warning else 'yellow'}]%s[/] -- %s" %
                          (device.info.hostname, warn.level_str, warn.message))
