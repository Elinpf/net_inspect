__version__ = '1.5.3'

import sys

from .api import NetInspect
from .base_info import EachVendorDeviceInfo, BaseInfo, AnalysisInfo
from .domain import (
    InputPluginAbstract,
    OutputPluginAbstract,
    ParsePluginAbstract,
    DeviceInfo,
    DeviceList,
    Device,
    Cmd,
    InputPluginResult,
)

__all__ = [
    "NetInspect",
    "EachVendorDeviceInfo",
    "BaseInfo",
    "AnalysisInfo",
    "InputPluginAbstract",
    "OutputPluginAbstract",
    "ParsePluginAbstract",
    "DeviceInfo",
    "DeviceList",
    "Device",
    "Cmd",
    "InputPluginResult",
]

if sys.version_info < (3, 7):
    print(f'NetInspect {__version__} requires Python 3.7+')
    sys.exit(1)


del sys
