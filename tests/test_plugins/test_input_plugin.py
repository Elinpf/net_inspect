import re


def test_input_plugin_with_console_simalr_huawei_reg():
    from net_inspect.plugins.input_plugin_with_console import simialr_huawei_reg

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
    from net_inspect.plugins.input_plugin_with_console import similar_cisco_reg

    test_list = [
        ('device>show version', 'device'),
        ('device(config)# sh version', 'device'),
        ('device-1(config-if)# sh version', 'device-1'),
    ]

    for (line, refer_hostname) in test_list:
        match = re.match(similar_cisco_reg, line)
        assert match.group('device_name') == refer_hostname
        assert re.match(r'\s*sh.*ver', match.group('cmd'))


def test_smartone_plugin_state_1(shared_datadir):
    """测试 smartone plugin 情况一"""
    from net_inspect.plugins.input_plugin_with_smartone import InputPluginWithSmartOne

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
    from net_inspect.plugins.input_plugin_with_smartone import InputPluginWithSmartOne

    input_plugin = InputPluginWithSmartOne()
    result = input_plugin.run(
        shared_datadir / 'B_FOO_BAR_AR01_21.1.1.1.diag')
    cmd_dict = result[0]
    device_info = result[1]
    assert device_info.name == 'B_FOO_BAR_AR01'
    assert device_info.ip == '21.1.1.1'
    assert len(cmd_dict) == 16
    assert len(cmd_dict['dis version'].split('\n')) > 6  # 判断是有内容的
