#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2019/07/05
# Describe：登录api，获取sid

import logging
import requests
import json


def get_sid(request_url, request_heads, request_passwd):
    request_data = {
        "ver": "v1",
        "sid": "00000000000000000000000000000000",
        "method": "login",
        "param": {
            "msg_id": 11111,
            "params": [{
                "module": "login",
                "api": "login",
                "param": {
                    "password": str(request_passwd)
                }
            }]
        }
    }

    logging.info(request_data)
    resp_data = requests.post(request_url, data=json.dumps(request_data), headers=request_heads)
    logging.info(resp_data.text)
    if resp_data.status_code == 200:
        msg = json.loads(resp_data.text)
        if 0 == msg["errcode"]:
            if msg["data"][0]["result"].__contains__("sid"):
                return msg["data"][0]["result"]["sid"]
        else:
            return False
    else:
        return False


if __name__ == '__main__':
    print("请开始你的表演")
