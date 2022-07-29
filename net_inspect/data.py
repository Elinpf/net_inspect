import os
from . import __file__ as module_file


class PyStr:
    def __init__(self):
        self.software = 'net_inspect'
        self.logger_format = "%(message)s"
        # self.logger_format = "%(asctime)-15s - %(levelname)s - %(message)s"
        self.default_parse_plugin = 'ntc_templates'
        self.analysis_warning_prefix = 'AnalysisWarning --'
        self.parse_waning_prefix = 'ParseWarning --'


class PyOption:
    def __init__(self):
        self.log_file_expend = ['.txt', '.log', '.diag']
        self.log_level = 'INFO'
        self.verbose_level = 0


class PyPath:
    def __init__(self):
        self.root_path = os.path.dirname(module_file)
        self.project_path = os.path.dirname(self.root_path)


pystr = PyStr()
pyoption = PyOption()
pypath = PyPath()
