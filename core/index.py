# -*- coding: utf-8 -*-
# author:liucong
# -*- coding: utf-8 -*-
# author:lcy
import traceback

from airtest.core.error import *
from poco.exceptions import *
from airtest.core.api import *
from core import RunTestCase
from Performance import *

#
# from tools.Email import *
from tools.Email import Email
from tools.log import logger

index_print = print


def print(*args, **kwargs):
    index_print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), *args, **kwargs)


'''
整个框架的主程序，根据配置表读取设备，并逐一为其分配功能测试进程和性能测试进程。
由于每个设备需要调用2个进程配合工作，所以使用Value进行进程间通信。Value会传递一个int值，默认为0，在功能进程结束时通知性能进程随之结束。
'''


def main():
    # 默认去config.ini里读取期望参与测试的设备，若为空，则选择当前连接的所有状态为“device”的设备
    devicesList = Madb().get_devicesList()
    if devicesList[0] == "":
        devicesList = Madb().getdevices()
    logger.info("最终的devicesList={}".format(devicesList))
    if Madb().get_apkpath() == "" or Madb().get_packagename() == "":
        logger.error("配置文件填写不全，packagename和apkpath是必填项")
        devicesList = None
    # 读取是否跳过发送邮件
    skip_email_flag = Madb().get_skip_email()
    skip_email = True if skip_email_flag == '1' else False
    # 读取是否需要同步性能测试的配置。
    skip_performance = Madb().get_skip_performance()
    skip_performance = True if skip_performance == "1" else False
    is_storaged_by_excel = Madb().get_storage_by_excel()
    is_storaged_by_excel = True if is_storaged_by_excel == "1" else False
    reportpath = os.path.join(os.getcwd(), "Report")
    # 没有Report目录时自动创建
    if not os.path.exists(reportpath):
        os.mkdir(reportpath)
        os.mkdir(reportpath + "/Screen")
        logger.debug(reportpath)
    logger.info("测试开始")
    if devicesList:
        try:
            logger.info("启动进程池")
            # 进程池
            p_list = []
            # 根据设备列表去循环创建进程，对每个进程调用下面的enter_processing/enter_enter_performance方法。
            for i in range(len(devicesList)):
                # start会被传递到2个进程函数里，作为区分最终产物html和excel的标志
                start = time.localtime()
                madb = Madb(devicesList[i])
                if madb.get_androidversion() < 5:
                    logger.error("设备{}的安卓版本低于5，不支持。".format(madb.get_mdevice()))
                    continue
                else:
                    # 进程通信变量flag，默认为0，完成测试时修改为1。
                    flag = Value('i', 0)
                    if not skip_performance:
                        pro1 = Process(target=enter_performance, args=(madb, flag, start, is_storaged_by_excel))
                        p_list.append(pro1)
                pro2 = Process(target=enter_processing, args=(i + 1, madb, flag, start,))
                p_list.append(pro2)
            for p1 in p_list:
                p1.start()
            for p2 in p_list:
                p2.join()
            logger.info("进程回收完毕")
            logger.info("测试结束")
        except AirtestError:
            logger.error("Airtest发生错误" + traceback.format_exc())
        except PocoException:
            logger.error("Poco发生错误" + traceback.format_exc())
        except Exception:
            logger.error("发生未知错误" + traceback.format_exc())
    else:
        logger.error("未找到设备，测试结束")
    # 判断是否发送邮件
    if not skip_email:
        try:
            Email().send_email()
        except Exception:
            logger.error(traceback.format_exc())
    else:
        logger.info('跳过发送邮件')

'''
功能进程模块
首先调用airtest库的方法进行设备连接并初始化，然后读取配表，进行应用的安装、启动、权限点击等操作。同步的操作会分由线程来完成。
确定启动应用成功以后，调用分配测试用例的RunTestCase函数。
在用例执行完毕以后，将Value置为1。
'''


def enter_processing(processNo, madb, flag, start):
    devices = madb.get_mdevice()
    logger.info("进入{}进程,devicename={}".format(processNo, devices))
    installflag = ""
    startflag = ""
    installResult = ''
    try:
        # 调用airtest的各个方法连接设备
        # connect_device("Android:///" + devices)
        try:
            connect_device("android://127.0.0.1:5037/{}?cap_method=javacap&touch_method=adb".format(devices))
        except Exception as e:
            isconnect = 'Fail'
            logger.error(e)
        else:
            time.sleep(madb.get_timeout_of_per_action())
            isconnect = "Pass"
            logger.info("设备{}连接成功".format(devices))
        if isconnect == "Pass":
            try:
                logger.info("设备{}开始安装apk".format(devices))
                # 尝试推送apk到设备上
                installResult = madb.PushApk2Devices()
                if installResult == "Success":
                    logger.info("{}确定安装成功".format(devices))
                    installflag = "Success"
                if installResult == "Skip":
                    logger.info("{}设备跳过PushAPK2Device步骤".format(devices))
                    installflag = "Success"
            except Exception:
                logger.info("{}安装失败，installResult={}".format(devices, installResult))
                logger.error(traceback.format_exc())
            if installflag == "Success":
                try:
                    # 尝试启动应用
                    madb.StartApp()
                    startflag = "Success"
                except Exception:
                    logger.error("运行失败", traceback.format_exc())
            time.sleep(madb.get_timeout_of_per_action())
            # 应用启动成功则开始运行用例
            if startflag == "Success":
                RunTestCase.RunTestCase(madb, start)
                logger.info("{}完成测试".format(devices))
                # 根据配置判断是否卸载app
                madb.AppUninstall()
            else:
                logger.error("{}未运行测试。".format(devices))
        else:
            logger.error("设备{}连接失败".format(devices))
    except Exception:
        logger.error(traceback.format_exc())
    # 无论结果如何，将flag置为1，通知Performance停止记录。
    flag.value = 1
    # madb.setScreenOFF()


if __name__ == "__main__":
    madb = Madb("172.16.6.82:20484")
    madb.setScreenOFF()
