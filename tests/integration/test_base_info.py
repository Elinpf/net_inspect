from http.client import UNSUPPORTED_MEDIA_TYPE
from net_inspect import NetInspect
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class BaseInfoExpect:
    """期望值"""
    hostname: str
    vendor: str
    vendor_platform: str
    model: str
    version: str
    uptime: str
    ip: str
    sn: List[Tuple[str, str]]
    cpu_usage: str
    memory_usage: str

    def __getitem__(self, item: str):
        return self.__getattribute__(item)


def check_base_info(file_path: str, expected: BaseInfoExpect):
    net = NetInspect()
    net.set_input_plugin('console')
    net.run_input(file_path)
    net.run_parse()
    device = net.cluster.devices[0]
    info = device.info

    for key in expected.__annotations__.keys():
        assert info[key] == expected[key]


def test_run_cisco_ios_base_info(shared_datadir):
    file_path = (shared_datadir / 'base_info_logs' / 'cisco_ios.txt')

    expected = BaseInfoExpect(
        hostname='AA_BB_SW1',
        vendor='Cisco',
        vendor_platform='cisco_ios',
        model='WS-C2960-48TC-L',
        version='12.2(55)SE7',
        uptime='7 weeks, 6 days, 2 hours, 39 minutes',
        ip='10.0.1.2',
        sn=[('1', 'FCQ1XXXX58D'), ('GigabitEthernet0/1', 'FNSXXXX1LVU'),
            ('GigabitEthernet0/2', 'FNSXXXX2FBJ')],
        cpu_usage='23%',
        memory_usage='68%',
    )

    check_base_info(file_path, expected)


def test_run_huawei_vrp_base_info(shared_datadir):
    file_path = (shared_datadir / 'base_info_logs' / 'huawei_vrp.txt')

    expected = BaseInfoExpect(
        hostname='Huawei_AA',
        vendor='Huawei',
        vendor_platform='huawei_vrp',
        model='S7706 Terabit Routing Switch',
        version='5.170',
        uptime='19 weeks, 5 days, 5 hours, 27 minutes',
        ip='11.22.255.238',
        sn=[('', '2102XXXXXXXXXXXX0288'), ('', '031XXXXXXXXX0235'),
            ('', '031XXXXXXXXX0289'), ('', '031XXXXXXXXXX274')],
        cpu_usage='7%',
        memory_usage='13%',
    )

    check_base_info(file_path, expected)


def test_run_hp_comware_base_info(shared_datadir):
    file_path = (shared_datadir / 'base_info_logs' / 'hp_comware.txt')

    expected = BaseInfoExpect(
        hostname='H3C_AA',
        vendor='H3C',
        vendor_platform='hp_comware',
        model='MSR30-40',
        version='5.20 Release: 2511,',
        uptime='367 weeks, 5 days, 5 hours, 18 minutes',
        ip='11.77.0.3',
        sn=[('30-40', '210235A19EB13A000042')],
        cpu_usage='5%',
        memory_usage='30%',
    )

    check_base_info(file_path, expected)


def test_run_hp_comware_2_base_info(shared_datadir):
    """display memory 第二种情况"""
    file_path = (shared_datadir / 'base_info_logs' / 'hp_comware_2.txt')

    expected = BaseInfoExpect(
        hostname='H3C_AA',
        vendor='H3C',
        vendor_platform='hp_comware',
        model='MSR30-40',
        version='5.20 Release: 2511,',
        uptime='367 weeks, 5 days, 5 hours, 18 minutes',
        ip='11.77.0.3',
        sn=[('30-40', '210235A19EB13A000042')],
        cpu_usage='5%',
        memory_usage='54.0%',
    )

    check_base_info(file_path, expected)


def test_run_maipu_mypower_base_info(shared_datadir):
    file_path = (shared_datadir / 'base_info_logs' / 'maipu_mypower.txt')

    expected = BaseInfoExpect(
        hostname='MAIPU_AA',
        vendor='Maipu',
        vendor_platform='maipu_mypower',
        model='MP3840',
        version='6.3.17(integrity)',
        uptime='345 weeks 4 days',
        ip='11.77.243.21',
        sn=[('MPU_RM3B_206_4GE', '591XXXXXXXXXXX49'), ('LPU_RM3B_4GET4GEFH',
                                                       '123XXXXXXXXXXX29'), ('SJJ1109-B', '253XXXXXXXXXXX08')],
        cpu_usage='9%',
        memory_usage='12.80%',
    )

    check_base_info(file_path, expected)


def test_run_ruijie_os_base_info(shared_datadir):
    file_path = (shared_datadir / 'base_info_logs' / 'ruijie_os.txt')

    expected = BaseInfoExpect(
        hostname='RUIJIE_AA',
        vendor='Ruijie',
        vendor_platform='ruijie_os',
        model='S8607E',
        version='S8600E_RGOS 11.0(4)B8',
        uptime='313:22:34:30',
        ip='11.89.0.1',
        sn=[('', 'G1XXXXXXXX020')],
        cpu_usage='13.0%',
        memory_usage='55.6%',
    )

    check_base_info(file_path, expected)
