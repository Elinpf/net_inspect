import re

from .logger import log
from .data import pyoption


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
        level: 日志级别
    """
    verbose = clamp_number(verbose, 1, 3)
    if pyoption.verbose_level >= verbose:
        log.debug(string)
