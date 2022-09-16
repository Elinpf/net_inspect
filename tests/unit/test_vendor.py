from net_inspect import vendor
from net_inspect.domain import Cmd


def test_check_vendor():
    """正常情况的检查设备"""
    cmd = Cmd('dis vers', 'Huawei Versatile Routing Platform')
    res = vendor.DefaultVendor.check_vendor({cmd.command: cmd})
    assert res.PLATFORM == vendor.Huawei.PLATFORM


def test_error_command_check_vendor():
    """非正常情况下，检查设备均会找不到"""
    cmds = [
        Cmd('dis verserr', 'Huawei Versatile Routing Platform'),  # 命令错误
        Cmd('dis ver', " % Ambiguous command found at '^' position."),  # 无效内容
        Cmd('dis ver', "\n  \n"),  # 无内容
    ]
    for cmd in cmds:
        res = vendor.DefaultVendor.check_vendor({cmd.command: cmd})
        assert res.PLATFORM == vendor.DefaultVendor.PLATFORM


def test_multi_commands_check_vendor():
    """多条命令混杂的情况下，检查设备"""
    cmds = [
        Cmd('dis verserr', 'Huawei Versatile Routing Platform'),
        Cmd('dis vers', 'Huawei Versatile Routing Platform'),  # 唯一正确的命令
        Cmd('dis version', " % Ambiguous command found at '^' position."),
        Cmd('dis versi', "\n  \n"),
    ]
    res = vendor.DefaultVendor.check_vendor({cmd.command: cmd for cmd in cmds})
    assert res.PLATFORM == vendor.Huawei.PLATFORM
