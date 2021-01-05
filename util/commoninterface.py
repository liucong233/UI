# -*- coding: utf-8 -*-
# author:liucong

import random
import json
import requests
import base64
import time
from core.MultiAdb import MultiAdb as madb
# hmlt_base_url = "http://api.dev.haimaliaotian.com/"
hmlt_base_url = "http://azure-api.haimaliaotian.com/"
hmlt_base_admin_url = "http://azure-admin.haimaliaotian.com"

# 获取jenkins打包时间及分支信息
def jenkins_lastBuild_info():
    jenkins_url = madb().get_jenkins_url()
    jenkins_url = jenkins_url + '/api/json'
    # url = 'http://staging-ops.situdata.com/jenkins/job/%E4%B8%AD%E5%AE%8F%E4%BA%BA%E5%AF%BF-android-staging-A%E7%AB' \
    #       '%AF/api/json'
    username = "wangqian@situdata.com"
    password = "Pisen666"
    auth = username + ":" + password
    headers = {"Content-Type": "application/json", 'Connection': 'close',
               "Authorization": "Basic " + base64.b64encode(auth.encode(encoding="utf-8")).decode(encoding='utf-8')}
    response = requests.get(jenkins_url, headers=headers, verify=False)
    res = response.json()
    jenkins_branch = res['displayName']
    last_url = 'http://staging-ops.situdata.com' + \
               res['lastBuild']['url'].replace('http://jenkins.situdata.com', '') + 'api/json'
    response = requests.get(last_url, headers=headers, verify=False)
    res = response.json()
    timestamp = res['timestamp']

    return jenkins_branch, timestamp