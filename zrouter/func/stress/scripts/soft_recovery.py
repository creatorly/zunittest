#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2019/08/15
# Describe：wifi测试

import logging
import requests
import json
import json5
import base64
import time
import configparser
import sys
import pywifi
import signal
import os

sys.path.append("./../../../..")
from zutils import zexcel
from zrouter.api.scripts import utils_login
from zrouter.func.wifi.scripts import utils_wifi


CASE_COUNT_COL = 1
CASE_ETH_COL = 2
CASE_WIFI_COL = 3
CASE_TIME_COL = 4


class ServerInfo(object):
    url = ''
    headers = {}
    sid = ''
    password = ''
    input_dict = {}
    output_dict = {}


class TestInfo(object):
    project = ''
    version = ''
    mac = ''
    date = ''
    name = ''
    total_num = 0
    pass_num = 0
    fail_num = 0
    modules = []
    timeout = 50  # 50次get请求
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


def data_init(module_name):
    # 获取配置文件信息
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__) + './../../../zrouter.conf')
    config.read(config_path, encoding="utf-8")
    if config.has_option("server", "host"):
        server.url = config.get("server", "host")
    else:
        print("miss url")
        exit()

    if config.has_option("server", "passwd"):
        server.password = base64.b64encode(bytes(config.get("server", "passwd"), encoding='utf8')).decode("utf-8")
    else:
        print("miss passwd")
        exit()

    if config.has_option("test", "project"):
        test.project = config.get("test", "project")
    else:
        print("miss project")
        exit()

    if config.has_option("test", "version"):
        test.version = config.get("test", "version")
    else:
        print("miss version")
        exit()

    if config.has_option("test", "mac"):
        test.mac = config.get("test", "mac")
    else:
        print("miss version")
        exit()

    server.headers = {'content-type': 'application/json'}
    test.date = time.strftime("%Y/%m/%d", time.localtime())
    test.total_num = 0
    test.pass_num = 0
    test.fail_num = 0
    test.output_file = time.strftime("%Y%m%d_%H%M%S", time.localtime()) + "_" + module_name + "_test"
    excel.row_point = 0


def logging_init():
    # 创建logger，如果参数为空则返回root logger
    logger = logging.getLogger("")
    logger.setLevel(logging.INFO)  # 设置logger日志等级

    # 创建handler
    log_file = os.path.join(os.path.dirname(__file__) + "./../results/" + test.output_file + ".log")
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


def excel_init(module_name):
    excel.excel_fd = zexcel.excel_init()
    sheet_name = test.name + " " + module_name + "测试结果"
    excel.sheet_fd = zexcel.common_sheet_init(excel.excel_fd, sheet_name)
    # 从第二行开始写入
    excel.row_point = 1
    rows = ['', 'Count', 'Eth', 'Wifi', 'Time']
    for index, val in enumerate(rows):
        excel.sheet_fd.write(1, index, val, style=zexcel.set_style(zexcel.BLACK, 280, bold=True, pattern_color='gray25'))

    # 写设备信息
    excel.sheet_fd.write(zexcel.PROJECT_ROW, zexcel.PROJECT_COL + 1, test.project,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zexcel.VERSION_ROW, zexcel.VERSION_COL + 1, test.version,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zexcel.MAC_ROW, zexcel.MAC_COL + 1, test.mac,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zexcel.DATE_ROW, zexcel.DATE_COL + 1, test.date,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))

    filename = os.path.join(os.path.dirname(__file__) + "./../results/" + test.output_file + ".xls")
    excel.excel_fd.save(filename)  # 保存xls


def test_json_init(module_name):
    check_name = "test_"
    # 获取所有的测试名称及请求内容
    input_file = os.path.join(os.path.dirname(__file__) + "./../input_json/" + test.name + "/" + module_name + ".json5")
    output_file = os.path.join(os.path.dirname(__file__) + "./../output_json/" + test.name + "/" + module_name + ".json5")
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
    excel.sheet_fd.write(excel.row_point, zexcel.CASE_NAME_COL, module_name.capitalize() + "TestCase",
                         style=zexcel.set_style(zexcel.BLACK, 280, bold=False, align='', pattern_color='sky_blue'))
    excel.module_info[module_name] = {}
    excel.module_info[module_name]["row"] = excel.row_point
    excel.module_info[module_name]["count"] = 0
    excel.module_info[module_name]["pass"] = 0
    excel.module_info[module_name]["fail"] = 0


def requests_internet():
    try:
        result = requests.get("http://www.baidu.com", timeout=5)
        logging.info(result.status_code)
        if result.status_code == 200:
            time.sleep(2)
            result = requests.get("http://www.baidu.com", timeout=5)
            logging.info(result.status_code)
            if result.status_code == 200:
                return True
            else:
                return False
        else:
            return False
    except Exception as e:
        print("---异常---：", e)
        return False


def run_test_case(module_name, count_max):
    # 写excel表,test case的头部
    test_top_write(module_name)

    test_count = 1
    while test_count <= count_max:
        server.sid = utils_login.get_sid(server.url, server.headers, server.password)
        if not server.sid:
            logging.error("login fail")
            test_end()

        for key in server.input_dict:
            # 填写测试名称到excel的第一列
            excel.row_point += 1
            excel.sheet_fd.write(excel.row_point, zexcel.CASE_NAME_COL, key,
                                 style=zexcel.set_style(zexcel.BLACK, 240, bold=False, align=''))
            excel.module_info[module_name]["count"] += 1

            # 一个case里面可能会有多个请求
            request_i = 0
            request_result = True
            while request_i < len(server.input_dict[key]):
                try:
                    request_data = server.input_dict[key][request_i]
                    request_data["sid"] = server.sid
                    logging.info("%s send:%s", key, request_data)
                    resp_data = requests.post(server.url, data=json.dumps(request_data), headers=server.headers, timeout=5)
                    logging.info("%s recv:%s", key, resp_data.text)
                    if resp_data.status_code == 200:
                        logging.info("%s src:%s", key, server.output_dict[key][request_i])
                        msg = json.loads(resp_data.text)

                        # 判断返回的数据与output_json里面的数据是否一致
                        if msg != server.output_dict[key][request_i]:
                            request_result = False

                except Exception as e:
                    logging.info("---异常---：", e)
                    request_result = False

                request_i += 1
                time.sleep(1)

            # 填写测试结果到excel的第二列
            if request_result:
                logging.info("pass")
                excel.sheet_fd.write(excel.row_point, zexcel.CASE_RESULT_COL, "pass",
                                     style=zexcel.set_style(zexcel.GREEN, 240, bold=False, align=''))
                excel.module_info[module_name]["pass"] += 1
                test.pass_num += 1
            else:
                logging.info("fail")
                excel.sheet_fd.write(excel.row_point, zexcel.CASE_RESULT_COL, "fail",
                                     style=zexcel.set_style(zexcel.RED, 240, bold=False, align=''))
                excel.module_info[module_name]["fail"] += 1
                test.fail_num += 1

        # 填写测试次数
        excel.row_point += 1
        excel.sheet_fd.write(excel.row_point, CASE_COUNT_COL, test_count,
                             style=zexcel.set_style(zexcel.BLACK, 240, bold=False, align=''))
        excel.module_info[module_name]["count"] += 1

        wan_result = False
        i = 0
        while i < test.timeout:
            i += 1
            logging.info("ping count %s", i)
            time.sleep(2)
            wan_result = requests_internet()
            if wan_result:
                break

        if wan_result:
            logging.info("count %s pass", test_count)
            test.pass_num += 1
            excel.sheet_fd.write(excel.row_point, CASE_ETH_COL, "pass",
                                 style=zexcel.set_style(zexcel.GREEN, 240, bold=False, align=''))
            excel.module_info[module_name]["pass"] += 1
        else:
            logging.info("fail")
            break

        test_count += 1
        time.sleep(2)

        filename = os.path.join(os.path.dirname(__file__) + "./../results/" + test.output_file + ".xls")
        excel.excel_fd.save(filename)  # 保存xls

    return True


def test_start(module_name):
    data_init(module_name)
    logging_init()
    logging.info("test start...")
    excel_init(module_name)


def test_end():
    # 将统计的count pass fail写入excel
    test.total_num = test.pass_num + test.fail_num
    for key in excel.module_info:
        excel.sheet_fd.write(excel.module_info[key]["row"], zexcel.COUNT_COL, excel.module_info[key]["count"],
                             style=zexcel.set_style(zexcel.RED, 240, bold=False, align=''))
        excel.sheet_fd.write(excel.module_info[key]["row"], zexcel.PASS_COL, excel.module_info[key]["pass"],
                             style=zexcel.set_style(zexcel.RED, 240, bold=False, align=''))
        excel.sheet_fd.write(excel.module_info[key]["row"], zexcel.FAIL_COL, excel.module_info[key]["fail"],
                             style=zexcel.set_style(zexcel.RED, 240, bold=False, align=''))

    excel.sheet_fd.write(zexcel.TOTAL_ROW, zexcel.TOTAL_COL + 1, test.total_num,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zexcel.TOTAL_PASS_ROW, zexcel.TOTAL_PASS_COL + 1, test.pass_num,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zexcel.TOTAL_FAIL_ROW, zexcel.TOTAL_FAIL_COL + 1, test.fail_num,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))

    filename = os.path.join(os.path.dirname(__file__) + "./../results/" + test.output_file + ".xls")
    excel.excel_fd.save(filename)  # 保存xls
    logging.info("test end!")
    exit()


def signal_handler(signal_num, frame):
    print("signal_num", signal_num)
    test_end()


if __name__ == '__main__':

    for sig in [signal.SIGABRT, signal.SIGFPE, signal.SIGILL, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM]:
        signal.signal(sig, signal_handler)

    module = "soft_recovery"

    test_start(module)

    if not test_json_init(module):
        logging.error("json init error")
        test_end()

    run_test_case(module, 100)
    test_end()


