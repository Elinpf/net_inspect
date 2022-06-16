from __future__ import annotations
import os
import shlex
from typing import Dict, List, Type
from argparse import ArgumentParser, Namespace

from net_inspect.bootstrap import bootstrap
from net_inspect.analysis_plugin import AnalysisPluginAbc
from net_inspect.func import get_command_from_textfsm

PLUGIN_DIR = os.path.join('net_inspect', 'plugins')
TEST_ANALYSIS_PLUGIN_DIR = os.path.join('tests', 'check_analysis_plugins')


class NotFoundErr(Exception):
    ...


def parse_args(command: str = '') -> Namespace:
    args = ArgumentParser()
    args.add_argument('-n', '--name', type=str,
                      help='模块名称，必须指定', required=True)
    args.add_argument('-g', '--generate', action='store_true',
                      help='创建Analysis模块文件')

    args.add_argument('-v', '--vendor', type=str, help='创建指定的厂商的测试文件')
    args.add_argument('-i', '--index', type=int,
                      help='创建第几个测试文件, 可以配合--vendor使用', default=1)
    if command:
        return args.parse_args(shlex.split(command))

    return args.parse_args()


def long_plugin_name(name: str) -> str:
    """将模块名称转化为文件名的格式"""
    name = name.lower()
    name = name.replace(' ', '_')
    if not name.startswith('analysis_plugin_with_'):
        name = 'analysis_plugin_with_' + name

    return name


def generate_file(plugin_name: str, give_vendor: str | None, index: int):
    """当没有插件文件的时候，创建插件文件，
    当有插件文件的时候，读取插件文件的插件，并且创建对应的测试文件"""
    file_name = plugin_name + '.py'
    if not os.path.exists(os.path.join(PLUGIN_DIR, file_name)):  # 如果没有插件文件，则创建插件文件
        open(os.path.join(PLUGIN_DIR, file_name), 'w').write('')
        return

    # 如果有插件文件，则读取插件文件的插件，并且创建对应的测试文件
    # 插件仓库
    plugin_repository = bootstrap()
    plugin = plugin_repository.get_analysis_plugin(
        plugin_name)  # type: Type[AnalysisPluginAbc]
    if not plugin:
        raise NotFoundErr

    vendors: Dict[str, List[str]] = {}
    plugin = plugin()  # type: AnalysisPluginAbc

    for vendor, fsm_dict in plugin._ntc_templates.items():
        cmd_list = []
        for fsm_name in fsm_dict.keys():
            cmd_list.append(get_command_from_textfsm(
                vendor.PLATFORM, fsm_name))
        vendors[vendor.PLATFORM] = cmd_list

    # 创建测试文件目录
    if not os.path.exists(os.path.join(TEST_ANALYSIS_PLUGIN_DIR, plugin_name)):
        os.mkdir(os.path.join(TEST_ANALYSIS_PLUGIN_DIR, plugin_name))

    for vendor_platform, cmd_list in vendors.items():
        # 当给出了厂商的时候，只创建对应的厂商的测试文件
        if give_vendor and vendor_platform != give_vendor:
            continue

        # 创建测试raw文件
        index_str = str(index) if index > 1 else ''
        raw_file = os.path.join(TEST_ANALYSIS_PLUGIN_DIR,
                                plugin_name, vendor_platform + index_str + '.raw')
        if not os.path.exists(raw_file):
            open(raw_file, 'w').write(write_cmds(cmd_list))


def write_cmds(cmd_list: list):
    """插入命令到文件中"""
    for i, cmd in enumerate(cmd_list):
        cmd_list[i] = f'-------------------------{cmd}-------------------------'

    return '\n\n\n\n'.join(cmd_list)


if __name__ == '__main__':
    command = "-n 'power status' -g"
    args = parse_args(command)
    plugin_name = long_plugin_name(args.name)

    if args.generate:
        generate_file(plugin_name, args.vendor, args.index)
        exit()
