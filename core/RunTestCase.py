# -*- coding: utf-8 -*-
# author:lcy

import unittest
from extra.BeautifulReport import BeautifulReport
from core.MultiAdb import *
from TestCase import *
from airtest.core.android.adb import ADB
from tools.log import *
from util.commoninterface import *

_print = print


def print(*args, **kwargs):
    _print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), *args, **kwargs)


adb_str = ADB().adb_path
if adb_str.count(' ') != 0:
    adb = '\"' + adb_str + '\"'
else:
    adb = adb_str


# 运行Testcase的主函数
def RunTestCase(madb, start):
    # 获取设备列表
    devices = madb.get_mdevice()
    logger.info("进入{}的RunTestCase".format(devices))

    # 获取是否跳过生成测试报告
    skip_report = madb.get_skip_report()
    report_flag = True if skip_report == "1" else False

    # 获取jenkins部署信息
    jenkins_branch, timestamp = jenkins_lastBuild_info()
    logger.info('jenkins分支：{}'.format(jenkins_branch))
    timeArray = time.localtime(timestamp / 1000)
    jenkins_time = time.strftime("%Y--%m--%d %H:%M:%S", timeArray)
    logger.info('部署时间：{}'.format(jenkins_time))

    # 获取手机型号
    command = adb + " -s {} shell getprop ro.product.model".format(devices)
    brand = os.popen(command).read()
    # 获取手机版本
    command1 = adb + " -s {} shell getprop ro.build.version.release".format(devices)
    version = os.popen(command1).read()
    # 获取路径
    package = madb.get_packagename()
    TestCasePath = madb.get_TestCasePath()
    if not os.path.exists(TestCasePath):
        logger.error("测试用例需放到‘TestCase’文件目录下")
    reportpath = os.path.join(os.getcwd(), "Report")
    # 读取ini文件，获得期望测试的用例列表
    TestList = madb.get_testcaseforselfdevice()
    logger.info("{}的待测用例为：{}".format(madb.get_mdevice(), TestList))
    # 通过GetPyList方法，取得目录里可测试的用例列表
    scriptList = File.GetPyList(TestCasePath)
    # 初始化测试套件
    suite = unittest.TestSuite()
    # 初始化poco
    poco = AndroidUiautomationPoco()
    for i in range(len(TestList)):
        fileName = "TC_" + TestList[i]
        logger.debug("fileName={}".format(fileName))
        if fileName in scriptList:
            # 在整个命名空间里遍历所有名称为"TC_xx.py"形式的文件，默认这些文件都是unittest测试文件，然后调用其run_case函数。
            result = globals()[fileName].run_case(devices, poco)
            # 根据result类型判断调试单个方法or全部方法
            if isinstance(result, unittest.suite.TestSuite):
                suite.addTests(result)
            else:
                suite.addTest(result)
    # 聚合报告到BR
    unittestReport = BeautifulReport(suite)
    nowtime = time.strftime("%Y%m%d%H%M%S", start)
    unittestReport.report(filename=madb.get_nickname() + "_" + str(nowtime), description=package, report_dir=reportpath,
                          brand=brand, version=version, jenkins_branch=jenkins_branch, jenkins_time=jenkins_time,
                          report_flag=report_flag)
