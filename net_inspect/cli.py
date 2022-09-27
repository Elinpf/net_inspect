from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Type

import rich_typer as typer
from rich import print
from rich.console import Console
from rich.table import Table

from . import NetInspect, __version__
from .analysis_plugin import analysis

if TYPE_CHECKING:
    from .domain import PluginAbstract


app = typer.RichTyper(add_completion=False)
console = Console()

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
BANNER = (
    f"[b]Network Inspect[/b] [magenta]v{__version__}[/] 🤑\n\n[dim]网络设备数据结构化分析框架[/]\n"
)
URL = "♥ https://github.com/Elinpf/net_inspect"


def print_plugin_list(all_plugins: Dict[str, Dict[str, Type[PluginAbstract]]]):
    """打印插件列表"""
    column_names = ['插件名称', '简写', '描述']
    for plugin_type, plugins in all_plugins.items():
        row_list = []
        for plugin_name, plugin_cls in plugins.items():
            instance = plugin_cls()
            row_list.append([plugin_name, instance.short_name, instance.doc])

        print_table(plugin_type, column_names, row_list)
        print()


def print_table(table_name: str, items: list, rows: list):
    """打印表格"""
    table = Table(title=f"[bold reverse cyan]{table_name}[/]", title_justify='left')
    for item in items:
        table.add_column(item)
    for row in rows:
        table.add_row(*row)

    table.expand = True
    console.print(table, justify='left')


def print_analysis_list():
    """打印每个分析模块支持的厂商"""
    analysis_vendor_dict = {}
    for info in analysis.store:
        if info.plugin_name not in analysis_vendor_dict:
            analysis_vendor_dict[info.plugin_name] = []
        analysis_vendor_dict[info.plugin_name].append(info.vendor_platform)

    # 对厂商进行排序
    rows = []
    for plugin_name, vendors in analysis_vendor_dict.items():
        rows.append([plugin_name, ', '.join(sorted(vendors)), str(len(vendors))])

    # 打印表格
    print_table('分析模块支持的厂商平台', ['插件名称', '厂商', '数量'], rows)
    print()


def print_base_info_list():
    """打印基础信息所包含的属性"""
    from .base_info import AnalysisInfo, BaseInfo

    base_info_field = BaseInfo().__annotations__
    analysis_info_field = AnalysisInfo().__annotations__
    rows = []
    for info, type in base_info_field.items():  # base_info中的属性
        if info == 'analysis':
            continue
        rows.append([info, type.replace('[', '\[')])

    for info, type in analysis_info_field.items():  # analysis中的属性
        rows.append(['analysis.' + info, type.replace('[', '\[')])

    print_table('基础信息所包含的属性', ['属性名称', '类型'], rows)
    print()


@app.command(
    banner=BANNER,
    banner_justify='center',
    context_settings=CONTEXT_SETTINGS,
    epilog=URL,
)
def main(
    ctx: typer.Context,
    input_path: str = typer.Option(None, '--input', '-i', help='输入的文件路径，可以是文件夹'),
    input_plugin: str = typer.Option('console', '--input-plugin', '-I', help='设置输入插件'),
    output_plugin: str = typer.Option(
        'device_list', '--output-plugin', '-O', help='设置输出插件'
    ),
    output_path: str = typer.Option('', '--output', '-o', help='输出的文件路径'),
    verbose: int = typer.Option(
        0, '--verbose', '-v', help='设置DEBUG等级(-v, -vv)', count=True, show_default=False
    ),
    plugin_list: bool = typer.Option(False, '--plugin-list', '-l', help='显示插件列表'),
    analysis_list: bool = typer.Option(
        False, '--analysis-list', '-L', help='显示分析插件所支持的厂商列表'
    ),
    base_info_list: bool = typer.Option(
        False, '--base-info-list', '-b', help='显示基础信息属性列表'
    ),
):
    net = NetInspect()
    net.set_plugins(input_plugin=input_plugin, output_plugin=output_plugin)
    if verbose == 1:
        net.enbale_console_log('INFO')
    elif verbose == 2:
        net.enbale_console_log('DEBUG')

    if plugin_list:
        print()
        print_plugin_list(net.get_all_plugins())
        exit()

    if analysis_list:
        print()
        print_analysis_list()
        exit()

    if base_info_list:
        print()
        print_base_info_list()
        exit()

    if input_path:
        net.run(input_path=input_path, output_file_path=output_path)
        exit()
