#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2019/06/26
# Describe：静态api测试，表示output的json是固定的，所以post得到的json和output里面的json内容完全匹配才通过

import logging
import requests
import json
import json5
import base64
import sys
import time
import configparser
sys.path.append("../../..")
import zutils.zexcel


class ServerInfo(object):
    url = ''
    headers = {}
    sid = ''
    password = ''
    input_dict = {}
    output_dict = {}


class TestInfo(object):
    modules = []
    start_time = ''
    output_file = ''


class ExcelInfo(object):
    excel_fd = 0
    sheet_fd = 0
    row_point = 0
    # {"row": 0, "count": 0, "pass": 0, "fail": 0}
    module_info = {}


server = ServerInfo
test = TestInfo
excel = ExcelInfo


def data_init():
    # 获取配置文件信息
    config = configparser.ConfigParser()
    config.read("../conf/static_api.conf", encoding="utf-8")
    if config.has_option("server", "host"):
        server.url = config.get("server", "host")
    if config.has_option("server", "passwd"):
        server.password = base64.b64encode(bytes(config.get("server", "passwd"), encoding='utf8'))
    if config.has_option("test", "modules"):
        test.modules = config.get("test", "modules").split(",")
    server.headers = {'content-type': 'application/json'}
    test.output_file = time.strftime("%Y%m%d_%H%M%S", time.localtime()) + "_api_test"
    excel.row_point = 0


def logging_init():
    logging.basicConfig(
        filename="../results/" + test.output_file + ".log",  # 指定输出的文件
        level=logging.INFO,
        format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    return True


def excel_init():
    excel.excel_fd = zutils.zexcel.excel_init()
    excel.sheet_fd = zutils.zexcel.sheet_init(excel.excel_fd, "静态API测试结果")
    # 从第二行开始写入
    excel.row_point = 1


def test_json_init(module_name):
    check_name = "test_"
    # 获取所有的测试名称及请求内容
    input_file = "../input_json/static/" + module_name + ".json5"
    output_file = "../output_json/static/" + module_name + ".json5"
    with open(input_file, 'r', encoding="utf8") as load_f:
        server.input_dict = json5.loads(load_f.read())

    for key in server.input_dict:
        # 判断key是否以"test_"开始
        if not str(key).startswith(check_name):
            logging.error("input_dict not start with test_")
            return False

    with open(output_file, 'r', encoding="utf8") as load_f:
        server.output_dict = json5.loads(load_f.read())

    for key in server.output_dict:
        # 判断key是否以"test_"开始
        if not str(key).startswith(check_name):
            logging.error("output_dict not start with test_")
            return False

    # 判断input和output的内容是否对应
    if len(server.input_dict) == len(server.output_dict):
        for key in server.input_dict:
            if key in server.output_dict:
                logging.info("test case:%s", key)
            else:
                logging.error("input_json is different with output_json")
                return False
    else:
        return False

    return True


def test_top_write(module_name):
    excel.row_point += 1
    excel.sheet_fd.write(excel.row_point, 0, module_name.capitalize() + "TestCase",
                         style=zutils.zexcel.set_style(0x7FFF, 280, bold=False, align='', pattern_color='sky_blue'))
    excel.module_info[module_name] = {}
    excel.module_info[module_name]["row"] = excel.row_point
    excel.module_info[module_name]["count"] = 0
    excel.module_info[module_name]["pass"] = 0
    excel.module_info[module_name]["fail"] = 0


def test_000_login():
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
                    "password": str(server.password.decode("utf-8"))
                }
            }]
        }
    }
    module_name = "Login"
    test_top_write(module_name)

    excel.row_point += 1
    excel.sheet_fd.write(excel.row_point, 0, "test_000_login",
                         style=zutils.zexcel.set_style(0x7FFF, 240, bold=False, align=''))
    excel.module_info[module_name]["count"] += 1

    logging.info(request_data)
    resp_data = requests.post(server.url, data=json.dumps(request_data), headers=server.headers)
    logging.info(resp_data.text)
    if resp_data.status_code == 200:
        msg = json.loads(resp_data.text)
        if 0 == msg["errcode"]:
            server.sid = msg["data"][0]["result"]["sid"]
            excel.sheet_fd.write(excel.row_point, 1, "pass",
                                 style=zutils.zexcel.set_style(0x11, 240, bold=False, align=''))
            excel.module_info[module_name]["pass"] += 1
            return True
        else:
            excel.sheet_fd.write(excel.row_point, 1, "fail",
                                 style=zutils.zexcel.set_style(0x0A, 240, bold=False, align=''))
            excel.module_info[module_name]["fail"] += 1
            return False
    else:
        excel.sheet_fd.write(excel.row_point, 1, "fail",
                             style=zutils.zexcel.set_style(0x0A, 240, bold=False, align=''))
        excel.module_info[module_name]["fail"] += 1
        return False


def run_test_case(module_name):
    # 写excel表,test case的头部
    test_top_write(module_name)
    print("run", module)

    for key in server.input_dict:
        # 填写测试名称到excel的第一列
        print(key)
        excel.row_point += 1
        excel.sheet_fd.write(excel.row_point, 0, key, style=zutils.zexcel.set_style(0x7FFF, 240, bold=False, align=''))
        excel.module_info[module_name]["count"] += 1

        # 一个case里面可能会有多个请求
        request_i = 0
        request_result = True
        while request_i < len(server.input_dict[key]):
            request_data = server.input_dict[key][request_i]
            request_data["sid"] = server.sid
            logging.info("%s send:%s", key, request_data)
            resp_data = requests.post(server.url, data=json.dumps(request_data), headers=server.headers)
            logging.info("%s recv:%s", key, resp_data.text)
            if resp_data.status_code == 200:
                msg = json.loads(resp_data.text)
                # 判断返回的数据与output_json里面的数据是否一致
                if msg != server.output_dict[key][request_i]:
                    request_result = False
            else:
                request_result = False

            request_i += 1

        # 填写测试结果到excel的第二列
        if request_result:
            logging.info("pass")
            print("pass")
            excel.sheet_fd.write(excel.row_point, 1, "pass",
                                 style=zutils.zexcel.set_style(0x11, 240, bold=False, align=''))
            excel.module_info[module_name]["pass"] += 1
        else:
            logging.info("fail")
            print("fail")
            excel.sheet_fd.write(excel.row_point, 1, "fail",
                                 style=zutils.zexcel.set_style(0x0A, 240, bold=False, align=''))
            excel.module_info[module_name]["fail"] += 1

    return True


def test_end():
    # 将统计的count pass fail写入excel
    for key in excel.module_info:
        excel.sheet_fd.write(excel.module_info[key]["row"], 2, excel.module_info[key]["count"],
                             style=zutils.zexcel.set_style(0x0A, 240, bold=False, align=''))
        excel.sheet_fd.write(excel.module_info[key]["row"], 3, excel.module_info[key]["pass"],
                             style=zutils.zexcel.set_style(0x0A, 240, bold=False, align=''))
        excel.sheet_fd.write(excel.module_info[key]["row"], 4, excel.module_info[key]["fail"],
                             style=zutils.zexcel.set_style(0x0A, 240, bold=False, align=''))

    filename = "../results/" + test.output_file + ".xls"
    excel.excel_fd.save(filename)  # 保存xls
    print("test end!")
    logging.info("test end!")
    exit()


if __name__ == '__main__':
    data_init()
    logging_init()
    excel_init()
    print("test start...")
    logging.info("test start...")

    if not test_000_login():
        logging.error("login fail")
        test_end()

    for module in test.modules:
        if not test_json_init(module):
            logging.error("json init error")
            test_end()

        run_test_case(module)

    test_end()
