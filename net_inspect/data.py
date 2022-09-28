import os
from . import __file__ as module_file


class PyStr:
    def __init__(self):
        self.software = 'net_inspect'
        self.default_parse_plugin = 'ntc_templates'
        self.parse_plugin_prefix = 'parse --'
        self.analysis_plugin_prefix = 'analysis --'


class PyOption:
    def __init__(self):
        self.input_file_expend = ['.txt', '.log', '.diag']

        self.console_log_level = 'INFO'
        self.console_format = "{time:HH:mm:ss} | <level>{level}</level> | {message}"

        self.logfile_format = (
            "{time:YYYY-MM-DD HH:mm:ss} [<level>{level}</level>] | {name}: {message}"
        )
        self.logfile_name = 'net_inspect.log'
        self.logfile_rotation = '2 MB'


class PyPath:
    def __init__(self):
        self.root_path = os.path.dirname(module_file)
        self.project_path = os.path.dirname(self.root_path)


pystr = PyStr()
pyoption = PyOption()
pypath = PyPath()
