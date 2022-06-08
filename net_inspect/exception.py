class Error(Exception):
    ...


class TemplateError(Error):
    ...


class PluginError(Error):
    ...


class NotPluginError(Error):
    ...


class AnalysisPluginError(Error):
    ...


class AnalysisLevelError(AnalysisPluginError):
    ...


class CommandNotFoundError(AnalysisPluginError):
    ...


class AnalysisTemplateError(AnalysisPluginError):
    ...


class AnalysisVendorNotSupport(AnalysisPluginError):
    ...
