import os
from . import __file__ as module_file


class PyStr:
    def __init__(self):
        self.software = 'net_inspect'
        self.logger_format = "%(message)s"
        # self.logger_format = "%(asctime)-15s - %(levelname)s - %(message)s"


class PyOption:
    def __init__(self):
        self.log_file_expend = ['.txt', '.log', '.diag']


class PyPath:
    def __init__(self):
        self.root_path = os.path.dirname(module_file)
        self.templates_dir_path = os.path.join(self.root_path, 'templates')


pystr = PyStr()
pyoption = PyOption()
pypath = PyPath()
