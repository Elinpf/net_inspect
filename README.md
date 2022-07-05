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

## 插件介绍

`net_inspect`采用了插件模块的框架，分别是`Input`, `Parse`, `Analysis`, `Output` 模块。

通过编写模块插件，实现快速定制的能力。

### InputPlugin

Input插件的功能是将**已经获得的设备检查命令的日志**转化为命令与命令输出的对应关系。如果是通过直接对设备进行操作获取的日志，可以使用`console`这个插件进行处理。如果是用的第三方平台进行的自动化收集，那么就需要自行编写Input插件实现命令与输出的对应。

### ParsePlugin

Parse插件的功能是将每条命令的输出进行解析并且结构化。提取出关键信息并以`List[dict]`的方式进行存储。

现有的`Parse`解析模块使用的是[ntc-templates-elinpf](https://github.com/Elinpf/ntc-templates)这个库，是`ntc-templates`库的分支，由于主仓更新频率很慢且不会增加国内常用的设备厂家，所以我Fork后进行了修改。


### AnalysisPlugin

Analysis插件的功能是将解析的信息进行分析，对分析的内容进行告警分级。例如电源是否异常。这个工作是在分析模块中进行的。

### OutputPlugin

输出模块可能是最需要自定义编写的地方。将解析和分析的结果按照自己想要的格式展现出来。

## 使用方法

`net_inspect`有三种使用方式

1. 作为三方库提供API
2. CLI命令行操作 (TODO)
3. 本地Web界面操作 (TODO)


### 使用库

示例:

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
                data = [device.info.name, device.info.ip]
                ps = device.parse_result('display version') # 获取解析的内容
                data.append(ps[0].get('model'))
                data.append(ps[0].get('vrp_version'))
                power_analysis = device.analysis_result.get('Power Status') # 获取分析的内容
                if power_analysis:
                    data.append(
                        power_analysis.message if power_analysis.is_focus else 'Normal')
                table.add_row(*data)
                table.row_styles = ['green']

        console.print(table)


net = NetInspect()
# net.set_log_level('DEBUG')
net.set_plugins('smartone', Output)
cluster = net.run('log_files', 'output',
                  output_plugin_params={'company': 'Company Name'})
```