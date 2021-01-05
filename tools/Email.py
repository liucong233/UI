# -*- coding: utf-8 -*-
# author:liucong

import smtplib, os, inspect
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from tools import Config
from tools.log import get_logger

configPath = os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(
    inspect.getfile(inspect.currentframe())) + os.path.sep + ".")) + os.path.sep + ".") + "\config.ini"

logger = get_logger('Email')


class Email(object):
    def __init__(self):
        self.smtp_server = Config.getEmail(configPath, "mail_host")
        self.username = Config.getEmail(configPath, "mail_user")
        self.password = Config.getEmail(configPath, "mail_pass")
        self.sender = Config.getEmail(configPath, "sender")
        # receivers为列表
        self.receivers = Config.getEmail(configPath, "receivers").split(',')
        self.addr_from = Config.getEmail(configPath, "from")
        self.addr_to = Config.getEmail(configPath, "to")

    # 设置邮件正文
    def set_content(self):
        send_time = time.strftime('%Y-%m-%d %H:%M:%S')
        msg = MIMEText("{}的测试报告结果".format(send_time), 'plain', 'utf-8')  # 邮件正文
        msg['From'] = self.addr_from  # 发送邮件的地址
        msg['To'] = self.addr_to  # 接收邮件的地址
        subject = "{} UI自动化测试报告".format(send_time)  # 邮件标题
        msg['Subject'] = subject
        return msg

    def send_email(self):
        # 第三方 SMTP 服务
        server = smtplib.SMTP(self.smtp_server, 25)
        server.login(self.username, self.password)
        msg = self.set_content()
        logger.info('----------------------------> 邮件发送中')
        server.sendmail(self.sender, self.receivers, msg.as_string())
        logger.info('----------------------------> 邮件发送成功')
        server.quit()
