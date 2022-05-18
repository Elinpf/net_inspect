from typing import Dict, Tuple

from ..domain import InputPluginAbstract, DeviceInfo


class InputPluginWithConsole(InputPluginAbstract):
    def run(self, file_path: str) -> Tuple[Dict[str, str], DeviceInfo]:
        ...
