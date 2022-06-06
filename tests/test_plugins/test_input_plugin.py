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
