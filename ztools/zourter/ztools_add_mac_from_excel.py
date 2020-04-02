#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2019/11/19
# Describe：


import requests
import logging
import os
import time
import json
import xlrd


def logging_init():
    # 创建logger，如果参数为空则返回root logger
    logger = logging.getLogger("")
    logger.setLevel(logging.INFO)  # 设置logger日志等级

    # 创建handler
    output_file = time.strftime("%Y%m%d_%H%M%S", time.localtime()) + "_add_mac"
    log_file = os.path.join(os.path.dirname(__file__) + output_file + ".log")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    ch = logging.StreamHandler()

    # 设置输出日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"
    )

    # 为handler指定输出格式，注意大小写
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # 为logger添加的日志处理器
    logger.addHandler(fh)
    logger.addHandler(ch)

    return True


def read_mac(excel_name):
    excel_fd = xlrd.open_workbook(excel_name)
    logging.info("sheet_names: %s", excel_fd.sheet_names())  # 获取所有sheet名字
    logging.info("sheets: %d", excel_fd.nsheets)  # 获取sheet数量
    excel_sheet = excel_fd.sheet_by_index(0)  # 第一个表
    mac_list = excel_sheet.col_values(1)   # 第二列数据
    logging.info("mac_list: %s", mac_list)

    return mac_list


if __name__ == '__main__':
    logging_init()

    gw_url = 'https://gw.zihome.com/link-assist-handle/v1/business/gateway/add'
    tlink_url = 'https://tlink.zihome.com/link-assist-handle/v1/business/gateway/add'
    payload = {
        "macs": ["001122334455"],
        "supplier": "zihome",
        "hardwareModel": "ZHA0103",
        "email": "liny5@ziroom.com"
    }
    headers = {'content-type': 'application/json'}

    i = 1  # 第一行不为MAC地址
    gw_pass = 0
    tlink_pass = 0

    mac_list = read_mac("自如SN-MAC.xlsx")

    while i < len(mac_list):
        start_mac = mac_list[i]
        payload["macs"][0] = start_mac.upper()
        logging.info("gw_url: %s, payload: %s", gw_url, payload)
        result = requests.post(gw_url, data=json.dumps(payload), headers=headers, timeout=(5, 5))
        logging.info("result: %s", result.text)
        if result.status_code == 200:
            msg = json.loads(result.text)
            if (200 == msg["code"]) and ("success" == msg["message"]):
                gw_pass += 1
                logging.info("正式环境 mac: %s, add ok", start_mac)
            else:
                logging.info("正式环境 mac: %s, add fail", start_mac)

        logging.info("tlink_url: %s, payload: %s", tlink_url, payload)
        result = requests.post(tlink_url, data=json.dumps(payload), headers=headers, timeout=(5, 5))
        logging.info("result: %s", result.text)
        if result.status_code == 200:
            msg = json.loads(result.text)
            if (200 == msg["code"]) and ("success" == msg["message"]):
                tlink_pass += 1
                logging.info("测试环境 mac: %s, add ok", start_mac)
            else:
                logging.info("测试环境 mac: %s, add fail", start_mac)

        int_mac = int(start_mac, base=16)
        int_mac += 2
        start_mac = str(hex(int_mac))[2:]

        i += 1
        time.sleep(0.2)

    logging.info("正式环境添加成功%d台", gw_pass)
    logging.info("测试环境添加成功%d台", tlink_pass)

