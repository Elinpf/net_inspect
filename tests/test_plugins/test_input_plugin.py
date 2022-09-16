import re

from net_inspect.plugins.input_plugin_with_console import (
    InputPluginWithConsole, simialr_huawei_reg, similar_cisco_reg)
from net_inspect.plugins.input_plugin_with_smartone import \
    InputPluginWithSmartOne


def test_input_plugin_with_console_simalr_huawei_reg():

    test_list = [
        ('<device>display version', 'device'),
        ('[device] dis version', 'device'),
        ('<GZ-24F-SN1-248.16>display version', 'GZ-24F-SN1-248.16')
    ]

    for (line, refer_hostname) in test_list:
        match = re.match(simialr_huawei_reg, line)
        assert match.group('device_name') == refer_hostname
        assert re.match(r'\s*dis.*ver', match.group('cmd'))


def test_input_pulgin_with_console_simalr_cisco_reg():

    test_list = [
        ('device>show version', 'device'),
        ('device(config)# sh version', 'device'),
        ('device-1(config-if)# sh version', 'device-1'),
    ]

    for (line, refer_hostname) in test_list:
        match = re.match(similar_cisco_reg, line)
        assert match.group('device_name') == refer_hostname
        assert re.match(r'\s*sh.*ver', match.group('cmd'))


def test_input_plugin_with_lower_commands():
    """保证cmd_dict.keys()是小写的"""

    input_plugin = InputPluginWithConsole()
    stream = """\
<YY_XX_YH_AR01>DIS version 
Huawei Versatile Routing Platform Software
VRP (R) software, Version 5.170 (AR2200 V200R009C00SPC500)
Copyright (C) 2011-2018 HUAWEI TECH CO., LTD
Huawei AR2204-51GE-P Router uptime is 104 weeks, 4 days, 21 hours, 46 minutes

MPU 0(Master) : uptime is 104 weeks, 4 days, 21 hours, 44 minutes
SDRAM Memory Size    : 512     M bytes
Flash 0 Memory Size  : 512     M bytes
MPU version information : 
1. PCB      Version  : AR-SRU2204C VER.B
2. MAB      Version  : 0
3. Board    Type     : AR2204-51GE-P
4. CPLD0    Version  : 100
5. BootROM  Version  : 1
"""
    res = input_plugin.main('', stream)
    cmd_dict, _ = res
    lower_cmd_dict = input_plugin._lower_keys(cmd_dict)
    assert lower_cmd_dict.get('dis version')


def test_console_plugin_with_prompt():
    """测试console plugin的命令提示符切割方法"""

    input_plugin = InputPluginWithConsole()
    stream = """\
<device>display version
Huawei Versatile Routing Platform Software
VRP (R) software, Version 5.170 (AR2200 V200R009C00SPC500)
Copyright (C) 2011-2018 HUAWEI TECH CO., LTD
Huawei AR2204-51GE-P Router uptime is 104 weeks, 4 days, 21 hours, 46 minutes
<device>!
        ^
Error: Unrecognized command found at '^' position.
"""
    res = input_plugin.main('', stream)
    cmd_dict, _ = res
    assert not re.search(r'Error:', cmd_dict.get('display version'))


def test_console_plugin_with_file(shared_datadir):
    """测试console plugin的比较复杂的文件"""

    input_plugin = InputPluginWithConsole()
    res = input_plugin.run(shared_datadir / 'console_input.log')
    cmd_dict, _ = res
    # 文件中的是 DIS version , 要求改为小写
    assert cmd_dict.get('dis version')

    # 文件中有两个dis cpu-usage, 其中一个被截断了，只保留最长的那个
    assert len(cmd_dict.get('dis cpu-usage').split("\n")) > 20


def test_smartone_plugin_state_1(shared_datadir):
    """测试 smartone plugin 情况一"""

    input_plugin = InputPluginWithSmartOne()
    result = input_plugin.run(
        shared_datadir / 'B_FOO_BAR_DS02_21.2.3.4_20220221170516.diag')
    cmd_dict = result[0]
    device_info = result[1]
    assert device_info.name == 'B_FOO_BAR_DS02'
    assert device_info.ip == '21.2.3.4'
    assert len(cmd_dict) == 13
    assert len(cmd_dict['dis version'].split('\n')) > 6  # 判断是有内容的


def test_smartone_plugin_state_2(shared_datadir):
    """测试 smartone plugin 情况二"""

    input_plugin = InputPluginWithSmartOne()
    result = input_plugin.run(
        shared_datadir / 'B_FOO_BAR_AR01_21.1.1.1.diag')
    cmd_dict = result[0]
    device_info = result[1]
    assert device_info.name == 'B_FOO_BAR_AR01'
    assert device_info.ip == '21.1.1.1'
    assert len(cmd_dict) == 16
    assert len(cmd_dict['dis version'].split('\n')) > 6  # 判断是有内容的
