# -*- coding: utf-8 -*-
# author:liucong

import os, inspect
import sys
import threading
import queue

import requests

from core import RunTestCase
from tools import Config
from airtest.core.api import *
from airtest.core.error import *
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
from airtest.core.android.adb import ADB
import subprocess
from airtest.utils.apkparser import APK

from tools.log import logger

_print = print


def print(*args, **kwargs):
    _print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), *args, **kwargs)


adb = ADB().adb_path
# adb_str = ADB().adb_path
# if adb_str.count(' ') != 0:
#     adb = '\"' + adb_str + '\"'

# 同文件内用queue进行线程通信
q = queue.Queue()

'''
MultiAdb类封装了所有与设备有关的方法。
大部分方法都单独写了注释。

'''


class MultiAdb:

    def __init__(self, mdevice=""):
        # 获取当前文件的上层路径
        self._parentPath = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())) + os.path.sep + ".")
        # 获取当前项目的根路径
        self._rootPath = os.path.abspath(os.path.dirname(self._parentPath) + os.path.sep + ".")
        self._configPath = self._rootPath + "\config.ini"
        # 获取项目名称
        self._pro_name = Config.getProName(self._configPath, "pro_name")
        # 获取项目配置
        self._jenkins_url = Config.getProConfig(self._configPath, 'jenkins_url', self._pro_name)[0]
        self._devicesList = Config.getProConfig(self._configPath, "deviceslist", self._pro_name)
        self._packagePath = Config.getProConfig(self._configPath, "apkpath", self._pro_name)[0]
        self._packageName = Config.getProConfig(self._configPath, "packname", self._pro_name)[0]
        self._activityName = Config.getProConfig(self._configPath, "activityname", self._pro_name)[0]
        # 获取基本配置
        self._skip_pushapk2devices = Config.getBasicConfig(self._configPath, "skip_pushapk2devices")
        self._auto_delete_package = Config.getBasicConfig(self._configPath, "auto_delete_package")
        self._auto_install_package = Config.getBasicConfig(self._configPath, "auto_install_package")
        self._skip_check_of_install = Config.getBasicConfig(self._configPath, "skip_check_of_install")
        self._skip_check_of_startapp = Config.getBasicConfig(self._configPath, "skip_check_of_startapp")
        self._skip_generate_report = Config.getBasicConfig(self._configPath, "skip_generate_report")
        self._skip_email = Config.getBasicConfig(self._configPath, "skip_email")
        self._skip_performance = Config.getBasicConfig(self._configPath, "skip_performance")
        self._storage_by_excel = Config.getBasicConfig(self._configPath, "storage_by_excel")
        self._startTime = time.time()
        self._timeout_of_per_action = int(Config.getBasicConfig(self._configPath, "timeout_of_per_action"))
        self._timeout_of_startapp = int(Config.getBasicConfig(self._configPath, "timeout_of_startapp"))
        self._mdevice = mdevice
        # 处理模拟器端口用的冒号
        if ":" in self._mdevice:
            self._nickName = self._mdevice.split(":")[1]
        else:
            self._nickName = self._mdevice
        self._iteration = int(Config.getBasicConfig(self._configPath, "iteration"))
        self._allTestcase = Config.getProConfig(self._configPath, "testcase", self._pro_name)
        try:
            self._testcaseForSelfDevice = Config.getTestCase(self._configPath, self._pro_name, self._nickName)
            if self._testcaseForSelfDevice[0] == "":
                self._testcaseForSelfDevice = self._allTestcase
        except Exception:
            self._testcaseForSelfDevice = self._allTestcase
        self._testCasePath = Config.getProConfig(self._configPath, "testcasepath", self._pro_name)
        if self._testCasePath[0] == "":
            self._testCasePath = os.path.join(self._rootPath, "TestCase")

        if self._activityName == "":
            if self._skip_check_of_install == 0:
                self._activityName = APK(self.get_apkpath()).activities[0]

    # 获取设备列表
    def get_devicesList(self):
        return self._devicesList

    # 获取apk的本地路径
    def get_apkpath(self):
        return self._packagePath

    # 获取包名
    def get_packagename(self):
        return self._packageName

    # 获取Activity类名
    def get_activityname(self):
        return self._activityName

    # 获取是否跳过安装apk步骤的flag
    def get_skip_pushapk2devices(self):
        return self._skip_pushapk2devices

    # 获取是否需要在安装应用时点击二次确认框的flag
    def get_skip_check_of_install(self):
        return self._skip_check_of_install

    # 获取是否需要在打开应用时点击二次确认框的flag
    def get_skip_check_of_startapp(self):
        return self._skip_check_of_startapp

    # 获取当前设备id
    def get_mdevice(self):
        return self._mdevice

    # 获取当前设备id的昵称，主要是为了防范模拟器和远程设备带来的冒号问题。windows的文件命名规范里不允许有冒号。
    def get_nickname(self):
        return self._nickName

    # 获取启动app的延时时间
    def get_timeout_of_startapp(self):
        return self._timeout_of_startapp

    # 获取每步操作的延时时间
    def get_timeout_of_per_action(self):
        return self._timeout_of_per_action

    # 获取运行循环点击处理脚本的循环次数
    def get_iteration(self):
        return self._iteration

    # 获取所有的用例名称列表
    def get_alltestcase(self):
        return self._allTestcase

    # def get_androidbrand(self):
    # command=adb+" -s {} shell getprop ro.product.brand".format(self.get_mdevice())
    # brand=os.popen(command).read()
    # return self._androidbrand

    # 获取针对特定设备的用例列表
    def get_testcaseforselfdevice(self):
        return self._testcaseForSelfDevice

    # 获取测试用例路径，不填是默认根目录TestCase
    def get_TestCasePath(self):
        return self._testCasePath

    # 获取项目的根目录绝对路径
    def get_rootPath(self):
        return self._rootPath

    # 获取是否要自动删除包的开关
    def auto_delete_package(self):
        return self._auto_delete_package

    def auto_install_package(self):
        return self._auto_install_package

    # 获取是否需要性能测试的开关
    def get_skip_performance(self):
        return self._skip_performance

    # 获取是否需要用excel来存储性能数据
    def get_storage_by_excel(self):
        return self._storage_by_excel

    # 修改当前设备的方法
    def set_mdevice(self, device):
        self._mdevice = device

    # 获取是否需要生成测试报告
    def get_skip_report(self):
        return self._skip_generate_report

    # 获取是否需要发送邮件
    def get_skip_email(self):
        return self._skip_email

    # 获取项目对应的jenkins地址
    def get_jenkins_url(self):
        return self._jenkins_url

    # 写回包名、包路径、测试用例路径等等到配置文件

    def set_packagename(self, packagename):
        configPath = self._configPath
        Config.setValue(configPath, "packname", packagename)

    def set_packagepath(self, packagepath):
        configPath = self._configPath
        Config.setValue(configPath, "apkpath", packagepath)

    def set_TestCasePath(self, TestCasepath):
        configPath = self._configPath
        Config.setValue(configPath, "testcasepath", TestCasepath)

    # 本方法用于读取实时的设备连接
    def getdevices(self):
        deviceslist = []
        for devices in os.popen(adb + " devices"):
            if "\t" in devices:
                if devices.find("emulator") < 0:
                    if devices.split("\t")[1] == "device\n":
                        devices = devices.split("\t")[0]
                        deviceslist.append(devices)
                        logger.info("设备{}被添加到deviceslist中".format(devices))
        return deviceslist

    # 启动APP的方法，核心是airtest的start_app函数，后面的一大堆if else 是用来根据设备进行点击操作的。需要用户自行完成。
    def StartApp(self):
        devices = self.get_mdevice()
        skip_check_of_startapp = self.get_skip_check_of_startapp()
        skip_check_of_startapp = True if skip_check_of_startapp == "1" else False
        logger.info("{}进入StartAPP函数".format(devices))
        start_app(self.get_packagename())
        if not skip_check_of_startapp:
            print("设备{}，skip_check_of_startapp为{}，开始初始化pocoui，处理应用权限".format(devices, skip_check_of_startapp))
            # 获取andorid的poco代理对象，准备进行开启应用权限（例如申请文件存储、定位等权限）点击操作
            pocoAndroid = AndroidUiautomationPoco(use_airtest_input=True, screenshot_each_action=False)
            n = self.get_iteration()

            # 以下代码写得极丑陋，以后有空再重构，期望是参数化。
            if devices == "127.0.0.1:62001":
                # 这里是针对不同机型进行不同控件的选取，需要用户根据自己的实际机型实际控件进行修改
                count = 0
                while not pocoAndroid("android.view.View").exists():
                    print("{}开启应用的权限点击，循环第{}次".format(devices, count))
                    if count >= n:
                        break
                    if pocoAndroid("com.android.packageinstaller:id/permission_allow_button").exists():
                        pocoAndroid("com.android.packageinstaller:id/permission_allow_button").click()
                    else:
                        time.sleep(self.get_timeout_of_per_action())
                        count += 1
            elif devices == "127.0.0.1:62025":
                count = 0
                while not pocoAndroid("android.view.View").exists():
                    print("{}开启应用的权限点击，循环第{}次".format(devices, count))
                    if count >= 3:
                        break
                    if pocoAndroid("android:id/button1").exists():
                        pocoAndroid("android:id/button1").click()
                    else:
                        time.sleep(3)
                        count += 1
        else:
            logger.info("设备{}，skip_check_of_startapp{}，不做开启权限点击操作".format(devices, skip_check_of_startapp))
        return None

    # 推送apk到设备上的函数，读配置决定要不要进行权限点击操作。
    def PushApk2Devices(self):
        skip_pushapk2devices = self.get_skip_pushapk2devices()
        skip_pushapk2devices = True if skip_pushapk2devices == "1" else False
        if skip_pushapk2devices:
            return "Skip"
        device = self.get_mdevice()
        skip_check_of_install = self.get_skip_check_of_install()
        skip_check_of_install = True if skip_check_of_install == "1" else False
        # 启动一个线程，执行AppInstall函数
        try:
            installThread = threading.Thread(target=self.AppInstall, args=())
            installThread.start()
            if not skip_check_of_install:
                # 如果配置上skip_check_of_install为True，则再开一个线程，执行安装权限点击操作
                logger.info("设备{}，skip_check_of_install为{}，开始进行安装点击权限操作".format(device, skip_check_of_install))
                inputThread = threading.Thread(target=self.InputEvent, args=())
                inputThread.start()
                inputThread.join()
            else:
                logger.info("设备{}，skip_check_of_install为{}，不进行安装点击权限操作".format(device, skip_check_of_install))
            installThread.join()
            # 从queue里获取线程函数的返回值
            result = q.get()
            if result == "Install Success":
                return "Success"
            else:
                return "Fail"
        except Exception as e:
            logger.error(e)
            pass

    def AppUninstall(self):
        devices = self.get_mdevice()
        package = self.get_packagename()
        auto_delete_package = self.auto_delete_package()
        auto_delete_package = True if auto_delete_package == "1" else False
        if auto_delete_package:
            if self.isinstalled():
                uninstallcommand = adb + " -s " + str(devices) + " uninstall " + package
                logger.info("正在{}上卸载{},卸载命令为：{}".format(devices, package, uninstallcommand))
                os.popen(uninstallcommand)
        else:
            logger.info("{}跳过卸载{}".format(devices, package))

    # 安装应用的方法，先判断应用包是否已安装，如已安装则卸载，然后按配置路径去重新安装。
    def AppInstall(self):
        devices = self.get_mdevice()
        apkpath = self.get_apkpath()
        package = self.get_packagename()
        logger.info("设备{}开始进行自动安装".format(devices))
        auto_install_package = self.auto_install_package()
        auto_install_package = True if auto_install_package == "1" else False
        # TODO 自动下载app包
        # if not os.path.exists(apkpath):
        #     r = requests.get(url)
        #     with open(apkpath, "wb") as code:
        #         try:
        #             code.write(r.content)
        #         except Exception:
        #             logger.error('下载失败')
        #         else:
        #             if os.path.exists(apkpath):
        #                 logger.info('下载成功')
        try:
            # time.sleep(self.get_timeout_of_startapp())
            installcommand = adb + " -s " + str(devices) + " install -r " + apkpath
            logger.info("正在{}上安装{},安装命令为：{}".format(devices, package, installcommand))
            if auto_install_package:
                os.system(installcommand)
            if self.isinstalled():
                logger.info("{}上安装成功，退出AppInstall线程".format(devices))
                # 将线程函数的返回值放入queue
                q.put("Install Success")
                return True
            else:
                logger.error("{}上安装未成功".format(devices))
                q.put("Install Fail")
                return False
        except Exception as e:
            logger.error("{}上安装异常".format(devices))
            logger.error(e)
            q.put("Install Fail")

    def InputEvent(self):
        devices = self.get_mdevice()
        logger.info("设备{}开始进行自动处理权限".format(devices))
        # 获取andorid的poco代理对象，准备进行开启安装权限（例如各个品牌的自定义系统普遍要求的二次安装确认、vivo/oppo特别要求的输入手机账号密码等）的点击操作。
        pocoAndroid = AndroidUiautomationPoco(use_airtest_input=True, screenshot_each_action=False)
        # 这里是针对不同机型进行不同控件的选取，需要用户根据自己的实际机型实际控件进行修改
        n = self.get_iteration()
        # 先实现功能，以后有空参数化函数
        if devices == "172.16.6.82:7425":
            count = 0
            # 找n次或找到对象以后跳出，否则等5秒重试。
            while True:
                logger.debug("{}安装应用的权限点击，循环第{}次".format(devices, count))
                if count >= n:
                    logger.debug("{}退出InputEvent线程".format(devices))
                    break
                if pocoAndroid("com.coloros.safecenter:id/et_login_passwd_edit").exists():
                    pocoAndroid("com.coloros.safecenter:id/et_login_passwd_edit").set_text("123456")
                    time.sleep(2)
                    if pocoAndroid("android.widget.FrameLayout").offspring("android:id/buttonPanel").offspring(
                            "android:id/button1").exists():
                        pocoAndroid("android.widget.FrameLayout").offspring("android:id/buttonPanel").offspring(
                            "android:id/button1").click()
                    break
                else:
                    time.sleep(5)
                count += 1
        elif devices == "127.0.0.1:62025":
            count = 0
            while True:
                logger.debug("{}安装应用的权限点击，循环第{}次".format(devices, count))
                if count >= n:
                    break
                if pocoAndroid("com.android.packageinstaller:id/continue_button").exists():
                    pocoAndroid("com.android.packageinstaller:id/continue_button").click()
                else:
                    time.sleep(5)
                count += 1

    # 判断给定设备里是否已经安装了指定apk
    def isinstalled(self):
        devices = self.get_mdevice()
        package = self.get_packagename()
        command = adb + " -s {} shell pm list package".format(devices)
        commandresult = os.popen(command)
        logger.info("设备{}进入isinstalled方法，package={}".format(devices, package))
        for pkg in commandresult:
            if "package:" + package in pkg:
                logger.info("在{}上发现已安装{}".format(devices, package))
                return True
        logger.info("在{}上没找到包{}".format(devices, package))
        return False

    # 判断给定设备的安卓版本号
    def get_androidversion(self):
        command = adb + " -s {} shell getprop ro.build.version.release".format(self.get_mdevice())
        version = os.popen(command).read()
        return int(version)

    # 判断给定设备的手机型号
    def get_androidmodel(self):
        command = adb + " -s {} shell getprop ro.product.model".format(self.get_mdevice())
        brand = os.popen(command).read()
        return str(brand)

    # 判断给定设备运行指定apk时的内存占用
    def get_allocated_memory(self):
        command = adb + " -s {} shell dumpsys meminfo {}".format(self.get_mdevice(), self.get_packagename())
        memory = os.popen(command)
        list = []
        for line in memory:
            line = line.strip()
            list = line.split(' ')
            if list[0] == "TOTAL":
                while '' in list:
                    list.remove('')
                allocated_memory = format(int(list[1]) / 1024, ".2f")
                q.put(allocated_memory)
                return allocated_memory
        q.put("N/a")
        return "N/a"

    # 判断给定设备运行时的内存总占用
    def get_totalmemory(self):
        command = adb + " -s {} shell dumpsys meminfo ".format(self.get_mdevice())
        memory = os.popen(command)
        TotalRAM = 0
        for line in memory:
            line = line.strip()
            list = line.split(":")
            if list[0] == "Total RAM":
                if self.get_androidversion() < 7:
                    TotalRAM = format(int(list[1].split(" ")[1]) / 1024, ".2f")
                elif self.get_androidversion() > 6:
                    TotalRAM = format(int(list[1].split("K")[0].replace(",", "")) / 1024, ".2f")
                break
        q.put(TotalRAM)
        return TotalRAM

    # 判断给定设备运行时的空闲内存
    def get_freememory(self):
        command = adb + " -s {} shell dumpsys meminfo ".format(self.get_mdevice())
        # print(command)
        memory = os.popen(command)
        FreeRAM = 0
        for line in memory:
            line = line.strip()
            list = line.split(":")
            if list[0] == "Free RAM":
                if self.get_androidversion() < 7:
                    FreeRAM = format(int(list[1].split(" ")[1]) / 1024, ".2f")
                elif self.get_androidversion() > 6:
                    FreeRAM = format(int(list[1].split("K")[0].replace(",", "")) / 1024, ".2f")
                break
        q.put(FreeRAM)
        return FreeRAM

    # 判断给定设备运行时的总使用内存
    def get_usedmemory(self):
        command = adb + " -s {} shell dumpsys meminfo ".format(self.get_mdevice())
        # print(command)
        memory = os.popen(command)
        UsedRAM = 0
        for line in memory:
            line = line.strip()
            list = line.split(":")
            if list[0] == "Used RAM":
                if self.get_androidversion() < 7:
                    UsedRAM = format(int(list[1].split(" ")[1]) / 1024, ".2f")
                elif self.get_androidversion() > 6:
                    UsedRAM = format(int(list[1].split("K")[0].replace(",", "")) / 1024, ".2f")
                break
        q.put(UsedRAM)
        return UsedRAM

    # 判断给定设备运行时的Total/Free/Used内存,一次dump，加快获取速度
    def get_memoryinfo(self):
        command = adb + " -s {} shell dumpsys meminfo ".format(self.get_mdevice())
        # print(command)
        memory = os.popen(command)
        androidversion = self.get_androidversion()
        TotalRAM, FreeRAM, UsedRAM = '', '', ''
        meminfo = {}
        for line in memory:
            line = line.strip()
            list = line.split(":")
            if list[0] == "Total RAM":
                if androidversion < 7:
                    TotalRAM = format(int(list[1].split(" ")[1]) / 1024, ".2f")
                elif androidversion > 6:
                    TotalRAM = format(int(list[1].split("K")[0].replace(",", "")) / 1024, ".2f")
            elif list[0] == "Free RAM":
                if androidversion < 7:
                    FreeRAM = format(int(list[1].split(" ")[1]) / 1024, ".2f")
                elif androidversion > 6:
                    FreeRAM = format(int(list[1].split("K")[0].replace(",", "")) / 1024, ".2f")
            elif list[0] == "Used RAM":
                if androidversion < 7:
                    UsedRAM = format(int(list[1].split(" ")[1]) / 1024, ".2f")
                elif androidversion > 6:
                    UsedRAM = format(int(list[1].split("K")[0].replace(",", "")) / 1024, ".2f")
        q.put(TotalRAM, FreeRAM, UsedRAM)
        # meminfo['TotalRAM'] = TotalRAM
        # meminfo['FreeRAM'] = FreeRAM
        # meminfo['UsedRAM'] = UsedRAM
        # q.put(meminfo)
        return TotalRAM, FreeRAM, UsedRAM

    # 判断给定设备运行时的总CPU占用。部分手机在安卓8以后多内核会分别显示CPU占用，这里统一除以内核数。
    def get_totalcpu(self):
        command = adb + " -s {} shell top -n 1 ".format(self.get_mdevice())
        # print(command)
        commandresult = os.popen(command)
        cputotal = 0
        andversion = self.get_androidversion()
        maxcpu = 1
        # ABI判断设备的内核型号，对一般安卓手机来说，基本都是ARM，但对模拟器来说，内核一般是X86。可以用这个值来判断真机或模拟器。
        ABIcommand = adb + " -s {} shell getprop ro.product.cpu.abi".format(self.get_mdevice())
        ABI = os.popen(ABIcommand).read().strip()
        # 逐行分析adbdump，根据不同的版本解析返回结果集，获得相应的cpu数据。
        for line in commandresult:
            list = line.strip().split(" ")
            while '' in list:
                list.remove('')
            if len(list) > 8:
                if andversion < 7 and ABI != "x86":
                    if ("%" in list[2] and list[2] != "CPU%"):
                        cpu = int(list[2][:-1])
                        if cpu != 0:
                            cputotal = cputotal + cpu
                        else:
                            break
                if andversion < 7 and ABI == "x86":
                    if "%cpu" in list[0]:
                        maxcpu = list[0]
                        idlecpu = list[4]
                        cputotal = int(maxcpu.split("%")[0]) - int(idlecpu.split("%")[0])
                        maxcpu = int(int(maxcpu.split("%")[0]) / 100)
                elif andversion == 7 and ABI != "x86":
                    if ("%" in list[4] and list[4] != "CPU%"):
                        cpu = int(list[4][:-1])
                        if cpu != 0:
                            cputotal = cputotal + cpu
                        else:
                            break
                elif andversion == 7 and ABI == "x86":
                    if "%cpu" in list[0]:
                        maxcpu = list[0]
                        idlecpu = list[4]
                        cputotal = int(maxcpu.split("%")[0]) - int(idlecpu.split("%")[0])
                        maxcpu = int(int(maxcpu.split("%")[0]) / 100)
                elif andversion > 7 and ABI != "x86":
                    if "%cpu" in list[0]:
                        maxcpu = list[0]
                        idlecpu = list[4]
                        cputotal = int(maxcpu.split("%")[0]) - int(idlecpu.split("%")[0])
                        maxcpu = int(int(maxcpu.split("%")[0]) / 100)
        # 由于cputotal在安卓7以下的adbdump里，无法通过Total-Idle获得，只能通过各个进程的CPU占用率累加，故有可能因四舍五入导致总和超过100%。当这种情况发生，则手动将cputotal置为100%。
        if cputotal > 100:
            cputotal = 100
        q.put(cputotal, maxcpu)
        return cputotal, maxcpu

    # 判断给定设备运行时的总使用CPU
    def get_allocated_cpu(self):
        start = time.time()
        ABIcommand = adb + " -s {} shell getprop ro.product.cpu.abi".format(self.get_mdevice())
        ABI = os.popen(ABIcommand).read().strip()
        # 包名过长时，包名会在adbdump里被折叠显示，所以需要提前将包名压缩，取其前11位基本可以保证不被压缩也不被混淆
        packagename = self.get_packagename()[0:11]
        command = adb + " -s {} shell top -n 1 |findstr {} ".format(self.get_mdevice(), packagename)
        # print(command)
        subresult = os.popen(command).read()
        version = self.get_androidversion()
        if subresult == "":
            q.put("N/a")
            return "N/a"
        else:
            cpuresult = subresult.split(" ")
            # 去空白项
            while '' in cpuresult:
                cpuresult.remove('')
            # print(self.get_mdevice(),"cpuresult=",cpuresult)
            cpu = ""
            if version < 7 and ABI != "x86":
                cpu = cpuresult[2].split("%")[0]
            if version < 7 and ABI == "x86":
                cpu = cpuresult[8]
            elif version == 7 and ABI != "x86":
                cpu = cpuresult[4].split("%")[0]
            elif version == 7 and ABI == "x86":
                cpu = cpuresult[8]
            elif version > 7:
                cpu = cpuresult[8]
            q.put(cpu)
            return cpu

    # 算法提取自 https://github.com/ChromiumWebApps/chromium/tree/master/build/android/pylib
    def get_fps(self):
        device = self.get_mdevice()
        package = self.get_packagename()
        activity = self.get_activityname()
        androidversion = self.get_androidversion()
        command = ""
        if androidversion < 7:
            command = adb + " -s {} shell dumpsys SurfaceFlinger --latency 'SurfaceView'".format(device)
        elif androidversion == 7:
            command = adb + " -s {} shell \"dumpsys SurfaceFlinger --latency 'SurfaceView - {}/{}'\"".format(device,
                                                                                                             package,
                                                                                                             activity)
        elif androidversion > 7:
            command = adb + " -s {} shell \"dumpsys SurfaceFlinger --latency 'SurfaceView - {}/{}#0'\"".format(device,
                                                                                                               package,
                                                                                                               activity)
            # command= adb + " -s {} shell \"dumpsys SurfaceFlinger --latency\"".format(device)
        print(command)
        results = os.popen(command)
        if not results:
            print("nothing")
            return (None, None)
        # print(device,results.read())
        timestamps = []
        # 定义纳秒
        nanoseconds_per_second = 1e9
        # 定义刷新间隔
        refresh_period = 16666666 / nanoseconds_per_second
        # 定义挂起时间戳
        pending_fence_timestamp = (1 << 63) - 1
        # 遍历结果集
        for line in results:
            # 去空格并分列
            line = line.strip()
            list = line.split("\t")
            # 剔除非数据列
            if len(list) != 3:
                continue
            # 取中间一列数据
            timestamp = float(list[1])
            # 当时间戳等于挂起时间戳时，舍弃
            if timestamp == pending_fence_timestamp:
                continue
            timestamp /= nanoseconds_per_second
            # 安卓7的adbdump提供255行数据，127行0以及128行真实数据，所以需要将0行剔除
            if timestamp != 0:
                timestamps.append(timestamp)
        # 获得总帧数
        frame_count = len(timestamps)
        # 获取帧列表总长、规范化帧列表总长
        frame_lengths, normalized_frame_lengths = self.GetNormalizedDeltas(timestamps, refresh_period, 0.5)
        if len(frame_lengths) < frame_count - 1:
            print('Skipping frame lengths that are too short.')
        frame_count = len(frame_lengths) + 1
        # 数据不足时，返回None
        if not refresh_period or not len(timestamps) >= 3 or len(frame_lengths) == 0:
            print("未收集到有效数据")
            return "N/a"
        # 总秒数为时间戳序列最后一位减第一位
        seconds = timestamps[-1] - timestamps[0]
        fps = int(round((frame_count - 1) / seconds))
        # 这部分计算掉帧率。思路是先将序列化过的帧列表重新序列化，由于min_normalized_delta此时为None，故直接求出frame_lengths数组中各个元素的差值保存到数组deltas中。
        # length_changes, normalized_changes = self.GetNormalizedDeltas(frame_lengths, refresh_period)
        # 求出normalized_changes数组中比0大的数，这部分就是掉帧。
        # jankiness = [max(0, round(change)) for change in normalized_changes]
        # pause_threshold = 20
        # normalized_changes数组中大于0小于20的总和记为jank_count。这块算法是看明白了，但思路get不到。。。
        # jank_count = sum(1 for change in jankiness  if change > 0 and change < pause_threshold)
        return fps

    # 将时间戳序列分2列并相减，得到时间差的序列。
    # 时间差序列中，除刷新间隔大于0.5的时间差重新序列化
    def GetNormalizedDeltas(self, data, refresh_period, min_normalized_delta=None):
        deltas = [t2 - t1 for t1, t2 in zip(data, data[1:])]
        if min_normalized_delta != None:
            deltas = filter(lambda d: d / refresh_period >= min_normalized_delta,
                            deltas)

        return list(deltas), [delta / refresh_period for delta in deltas]

    def setScreenOFF(self):
        platform = sys.platform
        device = self.get_mdevice()
        command1 = command2 = ""
        # setScreenON(device)
        if platform == "win32":
            command1 = "adb -s {}  shell dumpsys window policy|findstr mScreenOnFully".format(device)
        else:
            command1 = "adb -s {}  shell dumpsys window policy|grep mScreenOnFully".format(device)
        print(command1)
        result = os.popen(command1)
        line = result.read()
        if "mScreenOnEarly=false" in line:
            pass
        else:
            command2 = "adb -s {}  shell input keyevent 26".format(device)
            os.popen(command2)
        off = True
        n = 0
        while off or n < 10:
            result = os.popen(command1)
            line = result.read()
            if "mScreenOnEarly=true" in line:
                os.popen(command2)
                time.sleep(2)
                n += 1
            else:
                off = False
        print(device, "has been ScreenOFF")


if __name__ == "__main__":
    '''
    #android 9
    madb1=MultiAdb("172.16.6.82:7413")
    print("total1=",madb1.get_totalcpu())
    #android 8
    madb2=MultiAdb("172.16.6.82:7437")
    print("total2=",madb2.get_totalcpu())
    #android 7
    madb3=MultiAdb("172.16.6.82:7409")
    print("total3=",madb3.get_totalcpu())
    #android 6
    madb4=MultiAdb("172.16.6.82:7441")
    print("total4=",madb4.get_totalcpu())
    '''
    print(sys.platform)
    # madb=MultiAdb("cbe9d630")761b48c8
    madb = MultiAdb()
    # madb.setScreenON()
    sleep(5)
    # madb.setScreenOFF()
