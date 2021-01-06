# -*- coding: utf-8 -*-
# author:liucong

import inspect
import unittest
from tools.log import logger
from airtest.core.api import *
from core.MultiAdb import MultiAdb as Madb

# 获取工程路径
pro_path = os.path.dirname(inspect.getfile(inspect.currentframe())) + os.path.sep + ".."
# 获取case的图片路径
img_path = os.path.join(pro_path, 'TestCaseImage')
# 获取对应项目的case图片路径
case_img = os.path.join(img_path, 'project1')


def run_case(devices, poco):
    logger.debug("{}进入unittest".format(devices))
    package = Madb(devices).get_packagename()

    class TC101(unittest.TestCase):
        """用例描述"""

        @classmethod
        def setUpClass(cls):
            """ 这里放需要在所有用例执行前执行的部分"""
            wake()

        def setUp(self):
            """这里放需要在每条用例前执行的部分"""
            start_app(package)
            sleep(2)

        def test_login(self):
            """点击微信登录"""
            pass
            # logger.info('执行1')
            # poco(text='微信登录').click()

        def test_demo2(self):
            """点击手机号登录"""
            pass
            # logger.info('执行2')
            # poco(text='手机号登录').click()
            # pass

        def test_demo3(self):
            """touch使用"""
            pass
            # logger.info('执行test_demo3')
            # touch(Template('{}/login_on.png'.format(case_img)))

        def tearDown(self):
            """这里放需要在每条用例后执行的部分"""
            sleep(5)
            stop_app(package)

        @classmethod
        def tearDownClass(cls):
            u"""这里放需要在所有用例后执行的部分"""
            pass

    # 调试测试类下所有方法
    # srcSuite = unittest.TestLoader().loadTestsFromTestCase(TC101)
    # 调试测试类下某个方法
    srcSuite = TC101("test_login")
    return srcSuite
