from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Type
import re

from .func import reg_extend

if TYPE_CHECKING:
    from .domain import Cmd


class DefaultVendor:
    """默认厂商"""

    PLATFORM = 'default'
    VERSION_COMMAND = None
    KEYWORD_REG = None

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


class H3C(DefaultVendor):

    PLATFORM = 'h3c_comware'
    VERSION_COMMAND = 'dis[[play]] ver[[sion]]'
    KEYWORD_REG = r'H3C Comware Platform Software'


class Cisco(DefaultVendor):

    PLATFORM = 'cisco_ios'
    VERSION_COMMAND = 'sh[[ow]] ver[[sion]]'
    KEYWORD_REG = r'Cisco IOS Software'
