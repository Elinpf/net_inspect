from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Type
import re

from .func import reg_extend

if TYPE_CHECKING:
    from .domain import Cmd


class DefaultVendor:
    """默认厂商"""

    PLATFORM = 'default'
    VERSION_COMMAND = None  # 确定厂商信息的命令
    KEYWORD_REG = None  # 用于匹配厂商的关键字正则表达式
    INVALID_STR = None  # 如果命令返回的结果中包含该字符串, 则认为命令无效

    @classmethod
    def check_vendor(cls, cmds: Dict[str, Cmd]) -> Type[DefaultVendor]:
        """检查确认设备的厂商"""
        for handler in cls.__subclasses__():
            if handler._check_vendor(cmds):
                return handler

        return cls

    @classmethod
    def _check_vendor(cls, cmds: Dict[str, Cmd]) -> bool:
        """子类用于检查设备的厂商以及平台"""
        version_cmd = cls._check_version_command(cmds)
        if version_cmd:
            return (True if
                    re.search(cls.KEYWORD_REG,
                              cmds[version_cmd].content, re.IGNORECASE)
                    else False)

        return False

    @classmethod
    def _check_version_command(cls, cmds: Dict[str, Cmd]) -> str:
        """子类用于检查版本命令"""
        cmds_str = '|'.join(cmds.keys())
        match = re.search(re.compile('('+reg_extend(cls.VERSION_COMMAND)+')', re.IGNORECASE),
                          cmds_str)
        if match:
            return match.group()
        return ''


class Huawei(DefaultVendor):

    PLATFORM = 'huawei_vrp'
    VERSION_COMMAND = 'dis[[play]] ver[[sion]]'
    KEYWORD_REG = r'Huawei Versatile Routing Platform'
    INVALID_STR = r'Error:.*found at'


class H3C(DefaultVendor):

    PLATFORM = 'hp_comware'  # 新华三在海外用的是 HP Comware
    VERSION_COMMAND = 'dis[[play]] ver[[sion]]'
    KEYWORD_REG = r'H3C Comware Platform Software|H3C Comware Software'
    INVALID_STR = r'Ambiguous command found at'


class Cisco(DefaultVendor):

    PLATFORM = 'cisco_ios'
    VERSION_COMMAND = 'sh[[ow]] ver[[sion]]'
    KEYWORD_REG = r'Cisco IOS Software'
    INVALID_STR = r'Invalid input detected'


class Maipu(DefaultVendor):

    PLATFORM = 'maipu_mypower'
    VERSION_COMMAND = 'sh[[ow]] ver[[sion]]'
    KEYWORD_REG = r'MyPower \(R\) Operating System Software'
    INVALID_STR = r'Invalid input detected at'


class Ruijie(DefaultVendor):

    PLATFORM = 'ruijie_os'
    VERSION_COMMAND = 'sh[[ow]] ver[[sion]]'
    KEYWORD_REG = r'Ruijie Networks'
    INVALID_STR = r'Invalid input detected at'
