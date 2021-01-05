# -*- coding: utf-8 -*-
# author:lc

import unittest

from poco.drivers.android.uiautomation import AndroidUiautomationPoco

from tools.log import logger
from airtest.core.api import *
from core.MultiAdb import MultiAdb as Madb


def run_case(devices, poco):
    logger.info("{}进入unittest".format(devices))
    package = Madb(devices).get_packagename()

    class TC102(unittest.TestCase):
        u'''添加好友'''

        @classmethod
        def setUpClass(cls):
            """ 这里放需要在所有用例执行前执行的部分"""
            wake()

        def setUp(self):
            """这里放需要在每条用例前执行的部分"""
            start_app(package)
            sleep(2)

        def test_demo2(self):
            """此处添加用例描述"""
            poco(text='手机号登录').click()

        def tearDown(self):
            """这里放需要在每条用例后执行的部分"""
            sleep(5)
            stop_app(package)

        # @classmethod
        # def tearDownClass(cls):
        #     u"""这里放需要在所有用例后执行的部分"""
        #     stop_app("com.qywlandroid")
        #     sleep(1)

    srcSuite = unittest.TestLoader().loadTestsFromTestCase(TC102)
    # srcSuite = TC101("test_demo2")
    return srcSuite

