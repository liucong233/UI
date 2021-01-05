# -*- coding: utf-8 -*-
# author:liucong

import configparser
import os

con = configparser.ConfigParser()


# 获取项目名称
def getProName(path, key):
    con.read(path)
    result = con.get("project", key)
    return result


# 解析config文件并将其结果转成一个list，对单个的value，到时候可以用[0]来取到。
def getProConfig(path, key, pro):
    con.read(path)
    result = con.get("{}_config".format(pro), key)
    config = result.split(",")
    return config


# 解析config文件并将其结果转成一个list，对单个的value，到时候可以用[0]来取到。
def getBasicConfig(path, key):
    con.read(path)
    result = con.get("basic_config", key)
    return result


# 基本同上，读取TestCaseforDevice 节点下的键值
def getTestCase(path, pro, device=""):
    if device != "":
        con.read(path)
        result = con.get("{}_TestCaseforDevice".format(pro), device)
        case_list = result.split(",")
        return case_list
    else:
        return []


def getEmail(path, key):
    con.read(path)
    result = con.get("Email", key)
    return result


# 重新写回配置文件
def setValue(configpath, key, value):
    if key != "" and value != "":
        con.set("config", key, value)
        con.write(open(configpath, "w"))
