# -*- coding: utf-8 -*-
# author:liucong

import logging
import os
import time
import configparser

con = configparser.ConfigParser()
pro_path = os.getcwd()
log_path = os.path.join(pro_path, '../log')
logname = os.path.join(log_path, '{0}.txt'.format(time.strftime('%Y-%m-%d')))
config_path = os.path.join(pro_path, '../config.ini')


def get_basic_config(key):
    con.read(config_path)
    result = con.get("basic_config", key)
    return result


def get_logger(name):
    # logger = logging.root
    # use 'airtest' as root logger name to prevent changing other modules' logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # 流控制器
    try:
        detail_flag = get_basic_config('detail_log')
    except Exception:
        print('{}不存在，流控制器默认等级设为DEBUG'.format(config_path))
        level = logging.DEBUG
    else:
        detail_flag = True if detail_flag == '1' else False
        if detail_flag:
            level = logging.DEBUG
        else:
            level = logging.INFO
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter(
        fmt='[%(asctime)s][%(levelname)s]<%(name)s> %(message)s',
        datefmt='%I:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # 日志处理器
    if not os.path.exists(logname):
        os.popen('')
        log = open(logname, "a")
        log.close()
    log_handle = logging.FileHandler(logname, 'a', encoding='utf-8')
    log_handle.setLevel(logging.DEBUG)
    log_handle.setFormatter(formatter)
    logger.addHandler(log_handle)
    return logger
