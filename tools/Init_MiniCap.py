# -*- coding: utf-8 -*-
# author:liucong


from core.MultiAdb import MultiAdb as Madb
from tools.Screencap import *

_print = print


def print(*args, **kwargs):
    _print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), *args, **kwargs)


adb_str = ADB().adb_path
if adb_str.count(' ') != 0:
    adb = '\"' + adb_str + '\"'
else:
    adb = adb_str


# 用来给设备初始化MiniCap的，介绍见 https://blog.csdn.net/saint_228/article/details/92142914
def ini_MiniCap(devices):
    try:
        parent_path = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())) + os.path.sep + ".")
        root_path = os.path.abspath(os.path.dirname(parent_path) + os.path.sep + ".")
        print("项目目录为{}".format(root_path))
        ABIcommand = adb + " -s {} shell getprop ro.product.cpu.abi".format(devices)
        ABI = os.popen(ABIcommand).read().strip()
        print("ABI为{}".format(ABI))
        AndroidVersion = os.popen(adb + " -s {} shell getprop ro.build.version.sdk".format(devices)).read().strip()
        airtest_minicap_path = os.path.abspath(
            os.path.dirname(root_path) + os.path.sep + ".") + "\\airtest\\core\\android\\static\\stf_libs"
        airtest_minicapso_path = os.path.abspath(os.path.dirname(
            root_path) + os.path.sep + ".") + "\\airtest\\core\\android\\static\\stf_libs\\minicap-shared\\aosp\\libs\\" + "android-{}\\{}\\minicap.so".format(
            AndroidVersion, ABI)
        push_minicap = adb + " -s {} push {}/{}/minicap".format(devices, airtest_minicap_path,
                                                                ABI) + " /data/local/tmp/"
        push_minicapso = adb + " -s {} push {}".format(devices, airtest_minicapso_path) + " /data/local/tmp/"
        print("推送minicap和minicap.so")
        os.popen(push_minicap)
        os.popen(push_minicapso)
        chmod = adb + " -s {} shell chmod 777 /data/local/tmp/*".format(devices)
        print("赋予权限成功")
        os.popen(chmod)
        wm_size_command = adb + " -s {} shell wm size".format(devices)
        vm_size = os.popen(wm_size_command).read()
        vm_size = vm_size.split(":")[1].strip()
        print("屏幕分辨率为{}".format(vm_size))
        start_minicap = adb + " -s {} shell LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P {}@{}/0 -t".format(
            devices, vm_size, vm_size)
        result = os.popen(start_minicap).read()
        print(result)
        print("设备{}上已经成功安装并开启了MiniCap。".format(devices))
    except Exception as e:
        print(e, traceback.format_exc())


if __name__ == "__main__":
    devicesList = Madb().get_devicesList()
    if devicesList[0] == "":
        devicesList = Madb().getdevices()
    print("最终的devicesList=", devicesList)
    for device in devicesList:
        ini_MiniCap(device)
        # GetScreenbyMiniCap(time.time(),device,"测试")
