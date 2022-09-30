class Error(Exception):
    ...


class PluginError(Error):
    """插件类错误的基类"""


class TemplateError(PluginError):
    """ntc-template 错误"""


class TemplateNotSupperThisPlatform(TemplateError):
    """ntc-template 不支持该平台"""

    def __init__(self, platform: str):
        self.platform = platform

    def __str__(self):
        return f'platform:{self.platform!r} 暂不支持该平台的解析.'


class TemplateNotSupperThisCommand(TemplateError):
    """ntc-template 不支持该命令的解析"""

    def __init__(self, platform: str, command: str):
        self.platform = platform
        self.command = command

    def __str__(self):
        return f'platform:{self.platform!r} command:{self.command!r} 暂无该平台的textfsm模板文件.'


class NotParseAnyResult(TemplateError):
    """没有解析到结果"""

    def __init__(self, platform: str, command: str):
        self.platform = platform
        self.command = command

    def __str__(self):
        return f'platform:{self.platform!r} cmd:{self.command!r} 未能解析出任何内容, 请检查textfsm模板, 联系仓库维护者或者自定义模板文件.'


class PluginNotSpecify(PluginError):
    """未指定插件"""


class InputPluginError(PluginError):
    """输入插件错误的基类"""


# FIXME 不存在
class NotFoundDevice(InputPluginError):
    """Input Plugin 中未找到设备"""


class AnalysisPluginError(PluginError):
    """解析插件错误基类"""


class AnalysisLevelError(AnalysisPluginError):
    """分析级别错误"""


# FIXME 不存在
class AnalysisTemplateNameError(AnalysisPluginError):
    """模板的名称不存在"""


# FIXME 不存在
class AnalysisVendorNotSupport(AnalysisPluginError):
    """分析模块暂不支持该厂商"""


class NtcTemplateNotDefined(AnalysisPluginError):
    """模板名称不存在"""


class OutputPluginError(PluginError):
    """输出插件错误基类"""


class OutputParamsNotGiven(OutputPluginError):
    """没有向输出插件提供相应的参数"""

    def __init__(self, plugin_name: str, key: str):
        self.plugin_name = plugin_name
        self.key = key

    def __str__(self):
        return f'没有向输出插件 {self.plugin_name!r} 提供 {self.key!r} 参数'
