# net_inspect 介绍

`net_inspect`是网络设备数据结构化分析框架


## 安装方法

### PyPI

```bash
pip install net_inspect
```

### Poetry

```bash
git clone https://github.com/Elinpf/net_inspect
cd net_inspect
poetry install
```

## 使用方法

`net_inspect`有三种使用方式

1. 作为三方库提供API
2. CLI命令行操作 (TODO)
3. 本地Web界面操作 (TODO)


### 使用库

```python
from net_inspect import NetInspect, OutputPluginAbstract, PluginError, DeviceList
from typing import Dict
from rich.table import Table
from rich.console import Console


class Output(OutputPluginAbstract):
    def main(self, devices: DeviceList, path, params: Dict[str, str]):
        if not params.get('company'):
            raise PluginError('name or age is missing')

        console = Console()

        table = Table(title=params.get('company'), show_lines=False)
        table.add_column('name', justify='center')
        table.add_column('ip', justify='center')
        table.add_column('model', justify='center')
        table.add_column('version', justify='center')
        table.add_column('power', justify='center')

        for device in devices:
            if device.vendor.PLATFORM == 'huawei_vrp':
                data = [device.device_info.name, device.device_info.ip]
                cmd = device.search_cmd('dis version')
                res = cmd._parse_result
                data.append(res[0].get('model'))
                data.append(res[0].get('vrp_version'))
                power_result = device.analysis_result.get('Power Status')
                if power_result:
                    data.append(
                        power_result.message if power_result.is_focus() else 'Normal')
                table.add_row(*data)
                table.row_styles = ['green']

        console.print(table)


net = NetInspect()
net.set_plugins('console', Output)
cluster = net.run('log_files', 'output', {'company': 'Company Name'})
```