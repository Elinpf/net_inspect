from net_inspect import NetInspect


def test_output_plugin_with_excel_report(shared_datadir, tmp_path):
    """测试输出插件excel报告"""

    input_dir = shared_datadir / 'log_files'
    out_file = tmp_path / 'output.xlsx'
    net = NetInspect()
    net.set_plugins(input_plugin='smartone', output_plugin='excel_report')

    net.run(input_path=input_dir, output_file_path=out_file)
