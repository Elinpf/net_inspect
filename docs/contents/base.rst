基础教程
=========


NetInspect
-----------


通常情况下，需要构造一个 :class:`~net_inspect.NetInspect` 实例进行后续的操作，实例的方式如下::

    from net_inspect import NetInspect
    net = NetInspect()


设置插件
----------

插件是 net_inspect 的核心， ``input_plugin`` 和 ``output_plugin`` 需要通过 :meth:`~net_inspect.NetInspect.set_plugins` 方法设置插件。

而 ``analysis_plugin`` 不需要设置，net_inspect 会自动识别。

net_inspect 自带了部分插件，可以在命令行模式下用以下命令查看::

    net_inspect -l


.. note::

    ``input_plugins`` 中有个 ``InputPluginWithConsole`` 插件，其简写是 ``console`` 表示只要是从控制台输入的命令，都可以被这个插件处理。 
    :doc:`/others/console_input` 提供参考


要将输入插件设置为 ``console`` 可以这样做::

    net.set_plugins(input_plugin='console')

.. note::

    设置插件时，可以使用插件名称的简写字符串直接设置，也可以使用插件类设置。 ``Type[InputPluginAbstract] | str``


使用外部模板库
--------------

net_inspect 默认使用 `ntc-templates-elinpf <https://github.com/Elinpf/ntc-templates>`_, 虽然其中包含了大部分的设备模板，
但是有时候还是希望使用自己定义的模板库进行解析，这个时候需要做的工作如下：

#. 创建一个模板库文件夹，例如 ``local_templates``
#. 将模板文件放入 ``local_templates`` 文件夹中
#. 创建 ``index`` 文件
#. 在 :meth:`~net_inspect.NetInspect.set_external_templates` 方法中指定模板库文件夹路径

创建模板库文件夹
^^^^^^^^^^^^^^^^

模板库中的 ``textfsm`` 文件命名规则是 ``<vendor_platform>_<command>.textfsm``，例如 ``cisco_ios_show_version.textfsm``

``index`` 文件是一个字典文件，包含了模板库中模板的查找规则， 例如 ntc-templates-elinpf 中的 `index <https://github.com/Elinpf/ntc-templates/blob/master/ntc_templates/templates/index>`_ 文件。

index 文件编写 `规则 <https://github.com/Elinpf/ntc-templates#index-file>`_ 如下:

#. 文件开始必须包含 ``Template, Hostname, Platform, Command`` 字段
#. 按字母顺序排列操作系统
#. 按照模板名称长度排序（最长到最短）
#. 当长度相同时，使用字母顺序排列名称
#. 操作系统之间使用空行分隔

假设我们需要添加三个厂商的 ``clock`` 模板, 文件夹结构如下::

    ├── local_templates
    │   ├── huawei_vrp_display_clock.textfsm
    │   ├── hp_comware_display_clock.textfsm
    │   ├── cisco_ios_show_clock.textfsm
    │   ├── index

index 文件如下::

    Template, Hostname, Platform, Command

    huawei_vrp_display_clock.textfsm, .*, huawei_vrp, dis[[play]] clo[[ck]]

    hp_comware_display_clock.textfsm, .*, hp_comware, di[[splay]] clo[[ck]]

    cisco_ios_show_clock.textfsm, .*, cisco_ios, sh[[ow]] clo[[ck]]

设置模板库路径
^^^^^^^^^^^^^^

当创建好模板库，接下来只需要设置模板库路径即可, 
在 :meth:`~net_inspect.NetInspect.set_external_templates` 方法中指定模板库文件夹路径::

    net.set_external_templates('local_templates')

.. note::

    如果模板库中有重复的模板，会优先使用外部模板库中的模板

启用日志
--------

net_inspect 默认不会输出任何日志，如果需要启用控制台日志，可以使用 :meth:`~net_inspect.NetInspect.enable_console_log` 方法::

    net.enable_console_log(level='DEBUG')

或者想将日志保存在文件中，可以使用 :meth:`~net_inspect.NetInspect.enable_file_log` 方法::

    net.enable_file_log(file_path='net_inspect.log', level='DEBUG', rotation='5MB')

* ``file_path``: 日志文件路径
* ``level``: 日志级别
* ``rotation``: 日志文件大小，当日志文件大小超过 ``rotation`` 指定的大小时，会自动轮转日志文件

运行
-----

在设置完成后，就可以使用 :meth:`~net_inspect.NetInspect.run` 方法运行 net_inspect::

    net.run(input_path='logs')


此时 net_inspect 其实是依次执行了以下4个步骤:

#. :meth:`~net_inspect.NetInspect.run_input`
#. :meth:`~net_inspect.NetInspect.run_parse`
#. :meth:`~net_inspect.NetInspect.run_analysis`
#. :meth:`~net_inspect.NetInspect.run_output`

.. note::

    如果想单独执行某个步骤，可以使用 :meth:`~net_inspect.NetInspect.run_input` 、:meth:`~net_inspect.NetInspect.run_parse` 、:meth:`~net_inspect.NetInspect.run_analysis` 、:meth:`~net_inspect.NetInspect.run_output` 方法

.. note::

    如果没有指定 ``output_plugin`` 则会自动跳过 :meth:`~net_inspect.NetInspect.run_output` 步骤

执行完成后，设备的所有信息会保存在 :attr:`~net_inspect.NetInspect.cluster` 属性中, :attr:`~net_inspect.NetInspect.cluster` 表示设备集群，
是一个 :class:`~net_inspect.Cluster` 对象，可以通过 :attr:`~net_inspect.cluster.Cluster.devices` 属性获取设备列表::

    print(len(net.cluster.devices))

使用BaseInfo
--------------

net_inspect 会自动收集识别设备的基本信息，包括设备名称、设备厂商、设备类型、本版、IP、序列号信息、CPU利用率等等。

这些信息都存放在 :attr:`~net_inspect.Device.info` 中，是 :class:`~net_inspect.BaseInfo` 的实例::

    for device in net.cluster.devices:
        print(device.info)

其中一台的输出信息如下::

    BaseInfo(
        hostname='Switch_C',
        file_path='logs\\Switch_C.log',
        vendor='H3C',
        vendor_platform='hp_comware',
        model='S9508E-V',
        version='5.20 Release: 1238P08',
        uptime='255 weeks, 5 days, 8 hours, 20 minutes',
        ip='24.45.254.254',
        sn=[
            ('LSR2GP24LEB1', '210xxxxxxxxxxxx00041'),
            ('LSR2GT48LEB1', '210xxxxxxxxxxxx00038'),
            ('LSR1SRP2B1', '21023xxxxxxxxxxxx039'),
            ('LSR1SRP2B1', '21023xxxxxxxxxxxx009')
        ],
        cpu_usage='1%',
        memory_usage='20%',
        analysis=AnalysisInfo(cpu=False, memory=False, fan=False, power=None)
    )

例如想获取设备的版本信息，可以使用 :attr:`~net_inspect.BaseInfo.version` 属性::

        print(device.info.version)

里面还包含了 :class:`~net_inspect.AnalysisInfo` 对象，用于标记设备的CPU、内存、风扇、电源是否正常::

    print(device.info.analysis)

输出如下::

    AnalysisInfo(cpu=False, memory=False, fan=False, power=None)

每个属性的意思是是否异常，如果为 ``True`` 表示异常，如果为 ``False`` 表示正常，如果为 ``None`` 表示未知。


搜索设备
------------

通过 **名称** 搜索设备，可以使用 :meth:`~net_inspect.NetInspect.search` 方法，返回的是符合设备名称的 :class:`~net_inspect.Device` 集合 ``List[Device]`` ::

    for device in net.search('Switch_C'):
        print(device.info.hostname)


获取解析结果
-------------

在 :class:`~net_inspect.Device` 中有个 :meth:`~net_inspect.Device.parse_result` 方法，
获取设备对命令的解析结果::

    for row in device.parse_result('show ip int bri'):
        print(row)

返回类型是 ``List[dict]`` , 输出部分结果如下::

    {'interface': 'LoopBack0', 'ip': '24.44.1.248', 'mask': '32', 'physical': 'up', 'protocol': 'up(s)'}
    {'interface': 'NULL0', 'ip': 'unassigned', 'mask': '', 'physical': 'up', 'protocol': 'up(s)'}
    {'interface': 'Vlanif100', 'ip': '11.22.237.25', 'mask': '30', 'physical': 'up', 'protocol': 'up'}
    {'interface': 'Vlanif101', 'ip': '11.22.237.130', 'mask': '28', 'physical': 'up', 'protocol': 'up'}
    {'interface': 'Vlanif102', 'ip': '11.22.237.146', 'mask': '28', 'physical': 'up', 'protocol': 'up'}
    {'interface': 'Vlanif103', 'ip': '11.22.236.74', 'mask': '29', 'physical': 'up', 'protocol': 'up'}
    {'interface': 'XGigabitEthernet1/0/0', 'ip': '11.22.1.6', 'mask': '30', 'physical': 'up', 'protocol': 'up'}
    {'interface': 'XGigabitEthernet1/0/1', 'ip': '11.22.1.65', 'mask': '30', 'physical': 'up', 'protocol': 'up'}

可以看到，是对设备的 ``show ip int bri`` 命令的解析，这个命令的全称是 ``show ip interface brief``,
:meth:`~net_inspect.Device.parse_result` 方法会自动对命令进行模糊识别， 使用 **简写** 也可以准确识别到命令，
解析出来的内容为 `ntc-templates-elinpf <https://github.com/Elinpf/ntc-templates>`_ 中模板的解析结果。
例如这个案例中，由于设备厂商是 ``Huawei``, 所以对应的模板是
`huawei_vrp_show_ip_interface_brief.textfsm <https://github.com/Elinpf/ntc-templates/blob/master/ntc_templates/templates/huawei_vrp_display_ip_interface_brief.textfsm>`_ ，

如果我们想只将接口状态提取出来， 可以这么做

.. code-block:: python
    :emphasize-lines: 8-14

    from net_inspect import NetInspect

    net = NetInspect()

    net.set_input_plugin('console')
    net.run('logs')

    for device in net.cluster.devices:
        for row in device.parse_result('dis ip int bri'):
            print(
                'device: `{}` interface: `{}` status is `{}`'.format(
                    device.info.hostname, row['interface'], row['protocol']
                )
            )


部分输出结果如下::

    device: `Switch_A` interface: `Ethernet0/0/0` status is `down`
    device: `Switch_A` interface: `LoopBack0` status is `up(s)`
    device: `Switch_A` interface: `NULL0` status is `up(s)`
    device: `Switch_A` interface: `Vlanif100` status is `up`
    device: `Switch_A` interface: `Vlanif101` status is `up`
    device: `Switch_A` interface: `Vlanif102` status is `up`
    device: `Switch_A` interface: `Vlanif103` status is `up`
    device: `Switch_A` interface: `XGigabitEthernet1/0/0` status is `up`
    device: `Switch_A` interface: `XGigabitEthernet1/0/1` status is `up`
    device: `Switch_A` interface: `XGigabitEthernet1/0/2` status is `up`

获取执行命令内容
-----------------

当需要获取设备执行命令的内容(content)时，可以使用 :meth:`~net_inspect.Device.search_cmd` 方法::

    with device.search_cmd('show version') as cmd:
        print(cmd.content)

.. note::

    :meth:`~net_inspect.Device.search_cmd` 方法返回的是一个上下文管理器，返回 :class:`~net_inspect.Cmd` 类

.. note::

    :meth:`~net_inspect.Device.search_cmd` 方法所需要的参数可以是命令的简写，支持模糊查询
    

获取分析结果
------------

net_inspect 有 ``analysis_plugin`` 模块，可以做一定程度的设备运行情况分析，比如设备的内存使用率，CPU使用率是否在正常范围，
电源和风扇是否处于正常状态等。

.. note::

    使用命令行命令 ``net_inspect -l`` 查看当前支持的分析插件

    使用命令行命令 ``net_inspect -L`` 查看分析插件支持的厂商平台

可以通过 :attr:`~net_inspect.Device.analysis_result` 属性获取分析结果, 是 :class:`~net_inspect.domain.AnalysisResult` 的实例，
此时的 ``analysis_result`` 是包含了所有分析插件的结果，如果只想获取某个分析插件的结果，可以使用
使用 :meth:`~net_inspect.domain.AnalysisResult.get` 方法可以获取单独插件的 ``analysis_result``::

    # 获取所有分析插件的结果
    for alarm in device.analysis_result:
        print(alarm.message)

    # or 获取单独插件的结果
    cpu_status = device.analysis_result.get('cpu_status')
    for alarm in cpu_status:
        if alarm.above_focus: # 只获取关注级别以上的告警
            print(alarm.message)

    
    

