from net_inspect.plugins import autoload_plugin
from net_inspect.domain import InputPluginAbstract


def test_autoload_plugin():
    autoload_plugin()
    input_plugns = InputPluginAbstract.__subclasses__()
    assert len(input_plugns) >= 2
