from typer.testing import CliRunner
from net_inspect.cli import app
from shlex import split

runner = CliRunner()


def test_base_info_list():
    """检查基础信息列表，只要其中包含了sn的信息就算通过"""
    result = runner.invoke(app, split("--base-info-list"))
    assert result.exit_code == 0
    assert 'List[Tuple[str, str]]' in result.stdout


def test_plugin_list():
    """检查插件列表，只要每个类别的插件包含一个就算通过"""
    result = runner.invoke(app, split("--plugin-list"))
    assert result.exit_code == 0
    assert 'console' in result.stdout
    assert 'device_list' in result.stdout
    assert 'ntc_templates' in result.stdout
    assert 'cpu_status' in result.stdout


def test_analysis_plugin_list():
    """检查分析插件列表，只要其中包含了cisco_ios的信息就算通过"""
    result = runner.invoke(app, split("--analysis-list"))
    assert result.exit_code == 0
    assert 'cisco_ios' in result.stdout


def test_input(shared_datadir):
    """运行主程序，检查output中是否包含了主机信息"""
    path = str(shared_datadir).replace('\\', '\\\\')
    result = runner.invoke(app, split(f'--input {path} --output-plugin device_list'))

    assert result.exit_code == 0
    assert 'total devices: 6' in result.stdout


def test_verbose_v(shared_datadir):
    """运行主程序，检查是否包含了INFO信息"""
    path = str(shared_datadir).replace('\\', '\\\\')
    result = runner.invoke(app, split(f'--input {path} --output-plugin device_list -v'))

    assert result.exit_code == 0
    assert 'INFO' in result.stdout
    assert 'DEBUG' not in result.stdout


def test_verbose_vv(shared_datadir):
    """运行主程序，检查是否包含了DEBUG信息"""
    path = str(shared_datadir).replace('\\', '\\\\')
    result = runner.invoke(
        app, split(f'--input {path} --output-plugin device_list -vv')
    )

    assert result.exit_code == 0
    assert 'DEBUG' in result.stdout


def test_textfsm_values():
    """测试 textfsm 参数"""
    result = runner.invoke(app, split("textfsm -p huawei_vrp -c 'dis ver'"))
    assert result.exit_code == 0
    assert 'huawei_vrp_display_version.textfsm' in result.stdout
    assert 'vrp_version' in result.stdout


def test_textfsm_not_command():
    """测试 textfsm 参数没找到可用命令的情况"""
    result = runner.invoke(app, split("textfsm -p huawei_vrp -c 'not command'"))
    assert result.exit_code == 0
    assert '模板仓库中没有找到此命令' in result.stdout


def test_textfsm_not_platform():
    """测试 textfsm 参数没找支持厂商平台的情况"""
    result = runner.invoke(app, split("textfsm -p no_platform -c 'not command'"))
    assert result.exit_code == 0
    assert '模板仓库不支持此平台' in result.stdout


def test_textfsm_external_template(shared_datadir):
    """测试 textfsm 参数使用外部模板"""
    path = str(shared_datadir / 'external_templates').replace('\\', '\\\\')
    result = runner.invoke(app, split(f"textfsm -p huawei_vrp -c 'dis ver' -e {path}"))
    assert result.exit_code == 0
    assert 'uptime' not in result.stdout


def test_textfsm_external_template_2(shared_datadir):
    """测试 textfsm 参数使用外部模板的新增平台"""
    path = str(shared_datadir / 'external_templates').replace('\\', '\\\\')
    result = runner.invoke(
        app, split(f"textfsm -p test_external -c 'dis ver' -e {path}")
    )
    assert result.exit_code == 0
    assert 'model' in result.stdout
