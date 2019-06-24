#!/usr/bin/python

import requests
import functools
import time
import os
import logging
import json
import unittest
import uuid
from selenium import webdriver


class ServerInfo(object):
    control_url = ''
    control_headers = {}


server = ServerInfo
server.control_url = 'https://tlink.zihome.com/link-handle-gateway/v1/operate/device/control'
server.control_headers = {'GATEWAY-VALIDATE': 'kLSIUlsSLILEKXasAAALIELKFJCKSILidksKALSIDKCKAKSIDKOA',
               'content-type': 'application/json'}


def try_fun(func):
    if callable(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            try:  # 进行异常捕获
                response = func(*args, **kw)
            except Exception as e:
                print(e)
                response = None
            return response
        return wrapper
    else:
        def decorator(fn):
            @functools.wraps(fn)
            def wrapper(*args, **kw):
                try:  # 进行异常捕获
                    response = fn(*args, **kw)
                except Exception as e:
                    print(e)
                    response = None
                return response
            return wrapper
        return decorator


def logging_init():
    if 0 == os.path.exists("log"):
        print("log file don't exist.create")
        os.mkdir("log")
    else:
        print("log file exist")

    logging.basicConfig(  # filename="log/test.log", # 指定输出的文件
        level=logging.DEBUG,
        format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

    return True


def enter_error_passwd():
    # 绑定浏览器
    Browser = webdriver.Chrome()
    # 打开页面
    url = "http://192.168.18.1/#/home"
    Browser.get(url)

    time.sleep(1)
    # 密码的定位
    Browser.find_element_by_xpath("/html/body/app-root/login-component/div/div[2]/div[1]/div/input").clear()
    Browser.find_element_by_xpath("/html/body/app-root/login-component/div/div[2]/div[1]/div/input").send_keys("111111")
    # 点击登录
    Browser.find_element_by_xpath("/html/body/app-root/login-component/div/div[2]/div[2]/button").click()

    time.sleep(1)
    # Browser.get(url)
    # logging.info(Browser.page_source)
    login_status = Browser.find_element_by_xpath("/html/body/app-root/login-component/div/div[2]/div[1]/p[1]").text

    logging.info(login_status)
    if login_status == "管理员密码错误":
        result = True
    else:
        result = False

    time.sleep(1)
    # 关闭浏览器
    Browser.quit()

    return result


class TestLedMethods(unittest.TestCase):

    def test_000_logging_init(self):
        print("test_000_logging_init")
        self.assertTrue(logging_init())

    def test_001_enter_error_passwd(self):
        print("enter_error_passwd")
        self.assertTrue(enter_error_passwd())

    # def test_002_repeat_setbright(self):
    #     print("test_02repeat_setbright")
    #     dev = ["0110012157", "0110012184"]
    #     self.assertTrue(start_repeat_setbright(dev, 100))
    #
    # def test_003_repeat_settemperature(self):
    #     print("test_03repeat_settemperature")
    #     dev = ["011001215b"]
    #     self.assertTrue(start_repeat_settemperature(dev, 1000))


if __name__ == '__main__':
    unittest.main()
