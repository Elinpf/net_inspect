from net_inspect.domain import Device, DeviceInfo


def cmd_dict():
    d = {'display version': """Huawei Versatile Routing Platform Software
VRP (R) software, Version 8.180 (NE20E V800R010C10SPC500)
Copyright (C) 2012-2018 Huawei Technologies Co., Ltd.
HUAWEI NE20E-S4 uptime is 493 days, 18 hours, 38 minutes 
Patch Version: V800R010SPH120

NE20E-S4 version information:
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
BKP  version information:
  PCB         Version : CX68BKP01B REV A
  MPU  Slot  Quantity : 2
  NSP  Slot  Quantity : 1
  CARD Slot  Quantity : 4"""}

    return d


class TestDevice:
    def test_device_save_to_cmds(self):
        """保存命令到设备"""
        device = Device()
        device.save_to_cmds(cmd_dict())
        assert len(device.cmds) == 1

    def test_device_check_vendor(self):
        """检查设备厂商"""
        device = Device()
        device.save_to_cmds(cmd_dict())
        device.check_vendor()
        assert device.vendor.__name__ == 'Huawei'

    def test_device_check_vendor_with_short_command(self):
        """当执行的命令为缩短命令时，也能检查出来"""
        device = Device()
        d = {'dis ver': cmd_dict()['display version']}
        device.save_to_cmds(d)
        device.check_vendor()
        assert device.vendor.__name__ == 'Huawei'


def test_device_info():
    devinfo = DeviceInfo(name='Router-A')
    assert devinfo.name == 'Router-A'
