# -*- coding: utf-8 -*-
# author:liucong

import requests
import base64
import time


def jenkins_lastBuild_info():
    url = 'http://172.16.67.210:8080/jenkins/view/all/job/haima_android/lastBuild/api/json'
    username = "admin"
    password = "admin"
    auth = username + ":" + password
    headers = {"Content-Type": "application/json", 'Connection': 'close',
               "Authorization": "Basic " + base64.b64encode(auth.encode(encoding="utf-8")).decode(encoding='utf-8')}
    response = requests.get(url, headers=headers, verify=False)
    return response.json()
    result = response.json()

    jenkins_branch = result['displayName']
    timeArray = time.localtime(result['timestamp'] / 1000)
    jenkins_time = time.strftime("%Y--%m--%d %H:%M:%S", timeArray)
    print("111")
