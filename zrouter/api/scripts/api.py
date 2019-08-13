#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2019/06/26
# Describe：动态api测试，表示ooutput的json是变化的，所以post得到的json和output里面的json内容只要节点名称一致即判断通过

import logging
import requests
import json
import json5
import base64
import time
import configparser
import sys
import shutil

sys.path.append("../../..")
import zutils.zexcel
import zrouter.api.scripts.utils_login


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
    config.read("../conf/api.conf", encoding="utf-8")
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

    if config.has_option("test", test.name + "_modules"):
        test.modules = config.get("test", test.name + "_modules").split(",")
    else:
        print("miss modules")
        exit()

    server.headers = {'content-type': 'application/json'}
    test.date = time.strftime("%Y/%m/%d", time.localtime())
    test.total_num = 0
    test.pass_num = 0
    test.fail_num = 0
    test.output_file = time.strftime("%Y%m%d_%H%M%S", time.localtime()) + "_api_test"
    excel.row_point = 0


def update_json5():
    # update status
    output_file = "../output_json/static/status.json5"
    shutil.copyfile(output_file, "../output_json/static/status.backup")

    with open(output_file, 'r', encoding="utf8") as load_f:
        output_dict = json5.loads(load_f.read())

    output_dict["test_001_get_board"][0]["data"][0]["result"]["mac"] = test.mac
    output_dict["test_001_get_board"][0]["data"][0]["result"]["firmware_ver"] = test.version
    output_dict["test_001_get_board"][0]["data"][0]["result"]["name"] = test.project

    with open(output_file, 'w+', encoding="utf8") as load_f:
        json.dump(output_dict, load_f)

    # update wireless
    input_file = "../input_json/static/wireless.json5"
    output_file = "../output_json/static/wireless.json5"
    shutil.copyfile(input_file, "../input_json/static/wireless.backup")
    shutil.copyfile(output_file, "../output_json/static/wireless.backup")

    with open(input_file, 'r', encoding="utf8") as load_f:
        input_dict = json5.loads(load_f.read())
    with open(output_file, 'r', encoding="utf8") as load_f:
        output_dict = json5.loads(load_f.read())

    sn = test.mac.split(":")
    new_str = "ZHOME_" + sn[4] + sn[5]
    input_dict["test_003_reset_wireless"][0]["param"]["params"][0]["param"]["w2"]["ssid"] = new_str
    output_dict["test_001_get_wireless"][0]["data"][0]["result"]["w2"]["ssid"] = new_str
    new_str = "ZHOME_" + sn[4] + sn[5] + "_5G"
    input_dict["test_003_reset_wireless"][0]["param"]["params"][0]["param"]["w5"]["ssid"] = new_str
    output_dict["test_001_get_wireless"][0]["data"][0]["result"]["w5"]["ssid"] = new_str

    with open(input_file, 'w+', encoding="utf8") as load_f:
        json.dump(input_dict, load_f)
    with open(output_file, 'w+', encoding="utf8") as load_f:
        json.dump(output_dict, load_f)

    logging.info("json5更新完成...")
    print("json5更新完成...")


def recovery_json5():
    # recovery status
    output_file = "../output_json/static/status.json5"
    shutil.move("../output_json/static/status.backup", output_file)

    # recovery wireless
    input_file = "../input_json/static/wireless.json5"
    output_file = "../output_json/static/wireless.json5"
    shutil.move("../input_json/static/wireless.backup", input_file)
    shutil.move("../output_json/static/wireless.backup", output_file)

    logging.info("json5恢复完成...")
    print("json5恢复完成...")


def logging_init():
    logging.basicConfig(
        filename="../results/" + test.output_file + ".log",  # 指定输出的文件
        level=logging.INFO,
        format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    return True


def excel_init():
    excel.excel_fd = zutils.zexcel.excel_init()
    if test.name == "static":
        excel.sheet_fd = zutils.zexcel.sheet_init(excel.excel_fd, "静态API测试结果")
    elif test.name == "dynamic":
        excel.sheet_fd = zutils.zexcel.sheet_init(excel.excel_fd, "动态API测试结果")
    # 从第二行开始写入
    excel.row_point = 1


def test_json_init(module_name):
    check_name = "test_"
    # 获取所有的测试名称及请求内容
    input_file = "../input_json/" + test.name + "/" + module_name + ".json5"
    output_file = "../output_json/" + test.name + "/" + module_name + ".json5"
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
    excel.sheet_fd.write(excel.row_point, zutils.zexcel.CASE_NAME_COL, module_name.capitalize() + "TestCase",
                         style=zutils.zexcel.set_style(zutils.zexcel.BLACK, 280, bold=False, align='', pattern_color='sky_blue'))
    excel.module_info[module_name] = {}
    excel.module_info[module_name]["row"] = excel.row_point
    excel.module_info[module_name]["count"] = 0
    excel.module_info[module_name]["pass"] = 0
    excel.module_info[module_name]["fail"] = 0


def comp_json_key(src, dst):
    for key in dst:
        if src.__contains__(key):
            if type(dst[key]) is dict:
                if not comp_json_key(src[key], dst[key]):
                    return False
            elif type(dst[key]) is list:
                i = 0
                while i < len(dst[key]):
                    if type(dst[key][i]) is dict or type(dst[key][i]) is list:
                        if not comp_json_key(src[key][i], dst[key][i]):
                            return False
                    else:
                        if src[key][i] != dst[key][i]:
                            return False
                    i += 1
            else:
                continue
        else:
            print("src don't have", key)
            logging.info("src don't have %s", key)
            return False

    return True


def run_test_case(module_name):
    # 写excel表,test case的头部
    test_top_write(module_name)
    print("run", module)

    for key in server.input_dict:
        # 填写测试名称到excel的第一列
        print(key)
        excel.row_point += 1
        excel.sheet_fd.write(excel.row_point, zutils.zexcel.CASE_NAME_COL, key,
                             style=zutils.zexcel.set_style(zutils.zexcel.BLACK, 240, bold=False, align=''))
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
                logging.info("%s src:%s", key, server.output_dict[key][request_i])
                msg = json.loads(resp_data.text)

                if test.name == "static":
                    # 判断返回的数据与output_json里面的数据是否一致
                    if msg != server.output_dict[key][request_i]:
                        request_result = False
                    else:
                        request_result = True
                elif test.name == "dynamic":
                    # 判断返回的数据与output_json里面的是结构是否一致
                    if not comp_json_key(msg, server.output_dict[key][request_i]):
                        request_result = False
                    else:
                        request_result = True

            request_i += 1

        # 填写测试结果到excel的第二列
        if request_result:
            logging.info("pass")
            print("pass")
            excel.sheet_fd.write(excel.row_point, zutils.zexcel.CASE_RESULT_COL, "pass",
                                 style=zutils.zexcel.set_style(zutils.zexcel.GREEN, 240, bold=False, align=''))
            excel.module_info[module_name]["pass"] += 1
            test.pass_num += 1
        else:
            logging.info("fail")
            print("fail")
            excel.sheet_fd.write(excel.row_point, zutils.zexcel.CASE_RESULT_COL, "fail",
                                 style=zutils.zexcel.set_style(zutils.zexcel.RED, 240, bold=False, align=''))
            excel.module_info[module_name]["fail"] += 1
            test.fail_num += 1

    return True


def test_end():
    # 将统计的count pass fail写入excel
    test.total_num = test.pass_num + test.fail_num
    for key in excel.module_info:
        excel.sheet_fd.write(excel.module_info[key]["row"], zutils.zexcel.COUNT_COL, excel.module_info[key]["count"],
                             style=zutils.zexcel.set_style(zutils.zexcel.RED, 240, bold=False, align=''))
        excel.sheet_fd.write(excel.module_info[key]["row"], zutils.zexcel.PASS_COL, excel.module_info[key]["pass"],
                             style=zutils.zexcel.set_style(zutils.zexcel.RED, 240, bold=False, align=''))
        excel.sheet_fd.write(excel.module_info[key]["row"], zutils.zexcel.FAIL_COL, excel.module_info[key]["fail"],
                             style=zutils.zexcel.set_style(zutils.zexcel.RED, 240, bold=False, align=''))

    excel.sheet_fd.write(zutils.zexcel.PROJECT_ROW, zutils.zexcel.PROJECT_COL + 1, test.project,
                         style=zutils.zexcel.set_style(zutils.zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zutils.zexcel.VERSION_ROW, zutils.zexcel.VERSION_COL + 1, test.version,
                         style=zutils.zexcel.set_style(zutils.zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zutils.zexcel.MAC_ROW, zutils.zexcel.MAC_COL + 1, test.mac,
                         style=zutils.zexcel.set_style(zutils.zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zutils.zexcel.DATA_ROW, zutils.zexcel.DATA_COL + 1, test.date,
                         style=zutils.zexcel.set_style(zutils.zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zutils.zexcel.TOTAL_ROW, zutils.zexcel.TOTAL_COL + 1, test.total_num,
                         style=zutils.zexcel.set_style(zutils.zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zutils.zexcel.TOTAL_PASS_ROW, zutils.zexcel.TOTAL_PASS_COL + 1, test.pass_num,
                         style=zutils.zexcel.set_style(zutils.zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zutils.zexcel.TOTAL_FAIL_ROW, zutils.zexcel.TOTAL_FAIL_COL + 1, test.fail_num,
                         style=zutils.zexcel.set_style(zutils.zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))

    filename = "../results/" + test.output_file + ".xls"
    excel.excel_fd.save(filename)  # 保存xls
    print("test end!")
    logging.info("test end!")
    exit()


if __name__ == '__main__':
    if 2 != len(sys.argv) or (sys.argv[1] != 'static' and sys.argv[1] != 'dynamic'):
        print("please enter static/dynamic")
        exit()
    else:
        test.name = sys.argv[1]

    data_init()
    logging_init()
    update_json5()
    excel_init()
    print("test start...")
    logging.info("test start...")

    server.sid = zrouter.api.scripts.utils_login.get_sid(server.url, server.headers, server.password)
    if not server.sid:
        print("login fail")
        logging.error("login fail")
        test_end()

    for module in test.modules:
        if not test_json_init(module):
            logging.error("json init error")
            test_end()

        run_test_case(module)

    recovery_json5()
    test_end()
