from net_inspect import __version__
import os.path as p


def test_version():
    ver = '1.3.0'

    assert __version__ == ver
    setup_file = p.join(p.dirname(p.dirname(__file__)), 'pyproject.toml')
    with open(setup_file, 'r', encoding='utf8') as f:
        content = f.read()
        assert f'version = "{ver}"' in content
