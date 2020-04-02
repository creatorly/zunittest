#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2020/04/02
# Describe：通过服务器进行控制命令压力测试

import logging
import requests
import json
import json5
import time
import configparser
import sys
import uuid
import os
import signal

sys.path.append("../../../..")
from zutils import zexcel


class ServerInfo(object):
    host = ''
    headers = {}
    input_dict = {}
    output_dict = {}
    wait_time = 1
    sno = "123"


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


def data_init(module_name):
    # 获取配置文件信息
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__) + '/../conf/' + module_name + '.conf')
    config.read(config_path, encoding="utf-8")

    if config.has_option("link", "host"):
        server.host = config.get("link", "host")
    else:
        print("miss host")
        exit()

    config_path = os.path.join(os.path.dirname(__file__) + '/../../../zrouter.conf')
    config.read(config_path, encoding="utf-8")
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
    log_file = os.path.join(os.path.dirname(__file__) + "/../results/" + test.output_file + ".log")
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
    sheet_name = module_name + "测试结果"
    excel.sheet_fd = zexcel.sheet_init(excel.excel_fd, sheet_name)

    # 写设备信息
    excel.sheet_fd.write(zexcel.PROJECT_ROW, zexcel.PROJECT_COL + 1, test.project,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zexcel.VERSION_ROW, zexcel.VERSION_COL + 1, test.version,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zexcel.MAC_ROW, zexcel.MAC_COL + 1, test.mac,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zexcel.DATE_ROW, zexcel.DATE_COL + 1, test.date,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))

    filename = os.path.join(os.path.dirname(__file__) + "/../results/" + test.output_file + ".xls")
    excel.excel_fd.save(filename)  # 保存xls

    # 从第二行开始写入
    excel.row_point = 1


# 用于测试的设备版本、mac等信息是不一样，有些api需要跟新对应的信息
def test_json_update():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__) + '/../conf/control_stress.conf')
    config.read(config_path, encoding="utf-8")

    if config.has_option("link", "devId"):
        new_str = config.get("link", "devId")
        server.input_dict["test_control_stress"][0]["control"]["devId"] = new_str
        server.input_dict["test_control_stress"][0]["control"]["devUuid"] = new_str
        server.input_dict["test_control_stress"][2]["control"]["devId"] = new_str
        server.input_dict["test_control_stress"][2]["control"]["devUuid"] = new_str
        server.output_dict["test_control_stress"][1]["part_same"]["data"]["devId"] = new_str
        server.output_dict["test_control_stress"][1]["part_same"]["data"]["devUuid"] = new_str
        server.output_dict["test_control_stress"][3]["part_same"]["data"]["devId"] = new_str
        server.output_dict["test_control_stress"][3]["part_same"]["data"]["devUuid"] = new_str

    else:
        print("miss devId")
        exit()

    if config.has_option("link", "prodTypeId"):
        new_str = config.get("link", "prodTypeId")
        server.input_dict["test_control_stress"][0]["control"]["prodTypeId"] = new_str
        server.input_dict["test_control_stress"][2]["control"]["prodTypeId"] = new_str
        server.output_dict["test_control_stress"][1]["part_same"]["data"]["prodTypeId"] = new_str
        server.output_dict["test_control_stress"][3]["part_same"]["data"]["prodTypeId"] = new_str
    else:
        print("miss prodTypeId")
        exit()
    # print(server.input_dict)
    # print(server.output_dict)
    logging.info("json5更新完成...")


def test_json_init(module_name):
    check_name = "test_"
    # 获取所有的测试名称及请求内容
    input_file = os.path.join(os.path.dirname(__file__) + "/../input_json/" + test.name + "/" + module_name + ".json5")
    output_file = os.path.join(os.path.dirname(__file__) + "/../output_json/" + test.name + "/" + module_name + ".json5")
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

    test_json_update()

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


# src是否包含dst,内容也要相等
def comp_json_value(src, dst):
    # logging.info("src %s", src)
    # logging.info("dst %s", dst)
    for key in dst:
        logging.info("key %s", key)
        if src.__contains__(key):
            if type(dst[key]) is dict:
                if not comp_json_value(src[key], dst[key]):
                    return False
            elif type(dst[key]) is list:
                i = 0
                while i < len(dst[key]):
                    if type(dst[key][i]) is dict or type(dst[key][i]) is list:
                        if not comp_json_value(src[key][i], dst[key][i]):
                            return False
                    else:
                        if src[key][i] != dst[key][i]:
                            return False
                    i += 1
            else:
                # logging.info("src %s", src[key])
                # logging.info("dst %s", dst[key])
                if src[key] != dst[key]:
                    return False
                else:
                    continue
        else:
            logging.info("src don't have %s", key)
            return False

    return True


def run_test_case(module_name, count_max):
    # 写excel表,test case的头部
    test_top_write(module_name)
    test_count = 0

    while test_count <= count_max:
        test_count += 1
        for key in server.input_dict:
            # 填写测试名称到excel的第一列
            excel.row_point += 1
            excel.sheet_fd.write(excel.row_point, zexcel.CASE_NAME_COL, key,
                                 style=zexcel.set_style(zexcel.BLACK, 240, bold=False, align=''))
            excel.module_info[module_name]["count"] += 1

            # 一个case里面可能会有多个请求
            request_i = 0
            request_result = True
            net_result = True
            while request_i < len(server.input_dict[key]):
                try:
                    # 有url，说明要访问tlink
                    if server.input_dict[key][request_i].__contains__("url"):
                        request_url = server.host + server.input_dict[key][request_i]["url"]
                        request_head = {'content-type': 'application/json'}
                        request_data = {}
                        # 有head说明需要设置头部
                        if server.input_dict[key][request_i].__contains__("head_1") and \
                                server.input_dict[key][request_i].__contains__("head_2"):
                            request_head = {
                                server.input_dict[key][request_i]["head_1"]: server.input_dict[key][request_i]["head_2"],
                                'content-type': 'application/json'}

                        # 控制事件
                        if server.input_dict[key][request_i].__contains__("control"):
                            server.wait_time = 5
                            request_data = server.input_dict[key][request_i]["control"]
                            server.sno = str(uuid.uuid1())
                            request_data["sno"] = server.sno
                        # 控制相应事件（前提要有控制，否则sno会错误）
                        elif server.input_dict[key][request_i].__contains__("control_resp"):
                            server.wait_time = 1
                            request_data = server.input_dict[key][request_i]["control_resp"]
                            request_data["sno"] = server.sno
                        else:
                            server.wait_time = 1

                        logging.info("request_url:%s", request_url)
                        logging.info("%s send:%s", key, request_data)

                        resp_data = requests.post(request_url, data=json.dumps(request_data), headers=request_head,
                                                  timeout=5)
                        logging.info("%s recv:%s", key, resp_data.text)
                        if resp_data.status_code == 200:
                            msg = json.loads(resp_data.text)
                            if msg["code"] == 200:
                                # 全部相等
                                if server.output_dict[key][request_i].__contains__("total_same"):
                                    if msg != server.output_dict[key][request_i]["total_same"]:
                                        request_result = False
                                # 部分相等
                                elif server.output_dict[key][request_i].__contains__("part_same"):
                                    if not comp_json_value(msg, server.output_dict[key][request_i]["part_same"]):
                                        request_result = False
                            else:
                                net_result = False
                        else:
                            net_result = False

                    else:
                        server.wait_time = 1

                except Exception as e:
                    logging.info("---异常---：", e)
                    request_result = False
                    net_result = False

                request_i += 1
                time.sleep(server.wait_time)

            # 填写测试结果到excel的第二列
            if net_result:
                if request_result:
                    logging.info("%s: pass", key)
                    excel.sheet_fd.write(excel.row_point, zexcel.CASE_RESULT_COL, "pass",
                                         style=zexcel.set_style(zexcel.GREEN, 240, bold=False, align=''))
                    excel.module_info[module_name]["pass"] += 1
                    test.pass_num += 1
                else:
                    logging.info("%s: fail", key)
                    excel.sheet_fd.write(excel.row_point, zexcel.CASE_RESULT_COL, "fail",
                                         style=zexcel.set_style(zexcel.RED, 240, bold=False, align=''))
                    excel.module_info[module_name]["fail"] += 1
                    test.fail_num += 1
            else:
                logging.info("%s: fail", key)
                excel.sheet_fd.write(excel.row_point, zexcel.CASE_RESULT_COL, "net fail",
                                     style=zexcel.set_style(zexcel.RED, 240, bold=False, align=''))
                excel.module_info[module_name]["fail"] += 1
                test.fail_num += 1

            filename = os.path.join(os.path.dirname(__file__) + "/../results/" + test.output_file + ".xls")
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

    filename = os.path.join(os.path.dirname(__file__) + "/../results/" + test.output_file + ".xls")
    excel.excel_fd.save(filename)  # 保存xls
    logging.info("test end!")
    exit()


def signal_handler(signal_num, frame):
    print("signal_num", signal_num)
    test_end()


if __name__ == '__main__':

    for sig in [signal.SIGABRT, signal.SIGFPE, signal.SIGILL, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM]:
        signal.signal(sig, signal_handler)

    module = "control_stress"

    test_start(module)

    if not test_json_init(module):
        logging.error("json init error")
        test_end()

    run_test_case(module, 100)

    test_end()

