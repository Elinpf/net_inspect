import re
import sys

from .data import pyoption
from .logger import log


def reg_extend(reg: str) -> str:
    """扩展正则表达式写法，支持简单的逐字匹配
    e.g
    r'sh[[ow]] ver[[sion]]'
    将变成
    'sh(o(w)?)? ver(s(i(o(n)?)?)?)?'
    """
    def _completion(match):
        word = str(match.group())[2:-2]
        return '(' + ('(').join(word) + ')?' * len(word)

    return re.sub(r'(\[\[.+?\]\])', _completion, reg)


def get_command_from_textfsm(vendor_platform: str, template: str) -> str:
    """从模板文件名中获得命令
    :param vendor_platform: 平台名称
    :param template: 模板文件名

    :return: 命令

    >>> self.get_command('huawei_os', 'huawei_os_display_interface_status.textfsm')
    'display interface status'
    """

    template = template.replace(vendor_platform + '_', '')
    template = template.replace('.textfsm', '')
    return template.replace('_', ' ')


def pascal_case_to_snake_case(camel_case: str) -> str:
    """大驼峰（帕斯卡）转蛇形

    >>> pascal_case_to_snake_case('HuaweiVrpDisplayVersion')
    'huawei_vrp_display_version'
    """
    snake_case = re.sub(r"(?P<key>[A-Z])", r"_\g<key>", camel_case)
    return snake_case.lower().strip('_')


def snake_case_to_pascal_case(snake_case: str) -> str:
    """蛇形转大驼峰（帕斯卡）

    >>> snake_case_to_pascal_case('huawei_vrp_display_version')
    'HuaweiVrpDisplayVersion'
    """
    words = snake_case.split('_')
    return ''.join(word.title() for word in words)


def clamp_number(num: int, min_num: int, max_num: int) -> int:
    """
    将数字限制在指定范围内

    Args:
        num: 数字
        min_num: 最小值
        max_num: 最大值 

    Returns:
        int: 限制后的数字
    """
    return max(min(num, max_num), min_num)


def match(string: str, pattern: str) -> bool:
    """匹配字符串，区分大小写"""
    return bool(re.match(pattern, string))


def match_lower(string: str, pattern: str) -> bool:
    """匹配字符串，不区分大小写"""
    return bool(re.match(pattern, string.lower()))


def print_log(string: str, verbose: int = 0) -> None:
    """
    根据级别打印日志

    Args:
        string: 日志内容
        verbose: 日志级别

    `verbose`级别可以通过`verbose()`方法设置，总共0~3
    - 0: 日志关闭
    - 1: 提供Output模块的日志和Parse模块的日志
    - 2: 追加提供Analysis模块的日志
    - 3: 追加提供Parse模块不支持命令的信息日志和命令为无效的信息
    """
    verbose = clamp_number(verbose, 1, 3)
    if pyoption.verbose_level >= verbose:
        log.debug(string)


class SkipWithBlock(Exception):
    pass


class Singleton(object):
    """单例类继承"""
    _instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance


class NoneSkip(Singleton):
    """
    简单模仿None类，但是可以用来作为-with-中的跳过
    使用bool()来判断是否为空
    """

    def __init__(self):
        self.none = None

    def __enter__(self):
        if sys.gettrace():
            return self

        # NOTE 存在一定的问题，当程序处于调试状态的时候，调试进程会被破坏：
        # https://pydev.blogspot.com/2007/06/why-cant-pydev-debugger-work-with.html
        sys.settrace(lambda *args, **keys: None)
        frame = sys._getframe(1)
        frame.f_trace = self.trace

    def trace(self, frame, event, arg):
        raise SkipWithBlock()

    def __bool__(self):
        return False

    def __exit__(self, type, value, traceback):
        if type is None:
            return  # No exception
        if issubclass(type, SkipWithBlock):
            return True  # Suppress special SkipWithBlock exception

    def __eq__(self, other):
        return self.none == other

    def __ne__(self, other):
        return self.none != other

    def __getattr__(self, __name: str):
        # NOTE 当处于Debug状态的时候，调用不存在的属性时，就会触发这个，跳过-with-后面的内容
        raise SkipWithBlock()
