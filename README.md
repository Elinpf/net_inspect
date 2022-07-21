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
from net_inspect import NetInspect, OutputPluginAbstract, PluginError
from rich.table import Table
from rich.console import Console


class Output(OutputPluginAbstract):
    def main(self):
        if not self.params.output_params.get('company'):
            raise PluginError('name or age is missing')

        console = Console()

        table = Table(title=self.params.output_params.get(
            'company'), show_lines=False)
        table.add_column('name', justify='center')
        table.add_column('ip', justify='center')
        table.add_column('model', justify='center')
        table.add_column('version', justify='center')
        table.add_column('power', justify='center')

        for device in self.params.devices:
            if device.vendor.PLATFORM == 'huawei_vrp':
                data = [device.info.name, device.info.ip]
                ps = device.parse_result('display version')
                data.append(ps[0].get('model'))
                data.append(ps[0].get('vrp_version'))
                power_analysis = device.analysis_result.get('Power Status')
                power_desc = []
                for alarm in power_analysis:
                    if alarm.is_focus:
                        power_desc.append(alarm.message)
                data.append('\n'.join(power_desc) if power_desc else 'Normal')

                table.add_row(*data)
                table.row_styles = ['green']

        console.print(table)


net = NetInspect()
# net.set_log_level('DEBUG')
net.set_plugins('smartone', Output)
cluster = net.run('log_files', 'output',
                  output_plugin_params={'company': 'Company Name'})
```

## 关于贡献

分析插件还在持续开发中，`develop_script.py`脚本就是为高效开发提供的一个工具。

开发一个分析插件的流程，以开发检查风扇状态的`fan_status`插件为例：

1. 创建一个新的插件文件, 对应的文件初始状态会一并准备好

```bash
python ./develop_script.py -p fan_status -g
```

2. 在对应的文件中实现插件对每个厂商分析的函数

```py
class AnalysisPluginWithFanStatus(AnalysisPluginAbc):
    """
    要求设备所有在位风扇模块运行在正常状态。
    """
    @analysis.vendor(vendor.H3C)
    @analysis.template_key('hp_comware_display_fan.textfsm', ['slot', 'id', 'status'])
    def hp_comware(template: TemplateInfo, result: AnalysisResult):
        """模块状态不为Normal的时候告警"""
        for row in template['display fan']:
            if row['status'].lower() != 'normal':
                result.add_warning(
                    f'Slot {row["slot"]} Fan {row["id"]} 状态异常' if row['slot'] else f'Fan {row["id"]} 状态异常')
```

其中`@analysis`是用来记录插件的分析类型的，`vendor`记录插件的厂商类型，`template_key`记录分析模块所需要的`textfsm`文件以及里面的哪些值。
这些值会在参数`template: TemplateInfo`中给出。

`result: AnalysisResult`用来记录分析结果。可以添加告警信息。

分析方法为类方法，不需要`self`,不需要给出返回值。

插件中的类注释和方法注释都会被记录下来，方便后续调用。

3. 创建对应的测试文件

当编写了对应的分析方法后，再次执行创建命令，工具会自动根据分析方法中需要的命令，生成对应的测试文件。

测试文件路径为`tests/check_analysis_plugins/<plugin_name>/<funcation_name>.raw`

```bash
python ./development_script.py -p fan_status -f hp_comware -g
```

4. 在测试文件中添加测试用例
5. 执行测试

```bash
python ./development_script.py -p fan_status -f hp_comware -t
```

6. 完成测试，确认测试结果为正常后，生成yml文件作为参考文件。

```bash
python ./development_script.py -p fan_status -f hp_comware -y
```

