import requests
import functools
import time
import os
import uuid
import random
import logging
import json
import unittest


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


def start_addpasswd_test(devlist, max_count):
    payload = {
        "msgType": "DEVICE_CONTROL",
        "devId": "F206E34470A0C440",
        "prodTypeId": "YG0002",
        "time": "2018-05-14 10:10:10",
        "sno": "789",
        "command": "add_password",
        "attribute": "lock_password",
        "data": [{
            "k": "index",
            "v": "0"
        }, {
            "k": "content",
            "v": "12345678"
        }]
    }

    i = 0

    while i < max_count:
        for dev in devlist:
            payload["devId"] = dev
            payload["sno"] = str(uuid.uuid1())
            payload["data"][0]["v"] = str(i)
            payload["data"][1]["v"] = random.randint(000000, 9999999)
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

        i += 1
        logging.info("test_count:%d", i)

        time.sleep(3)

    return True


class TestLockMethods(unittest.TestCase):

    def test_000_logging_init(self):
        print("test_000_logging_init")
        self.assertTrue(logging_init())

    def test_001_addpasswd(self):
        print("test_001_addpasswd")
        dev = ["F206E34470A0C440"]
        self.assertTrue(start_addpasswd_test(dev, 100))


if __name__ == '__main__':
    unittest.main()
