class Error(Exception):
    ...


# FIXME 在这里应该做出分级，用在parse_plugin中的
class Continue(Exception):
    """用于控制循环"""


class TemplateError(Error):
    """ntc-template 错误"""


# FIXME 未使用
class PluginError(Error):
    """插件类错误的基类"""


# FIXME 未使用
class PluginNotSpecify(PluginError):
    """未指定插件"""


class InputPluginError(PluginError):
    """输入插件错误的基类"""


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
