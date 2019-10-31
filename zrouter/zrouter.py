#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2019/10/29
# Describe：运行所有脚本

import os
import time

print("开始测试动态API。。。")
os.system('python ./api/scripts/api.py dynamic')
print("动态API测试完成，休息5秒。。。")
time.sleep(5)
print("开始测试静态API。。。")
os.system('python ./api/scripts/api.py static')
print("静态API测试完成，休息80秒。。。")
time.sleep(80)
print("开始测试WAN功能。。。")
os.system('python ./func/wan/scripts/wan.py')
print("WAN功能测试完成，休息5秒。。。")
time.sleep(5)
print("开始测试WIFI功能。。。")
os.system('python ./func/wifi/scripts/wifi.py')
print("WIFI功能测试完成，休息5秒。。。")
time.sleep(5)
print("开始测试zgateway功能。。。")
os.system('python ./func/zgateway/scripts/zgateway.py')
print("zgateway功能测试完成，自动化测试完成。。。")
