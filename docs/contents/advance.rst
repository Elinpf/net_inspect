进阶教程
==========


自定义厂商
----------

目前 net_inspect 支持以下厂商的识别：

#. :class:`~net_inspect.vendor.Cisco` ``cisco_ios``
#. :class:`~net_inspect.vendor.Huawei` ``huawei_vrp``
#. :class:`~net_inspect.vendor.H3C` ``hp_comware``
#. :class:`~net_inspect.vendor.Maipu` ``maipu_mypower``
#. :class:`~net_inspect.vendor.Ruijie` ``ruijie_os``

但是在 `ntc-templates-elinpf <https://github.com/Elinpf/ntc-templates>`_ 中包含的的远远不止这5家厂商，
当有需要时，可以自定义厂商，只需要继承 :class:`~net_inspect.vendor.DefaultVendor` 类即可。

例如，我们需要识别一台 ``Juniper`` 的设备，我们可以这样做：

.. code-block:: python

    from net_inspect.vendor import DefaultVendor

    class Juniper(DefaultVendor):
        PLATFORM = 'juniper_junos'
        VERSION_COMMAND = 'sh[[ow]] ver[[sion]]'
        KEYWORD_REG = r'JUNOS'
        INVALID_STR = r'Invalid input detected at'


* ``PLATFORM`` 表示在 ``ntc-templates-elinpf`` 中的厂商名称前缀
* ``VERSION_COMMAND`` 表示获取设备版本的命令， ``[[`` 和 ``]]`` 包裹的内容是可以简写的，例如 ``sh ver`` 和 ``sh[[ow]] ver[[sion]]`` 是等价的
* ``KEYWORD_REG`` 表示设备厂商信息的关键字，可以使用正则匹配，匹配到关键字后识别为对应厂商设备
* ``INVALID_STR`` 表示命令回显是无效回显的关键字，必须命令错误时的回显等。

只需要这样定义一下， net_inspect 在执行的时候会自动识别出来。并将对应的 ``juniper_junos`` 模板调用执行解析。


自定义输入模块
--------------

由于各个网络管理平台平台或者自动化工具输出的日志格式不尽相同，
所以 net_inspect 提供了自定义输入模块的功能，可以自定义输入模块，实现自己的信息解析逻辑。

以一个网管平台的采集信息为例，采集的 ``日志文件名`` 格式如下:

.. code-block:: text

    <hostname>_<ip>_<date>.diag

例如:

.. code-block:: text

    A_FOO_BAR_DR01_127.0.0.1_20220221180010.diag


而采集的 ``日志内容`` 格式如下:

.. code-block:: text

    -------------------------dis clock-------------------------

    17:05:11 bj Mon 02/21/2022
    Time Zone : bj add 08:00:00



    -------------------------dis version-------------------------

    H3C Comware Platform Software
    Comware Software, Version 5.20, Release 2202
    Copyright (c) 2004-2010 Hangzhou H3C Tech. Co., Ltd. All rights reserved.
    H3C S5500-28C-EI uptime is 115 weeks, 1 day, 8 hours, 37 minutes

    H3C S5500-28C-EI with 1 Processor
    256M    bytes SDRAM
    32768K  bytes Flash Memory

    Hardware Version is REV.C
    CPLD Version is 002
    Bootrom Version is 609
    [SubSlot 0] 24GE+4SFP Hardware Version is REV.C

我们需要做的事情就是将 ``hostname``, ``ip(可选)``, ``每个执行命令`` 和 ``执行命令回显`` 提取出来交给 net_inspect 处理。

我们需要定义一个 ``InputPlugin`` 类，继承自 :class:`~net_inspect.domain.InputPluginAbstract` 类，实现 ``main`` 方法。

.. literalinclude:: /_static/custom_input_plugin_demo.py
   :encoding: utf-8
   :language: python

输出结果如下：

.. code-block:: text

    [+] B_FOO_BAR_DS02 H3C S5500-28C-EI clock: 2022-02-21 17:05:11

从上面的示例中，可以看到，实现了 ``InputPlugin`` 的 ``main`` 方法。
其中 :meth:`~net_inspect.domain.InputPluginAbstract.main` 方法的参数如下：

1. ``file_path`` 输入的单个日志文件名称
2. ``stream`` 输入的日志文件内容

返回指定的是一个 :class:`~net_inspect.domain.InputPluginResult` 类，需要做到:

1. 设置设备名称
2. 通过 :meth:`~net_inspect.domain.InputPluginResult.add_cmd` 方法添加每个执行的命令和返回的内容


最后将 ``InputPlugin`` 类注册到 net_inspect 中，即可使用。

.. code-block:: python

    net.set_input_plugin(CustomInputPlugin)


增加base_info条目
-----------------

在 :class:`~net_inspect.BaseInfo` 中，net_inspect 定义了一些基本的信息，比如 ``hostname``, ``ip``, ``cpu_usage`` 等等， 实现跨设备类型的统一调用。
但是有时候还需要增加一些自定义的字段，方便后续统一调用。


例如，我们需要增加一个 ``clock`` 字段，用于获取设备的时钟信息，我们可以这样做:

.. code-block:: python
    :emphasize-lines: 5,10,27

    from net_inspect import NetInspect, EachVendorDeviceInfo, BaseInfo, Device


    class AppendClock(BaseInfo):
        clock: str = ''  # 时钟信息


    class EachVendorWithClock(EachVendorDeviceInfo):

        base_info_class = AppendClock  # 设置base_info的类

        def do_huawei_vrp_baseinfo_2(self, device: Device, info: AppendClock):
            # 添加do_<vendor_platform>_baseinfo_<something>方法，可以自动运行
            for row in device.parse_result('display clock'):
                info.clock = f'{row["year"]}-{row["month"]}-{row["day"]} {row["time"]}'

        def do_hp_comware_baseinfo_2(self, device: Device, info: AppendClock):
            for row in device.parse_result('display clock'):
                info.clock = f'{row["year"]}-{row["month"]}-{row["day"]} {row["time"]}'

        # ... 可自行其他厂商的do_<vendor_platform>_baseinfo_<something>方法


    if __name__ == '__main__':
        net = NetInspect()
        net.set_plugins(input_plugin='console')
        net.set_base_info_handler(EachVendorWithClock)  # 设置获取设备基本信息的处理类
        net.run(input_path='logs')

        print('total devices:', len(net.cluster.devices))

        for device in net.cluster.devices:
            info = device.info  # type: AppendClock
            print(' | '.join([info.hostname, info.clock]))

执行的输出结果如下::

    total devices: 3
    Switch_A | 2021-03-19 10:23:08
    Switch_B | 2021-03-19 10:24:17
    Switch_C | 2021-03-19 10:32:17

可以看到，我们增加 ``huawei_vrp`` 和 ``hp_comware`` 平台的 ``clock`` 信息，使用 ``device.info.clock`` 进行统一调用。

.. note::
    
    没有实现 ``clock`` 的平台，将会以空字符串作为默认值。

增加分析条目
-------------

net_inspect 同样可以增加自定义的分析条目，会在 :meth:`~net_inspect.NetInspect.run_analysis` 执行的时候自动运行。

例如，我们需要增加一个检查OSPF邻居状态的分析模块

.. code-block:: python
    :emphasize-lines: 5,15-17

    from __future__ import annotations

    from typing import TYPE_CHECKING
    from net_inspect import NetInspect, vendor
    from net_inspect.analysis_plugin import analysis, AnalysisPluginAbc

    if TYPE_CHECKING:
        from net_inspect.analysis_plugin import TemplateInfo
        from net_inspect.domain import AnalysisResult


    class AnalysisPluginWithOSPFStatus(AnalysisPluginAbc):
        """OSPF status 状态不能为Init"""

        @analysis.vendor(vendor.Huawei)
        @analysis.template_key('huawei_vrp_display_ospf_peer_brief.textfsm', ['neighbor', 'state'])
        def huawei_vrp(template: TemplateInfo, result: AnalysisResult):
            """华为状态检查"""
            for row in template['display ospf peer brief']:
                if row['state'].lower() == 'init':
                    result.add_warning(f'{row["neighbor"]} is in init state')


    if __name__ == '__main__':
        net = NetInspect()
        net.set_plugins(input_plugin='console')
        net.run(input_path='logs')

        print('total devices:', len(net.cluster.devices))

        for device in net.cluster.devices:
            ospf_status = device.analysis_result.get('ospf status')
            warning_list = []
            for alarm in ospf_status:
                if alarm.is_warning:
                    warning_list.append(alarm.message)

            print(' | '.join([device.info.hostname, ', '.join(warning_list)]))


这样就得到了一个可重复利用的分析模块，后续在想要检查OSPF邻居状态的时候，只需要调用这个模块即可。

这里只添加了 ``huawei_vrp`` 这一个平台，其他平台增加方法同上。

编写这个需要注意：

#. ``@analysis.template_key`` 中第一个参数是 ``textfsm`` 文件名称， 第二个是其中将要用到的变量。
#. 类方法不需要self这个关键字。
#. 结果加入到result中即可，不需要返回值。
#. 整个过程不用单独设置，所有信息会直接写入analysis全局变量中。
#. 类注释和方法注释必须要写，因为会用到这个注释作为分析结果的标题。


自定义输出模块
---------------

对结果进行调用，可以直接以写脚本的方式，也可以自定义输出模块。

自定义输出模块的方式方便二次调用，比如写一个输出table的例子:

.. code-block:: python
    :emphasize-lines: 6,8,12

    from net_inspect import NetInspect, OutputPluginAbstract
    from rich.table import Table
    from rich.console import Console


    class Output(OutputPluginAbstract):
        def main(self):
            self.check_args('title')  # 检查是否提供title参数
            console = Console()

            table = Table(
                title=self.args.output_params.get('title'),
                show_lines=False
            )
            columns = ['hostname', 'ip', 'model', 'version', 'power status']
            for col in columns:
                table.add_column(col, justify='center')
            table.row_styles = ['green']

            for device in self.args.devices:
                info = device.info
                table.add_row(
                    info.hostname,
                    info.ip,
                    info.model,
                    info.version,
                    'Abnormal' if info.analysis.power else 'Normal'
                )

            console.print(table)

    if __name__ == '__main__':
        net = NetInspect()
        net.set_plugins(input_plugin='console', output_plugin=Output)
        cluster = net.run(input_path='log', output_plugin_params={
                        'title': '设备信息'})

输出结果：

.. image:: /_static/custom_output_plugin.png
    :align: center

可以看到，自定义了一个输出模块，可以直接调用，而不需要写脚本。

``output_plugin_params`` 中的所有参数都会传递到 :class:`~net_inspect.OutputPluginAbstract` 类中的 ``output_params`` 变量中，可以直接使用。

手动添加设备
------------

有时候我们需要手动添加设备，比如我们需要添加一个设备，
但是设备没有文件日志，我们可以手动添加，并且指定设备的厂家，这样就可以使用对应厂家的分析模块。

.. code-block:: python
    :emphasize-lines: 5-10

    from net_inspect import NetInspect, InputPluginResult, vendor

    net = NetInspect()

    d = InputPluginResult() # 创建一个InputPluginResult对象
    d.add_cmd('display clock', "2021-03-19 10:23:08+08:00") # 添加命令和结果
    d.hostname = 'Device' # 指定设备名称
    d.vendor = vendor.Huawei # 指定设备厂家平台

    net.add_device(d) # 添加设备到 NetInspect 中

    net.run()

    for device in net.cluster.devices:
        print(device.info.hostname)
        print(device.parse_result('dis clo'))

output::

    Device
    [{'time': '10:23:08', 'timezone': '', 'dayweek': '', 'year': '2021', 'month': '03', 'day': '19'}]

