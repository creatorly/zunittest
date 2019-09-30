#!/usr/bin/python

import requests
import functools
import time
import os
import logging
import json
import unittest
import uuid


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


def get_dev_status(starttime, dev, status, setvalue):
    url = 'http://10.216.4.161:8081/v1/data/query/devMac'
    payload = {
       "startTime": "1536517559",
       "endTime": "",
       "devId": "0110012159",
       "prodTypeId": "8grteg3l",
       "metrics": ["light_state.power"]
    }
    headers = {'GATEWAY-VALIDATE': 'kLSIUlsSLILEKXasAAALIELKFJCKSILidksKALSIDKCKAKSIDKOA',
               'content-type': 'application/json'}

    for i in range(5):
        time.sleep(1)
        payload["devId"] = dev
        payload["startTime"] = str(starttime)
        payload["metrics"][0] = status

        logging.info(payload)
        result = requests.post(url, data=json.dumps(payload), headers=headers, timeout=(5, 5))
        logging.info(result.text)
        if result.status_code == 200:
            msg = json.loads(result.text)
            length = len(msg["data"][0]["dps"])
            if length:
                resp_value = msg["data"][0]["dps"][length - 1]["value"]
                print(resp_value)
                if str(setvalue) == resp_value:
                    return True
                else:
                    continue
            else:
                continue
        else:
            continue

    return False


def start_repeat_setpower(devlist, max_count):
    payload = {
        "msgType": "DEVICE_CONTROL",
        "devId": "",
        "prodTypeId":   "8grteg3l",
        "time": "2018-05-14 10:10:10",
        "sno": "789",
        "attribute": "light_power",
        "command": "set_power",
        "data": [{
            "k": "power",
            "v": "0"
        }]
    }

    i = 0
    power_value = 0

    while i < max_count:
        for dev in devlist:
            payload["devId"] = dev
            payload["sno"] = str(uuid.uuid1())
            payload["data"][0]["v"] = str(power_value)
            logging.info(payload)
            result = requests.post(server.control_url, data=json.dumps(payload), headers=server.control_headers, timeout=(5, 5))
            logging.info(result.text)
            if result.status_code == 200:
                msg = json.loads(result.text)
                if 200 == msg["code"]:
                    continue
                    # if True == get_dev_status(int(time.time()), dev, "light_state.power", power_value):
                    #     continue
                    # else:
                    #     return False
                else:
                    return False
            else:
                return False

        i += 1
        logging.info("test_count:%d", i)
        if 0 == power_value:
            power_value = 1
        else:
            power_value = 0

        time.sleep(3)

    return True


def start_repeat_setbright(devlist, max_bright):
    payload = {
        "msgType": "DEVICE_CONTROL",
        "devId": "",
        "prodTypeId":   "8grteg3l",
        "time": "2018-05-14 10:10:10",
        "sno": "789",
        "attribute": "light_bright",
        "command": "set_bright",
        "data": [{
            "k": "bright",
            "v": "0"
        }]
    }

    bright_value = 1

    while bright_value < max_bright:
        for dev in devlist:
            payload["devId"] = dev
            payload["sno"] = str(uuid.uuid1())
            payload["data"][0]["v"] = str(bright_value)

            logging.info(payload)
            result = requests.post(server.control_url, data=json.dumps(payload), headers=server.control_headers, timeout=(5, 5))
            logging.info(result.text)
            if result.status_code == 200:
                msg = json.loads(result.text)
                if 200 == msg["code"]:
                    continue
                else:
                    return False
            else:
                return False

        logging.info("bright_value:%d", bright_value)
        bright_value += 5

        time.sleep(3)

    return True


def start_repeat_settemperature(devlist, max_temperature):
    payload = {
        "msgType": "DEVICE_CONTROL",
        "devId": "",
        "prodTypeId":   "8grteg3l",
        "time": "2018-05-14 10:10:10",
        "sno": "789",
        "attribute": "light_temperature",
        "command": "set_temperature",
        "data": [{
            "k": "temperature",
            "v": "0"
        }]
    }

    temperature_value = 0

    while temperature_value < max_temperature:
        for dev in devlist:
            payload["devId"] = dev
            payload["sno"] = str(uuid.uuid1())
            payload["data"][0]["v"] = str(temperature_value)

            logging.info(payload)
            result = requests.post(server.control_url, data=json.dumps(payload), headers=server.control_headers, timeout=(5, 5))
            logging.info(result.text)
            if result.status_code == 200:
                msg = json.loads(result.text)
                if 200 == msg["code"]:
                    continue
                else:
                    return False
            else:
                return False

        logging.info("temperature_value:%d", temperature_value)
        temperature_value += 10

        time.sleep(3)

    return True


class TestLedMethods(unittest.TestCase):

    def test_000_logging_init(self):
        print("test_000_logging_init")
        self.assertTrue(logging_init())

    def test_001_repeat_setpower(self):
        print("test_01repeat_setpower")
        dev = ["011001215b"]
        self.assertTrue(start_repeat_setpower(dev, 1000))

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
