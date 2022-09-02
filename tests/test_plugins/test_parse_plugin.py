from net_inspect.plugins.parse_plugin_with_ntc_templates import ParsePluginWithNtcTemplates
from net_inspect.domain import Cmd

huawei_verison = """
Huawei Versatile Routing Platform Software
VRP (R) software, Version 8.180 (NE20E V800R010C10SPC500)
Copyright (C) 2012-2018 Huawei Technologies Co., Ltd.
HUAWEI NE20E-S4 uptime is 169 days, 13 hours, 50 minutes 
Patch Version: V800R010SPH120

NE20E-S4 version information:
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
BKP  version information:
  PCB         Version : CX68BKP01B REV A
  MPU  Slot  Quantity : 2
  NSP  Slot  Quantity : 1
  CARD Slot  Quantity : 4
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
MPU version information:

MPU (Master) 6 : uptime is 169 days, 13 hours, 46 minutes
  StartupTime 2021/09/05   02:39:58
  SDRAM Memory Size   : 2048 M bytes
  FLASH Memory Size   : 16 M bytes
  NVRAM Memory Size   : 512 K bytes
  CFCARD Memory Size  : 2048 M bytes
  MPU CR2D00MPUE10 version information:
  PCB         Version : CX68MPUK REV B
  EPLD        Version : 107
  FPGA        Version : 109
  BootROM     Version : 03.47
  BootLoad    Version : 03.47

MPU (Slave) 7 : uptime is 169 days, 13 hours, 46 minutes
  StartupTime 2021/09/05   02:39:57
  SDRAM Memory Size   : 2048 M bytes
  FLASH Memory Size   : 16 M bytes
  NVRAM Memory Size   : 512 K bytes
  CFCARD Memory Size  : 2048 M bytes
  MPU CR2D00MPUE10 version information:
  PCB         Version : CX68MPUK REV B
  EPLD        Version : 107
  FPGA        Version : 109
  BootROM     Version : 03.47
  BootLoad    Version : 03.47
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
"""


def test_ntc_templates_parse():
    """使用ntc_templates模板解析"""
    cmd = Cmd('display version')
    cmd.content = huawei_verison
    parse_plugin = ParsePluginWithNtcTemplates()
    res = parse_plugin.main(cmd, 'huawei_vrp')
    assert res[0]['vrp_version'] == '8.180'
    assert res[0].get('uptime')  # ntc_templates 是有uptime这个值的


def test_external_textfsm_parse(shared_datadir):
    """使用外部textfsm解析"""
    cmd = Cmd('display version')
    cmd.content = huawei_verison
    parse_plugin = ParsePluginWithNtcTemplates()
    parse_plugin.set_external_templates(shared_datadir / 'external_templates')
    res = parse_plugin.main(cmd, 'test_external')  # 使用的是外部模板
    assert res[0]['vrp_version'] == '8.180'
    assert not res[0].get('uptime')  # 确认外部模板是没有uptime这个值的


def test_external_and_ntc_textfsm_parse(shared_datadir):
    """当外部和ntc_templates同时都有相同模板的时候，会优先使用外部的"""
    cmd = Cmd('display version')
    cmd.content = huawei_verison
    parse_plugin = ParsePluginWithNtcTemplates()
    parse_plugin.set_external_templates(shared_datadir / 'external_templates')
    res = parse_plugin.main(cmd, 'huawei_vrp')  # 使用的是外部模板
    assert res[0]['vrp_version'] == '8.180'
    assert not res[0].get('uptime')  # 确认外部模板是没有uptime这个值的
