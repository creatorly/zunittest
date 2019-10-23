#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2019/08/15
# Describe：zgateway测试

import logging
import requests
import json
import json5
import time
import configparser
import sys
import paramiko
import uuid

sys.path.append("../../../..")
from zutils import zexcel
from zrouter.func.wifi.scripts import utils_wifi


class ServerInfo(object):
    url = ''
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
    zigbee_devId = "000d6f000b7ab1d3"
    zigbee_prodTypeId = "SmartPlug"
    ble_devId = "011001275a"
    ble_prodTypeId = "8grteg3l"


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
    config.read("../conf/zgateway.conf", encoding="utf-8")
    if config.has_option("link", "host"):
        server.url = config.get("link", "host")
    else:
        print("miss url")
        exit()

    config.read("../conf/zgateway.conf", encoding="utf-8")
    if config.has_option("link", "zigbee_devId"):
        test.zigbee_devId = config.get("link", "zigbee_devId")
    else:
        print("miss zigbee_devId")
        exit()

    config.read("../conf/zgateway.conf", encoding="utf-8")
    if config.has_option("link", "zigbee_prodTypeId"):
        test.zigbee_prodTypeId = config.get("link", "zigbee_prodTypeId")
    else:
        print("miss zigbee_prodTypeId")
        exit()

    config.read("../conf/zgateway.conf", encoding="utf-8")
    if config.has_option("link", "ble_devId"):
        test.ble_devId = config.get("link", "ble_devId")
    else:
        print("miss ble_devId")
        exit()

    config.read("../conf/zgateway.conf", encoding="utf-8")
    if config.has_option("link", "ble_prodTypeId"):
        test.ble_prodTypeId = config.get("link", "ble_prodTypeId")
    else:
        print("miss ble_prodTypeId")
        exit()

    config.read("../../../zrouter.conf", encoding="utf-8")
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
    test.output_file = time.strftime("%Y%m%d_%H%M%S", time.localtime()) + "_zgateway_test"
    excel.row_point = 0


def logging_init():
    # 创建logger，如果参数为空则返回root logger
    logger = logging.getLogger("")
    logger.setLevel(logging.INFO)  # 设置logger日志等级

    # 创建handler
    fh = logging.FileHandler("../results/" + test.output_file + ".log", encoding="utf-8")
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


def excel_init():
    excel.excel_fd = zexcel.excel_init()
    excel.sheet_fd = zexcel.sheet_init(excel.excel_fd, "Zgateway测试结果")
    # 从第二行开始写入
    excel.row_point = 1


# 用于测试的设备版本、mac等信息是不一样，有些api需要跟新对应的信息
def test_json_update():
    sn = test.mac.split(":")
    new_str = sn[0] + sn[1] + sn[2] + sn[3] + sn[4] + sn[5]
    server.input_dict["test_002_check_gateway_version"][0]["query"]["devId"] = new_str
    server.input_dict["test_003_check_iot_version"][2]["query"]["devId"] = new_str + "_S3GATEWAY"
    server.input_dict["test_003_check_iot_version"][3]["query"]["devId"] = new_str + "_LED2_4"
    server.input_dict["test_004_set_device_ssid"][0]["query"]["devId"] = new_str
    server.input_dict["test_004_set_device_ssid"][2]["query"]["data"][0]["v"] = "ZR_D" + sn[4] + sn[5]
    server.input_dict["test_004_set_device_ssid"][2]["query"]["data"][1]["v"] = "ZR_P" + sn[4] + sn[5]
    server.input_dict["test_004_set_device_ssid"][2]["query"]["devId"] = new_str

    server.input_dict["test_007_2.4G_connect"][20]["connect"]["devId"] = new_str + "_LED2_4"
    server.input_dict["test_007_2.4G_connect"][21]["query"]["devId"] = test.ble_devId
    server.input_dict["test_007_2.4G_connect"][21]["query"]["prodTypeId"] = test.ble_prodTypeId
    server.input_dict["test_008_2.4G_control"][0]["control"]["devId"] = test.ble_devId
    server.input_dict["test_008_2.4G_control"][0]["control"]["devUuid"] = test.ble_devId
    server.input_dict["test_008_2.4G_control"][0]["control"]["prodTypeId"] = test.ble_prodTypeId
    server.input_dict["test_009_2.4G_remove"][0]["control"]["devId"] = new_str + "_LED2_4"
    server.input_dict["test_009_2.4G_remove"][0]["control"]["devUuid"] = new_str + "_LED2_4"
    server.input_dict["test_009_2.4G_remove"][0]["control"]["data"][1]["v"] = test.ble_devId

    server.output_dict["test_002_check_gateway_version"][0]["part_same"]["data"]["deviceMac"] = new_str
    server.output_dict["test_003_check_iot_version"][1]["part_same"]["data"]["gatewayMac"] = new_str
    server.output_dict["test_003_check_iot_version"][2]["part_same"]["data"]["deviceMac"] = new_str + "_S3GATEWAY"
    server.output_dict["test_003_check_iot_version"][2]["part_same"]["data"]["gatewayMac"] = new_str
    server.output_dict["test_003_check_iot_version"][3]["part_same"]["data"]["deviceMac"] = new_str + "_LED2_4"
    server.output_dict["test_003_check_iot_version"][3]["part_same"]["data"]["gatewayMac"] = new_str
    server.output_dict["test_005_zigbee_connect"][1]["part_same"]["data"]["gatewayMac"] = new_str
    server.output_dict["test_007_2.4G_connect"][21]["part_same"]["data"]["gatewayMac"] = new_str
    server.output_dict["test_007_2.4G_connect"][21]["part_same"]["data"]["deviceMac"] = test.ble_devId
    server.output_dict["test_007_2.4G_connect"][21]["part_same"]["data"]["prodTypeId"] = test.ble_prodTypeId

    config = configparser.ConfigParser()
    config.read("../conf/zgateway.conf", encoding="utf-8")
    if config.has_option("link", "zgateway"):
        new_str = config.get("link", "zgateway")
        server.output_dict["test_002_check_gateway_version"][0]["part_same"]["data"]["version"] = new_str
    else:
        print("miss zgateway")
        exit()

    if config.has_option("link", "433"):
        new_str = config.get("link", "433")
        server.output_dict["test_003_check_iot_version"][2]["part_same"]["data"]["version"] = "ZIROOM433*V" + new_str
    else:
        print("miss 433")
        exit()

    if config.has_option("link", "2.4"):
        new_str = config.get("link", "2.4")
        server.output_dict["test_003_check_iot_version"][3]["part_same"]["data"]["version"] = new_str
    else:
        print("miss 2.4")
        exit()

    # print(server.input_dict)
    # print(server.output_dict)
    logging.info("json5更新完成...")


# 由于zigbee网关的mac需要获取才能得到，得到后再更新到json中
def zigbee_json_update(zigbeeGate):
    server.input_dict["test_003_check_iot_version"][1]["query"]["devId"] = zigbeeGate
    server.input_dict["test_005_zigbee_connect"][0]["connect"]["devId"] = zigbeeGate
    server.input_dict["test_005_zigbee_connect"][1]["query"]["devId"] = test.zigbee_devId
    server.input_dict["test_005_zigbee_connect"][1]["query"]["prodTypeId"] = test.zigbee_prodTypeId
    server.input_dict["test_006_zigbee_control"][0]["control"]["devId"] = test.zigbee_devId
    server.input_dict["test_006_zigbee_control"][0]["control"]["devUuid"] = test.zigbee_devId
    server.input_dict["test_006_zigbee_control"][0]["control"]["prodTypeId"] = test.zigbee_prodTypeId
    server.input_dict["test_006_zigbee_control"][2]["control"]["devId"] = test.zigbee_devId
    server.input_dict["test_006_zigbee_control"][2]["control"]["devUuid"] = test.zigbee_devId
    server.input_dict["test_006_zigbee_control"][2]["control"]["prodTypeId"] = test.zigbee_prodTypeId

    server.input_dict["test_007_2.4G_connect"][0]["control"]["devId"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][0]["control"]["devUuid"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][0]["control"]["prodTypeId"] = test.zigbee_prodTypeId
    server.input_dict["test_007_2.4G_connect"][2]["control"]["devId"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][2]["control"]["devUuid"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][2]["control"]["prodTypeId"] = test.zigbee_prodTypeId
    server.input_dict["test_007_2.4G_connect"][4]["control"]["devId"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][4]["control"]["devUuid"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][4]["control"]["prodTypeId"] = test.zigbee_prodTypeId
    server.input_dict["test_007_2.4G_connect"][6]["control"]["devId"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][6]["control"]["devUuid"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][6]["control"]["prodTypeId"] = test.zigbee_prodTypeId
    server.input_dict["test_007_2.4G_connect"][8]["control"]["devId"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][8]["control"]["devUuid"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][8]["control"]["prodTypeId"] = test.zigbee_prodTypeId
    server.input_dict["test_007_2.4G_connect"][10]["control"]["devId"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][10]["control"]["devUuid"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][10]["control"]["prodTypeId"] = test.zigbee_prodTypeId
    server.input_dict["test_007_2.4G_connect"][12]["control"]["devId"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][12]["control"]["devUuid"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][12]["control"]["prodTypeId"] = test.zigbee_prodTypeId
    server.input_dict["test_007_2.4G_connect"][14]["control"]["devId"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][14]["control"]["devUuid"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][14]["control"]["prodTypeId"] = test.zigbee_prodTypeId
    server.input_dict["test_007_2.4G_connect"][16]["control"]["devId"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][16]["control"]["devUuid"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][16]["control"]["prodTypeId"] = test.zigbee_prodTypeId
    server.input_dict["test_007_2.4G_connect"][18]["control"]["devId"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][18]["control"]["devUuid"] = test.zigbee_devId
    server.input_dict["test_007_2.4G_connect"][18]["control"]["prodTypeId"] = test.zigbee_prodTypeId

    server.input_dict["test_010_zigbee_remove"][0]["control"]["devId"] = zigbeeGate
    server.input_dict["test_010_zigbee_remove"][0]["control"]["devUuid"] = zigbeeGate
    server.input_dict["test_010_zigbee_remove"][0]["control"]["data"][0]["v"] = test.zigbee_devId

    server.output_dict["test_003_check_iot_version"][1]["part_same"]["data"]["deviceMac"] = zigbeeGate
    server.output_dict["test_005_zigbee_connect"][1]["part_same"]["data"]["deviceMac"] = test.zigbee_devId
    server.output_dict["test_005_zigbee_connect"][1]["part_same"]["data"]["prodTypeId"] = test.zigbee_prodTypeId
    server.output_dict["test_006_zigbee_control"][1]["part_same"]["data"]["devId"] = test.zigbee_devId
    server.output_dict["test_006_zigbee_control"][1]["part_same"]["data"]["devUuid"] = test.zigbee_devId
    server.output_dict["test_006_zigbee_control"][1]["part_same"]["data"]["prodTypeId"] = test.zigbee_prodTypeId
    server.output_dict["test_006_zigbee_control"][3]["part_same"]["data"]["devId"] = test.zigbee_devId
    server.output_dict["test_006_zigbee_control"][3]["part_same"]["data"]["devUuid"] = test.zigbee_devId
    server.output_dict["test_006_zigbee_control"][3]["part_same"]["data"]["prodTypeId"] = test.zigbee_prodTypeId
    server.output_dict["test_007_2.4G_connect"][1]["part_same"]["data"]["devId"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][1]["part_same"]["data"]["devUuid"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][1]["part_same"]["data"]["prodTypeId"] = test.zigbee_prodTypeId
    server.output_dict["test_007_2.4G_connect"][3]["part_same"]["data"]["devId"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][3]["part_same"]["data"]["devUuid"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][3]["part_same"]["data"]["prodTypeId"] = test.zigbee_prodTypeId
    server.output_dict["test_007_2.4G_connect"][5]["part_same"]["data"]["devId"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][5]["part_same"]["data"]["devUuid"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][5]["part_same"]["data"]["prodTypeId"] = test.zigbee_prodTypeId
    server.output_dict["test_007_2.4G_connect"][7]["part_same"]["data"]["devId"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][7]["part_same"]["data"]["devUuid"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][7]["part_same"]["data"]["prodTypeId"] = test.zigbee_prodTypeId
    server.output_dict["test_007_2.4G_connect"][9]["part_same"]["data"]["devId"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][9]["part_same"]["data"]["devUuid"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][9]["part_same"]["data"]["prodTypeId"] = test.zigbee_prodTypeId
    server.output_dict["test_007_2.4G_connect"][11]["part_same"]["data"]["devId"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][11]["part_same"]["data"]["devUuid"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][11]["part_same"]["data"]["prodTypeId"] = test.zigbee_prodTypeId
    server.output_dict["test_007_2.4G_connect"][13]["part_same"]["data"]["devId"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][13]["part_same"]["data"]["devUuid"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][13]["part_same"]["data"]["prodTypeId"] = test.zigbee_prodTypeId
    server.output_dict["test_007_2.4G_connect"][15]["part_same"]["data"]["devId"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][15]["part_same"]["data"]["devUuid"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][15]["part_same"]["data"]["prodTypeId"] = test.zigbee_prodTypeId
    server.output_dict["test_007_2.4G_connect"][17]["part_same"]["data"]["devId"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][17]["part_same"]["data"]["devUuid"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][17]["part_same"]["data"]["prodTypeId"] = test.zigbee_prodTypeId
    server.output_dict["test_007_2.4G_connect"][19]["part_same"]["data"]["devId"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][19]["part_same"]["data"]["devUuid"] = test.zigbee_devId
    server.output_dict["test_007_2.4G_connect"][19]["part_same"]["data"]["prodTypeId"] = test.zigbee_prodTypeId
    server.output_dict["test_010_zigbee_remove"][1]["part_same"]["data"]["data"][0]["v"] = test.zigbee_devId

    # print(server.input_dict)
    # print(server.output_dict)


def test_json_init(module_name):
    check_name = "test_"
    # 获取所有的测试名称及请求内容
    input_file = "../input_json/" + module_name + ".json5"
    output_file = "../output_json/" + module_name + ".json5"
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


def start_connect_ssh(info):
    # 实例化SSHClient
    client = paramiko.SSHClient()

    # 自动添加策略，保存服务器的主机名和密钥信息，如果不添加，那么不再本地know_hosts文件中记录的主机将无法连接
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # 连接SSH服务端，以用户名和密码进行认证
    logging.info(info["host"])
    logging.info(info["username"])
    logging.info(info["passwd"])

    try:
        client.connect(hostname=info["host"], port=22, username=info["username"], password=info["passwd"])
    except Exception as e:
        print("---异常---：", e)
        return True

    if client:
        # 打开一个Channel并执行命令
        stdin, stdout, stderr = client.exec_command('cat /proc/net/arp')  # stdout 为正确输出，stderr为错误输出，同时是有1个变量有值

        # 打印执行结果
        logging.info(stdout.read().decode('utf-8'))

        # 关闭SSHClient
        client.close()
        conn_result = False

    else:
        conn_result = True

    return conn_result


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


def run_test_case(module_name):
    # 写excel表,test case的头部
    test_top_write(module_name)
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
                # 有url，说明要访问tlink
                if server.input_dict[key][request_i].__contains__("url"):
                    request_url = server.url + server.input_dict[key][request_i]["url"]
                    request_head = {'content-type': 'application/json'}
                    request_data = {}
                    # 有head说明需要设置头部
                    if server.input_dict[key][request_i].__contains__("head_1") and \
                            server.input_dict[key][request_i].__contains__("head_2"):
                        request_head = {
                            server.input_dict[key][request_i]["head_1"]: server.input_dict[key][request_i]["head_2"],
                            'content-type': 'application/json'}
                    # 入网事件
                    if server.input_dict[key][request_i].__contains__("connect"):
                        server.wait_time = 30
                        request_data = server.input_dict[key][request_i]["connect"]
                    # 解网事件
                    elif server.input_dict[key][request_i].__contains__("remove"):
                        server.wait_time = 3
                        request_data = server.input_dict[key][request_i]["remove"]
                    # 控制事件
                    elif server.input_dict[key][request_i].__contains__("control"):
                        server.wait_time = 3
                        request_data = server.input_dict[key][request_i]["control"]
                        server.sno = str(uuid.uuid1())
                        request_data["sno"] = server.sno
                    # 控制相应事件（前提要有控制，否则sno会错误）
                    elif server.input_dict[key][request_i].__contains__("control_resp"):
                        server.wait_time = 1
                        request_data = server.input_dict[key][request_i]["control_resp"]
                        request_data["sno"] = server.sno
                    # 请求事件
                    elif server.input_dict[key][request_i].__contains__("query"):
                        server.wait_time = 1
                        request_data = server.input_dict[key][request_i]["query"]

                    logging.info("%s send:%s", key, request_data)
                    resp_data = requests.post(request_url, data=json.dumps(request_data), headers=request_head)
                    logging.info("%s recv:%s", key, resp_data.text)
                    if resp_data.status_code == 200:
                        msg = json.loads(resp_data.text)
                        # 全部相等
                        if server.output_dict[key][request_i].__contains__("total_same"):
                            if msg != server.output_dict[key][request_i]["total_same"]:
                                request_result = False
                        # 部分相等
                        elif server.output_dict[key][request_i].__contains__("part_same"):
                            if not comp_json_value(msg, server.output_dict[key][request_i]["part_same"]):
                                request_result = False
                        # 获取zigbeeGate的mac
                        elif server.output_dict[key][request_i].__contains__("Dusun_zigbeeGate"):
                            if not comp_json_value(msg, server.output_dict[key][request_i]["Dusun_zigbeeGate"]):
                                request_result = False
                            else:
                                i = 0
                                while i < len(msg["data"][0]):
                                    if msg["data"][i]["prodTypeId"] == "Dusun_zigbeeGate":
                                        zigbee_json_update(msg["data"][i]["deviceMac"])
                                        break
                                    i += 1
                elif server.input_dict[key][request_i].__contains__("wifi_connect"):
                    if not utils_wifi.start_connect_wifi(server.input_dict[key][request_i]["wifi_connect"]):
                        request_result = False
                elif server.input_dict[key][request_i].__contains__("ssh_connect"):
                    if not start_connect_ssh(server.input_dict[key][request_i]["ssh_connect"]):
                        request_result = False

            except Exception as e:
                logging.info("---异常---：", e)
                request_result = False

            request_i += 1
            time.sleep(server.wait_time)

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

    return True


def test_start():
    data_init()
    logging_init()
    logging.info("test start...")
    excel_init()


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

    excel.sheet_fd.write(zexcel.PROJECT_ROW, zexcel.PROJECT_COL + 1, test.project,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zexcel.VERSION_ROW, zexcel.VERSION_COL + 1, test.version,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zexcel.MAC_ROW, zexcel.MAC_COL + 1, test.mac,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zexcel.DATE_ROW, zexcel.DATE_COL + 1, test.date,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zexcel.TOTAL_ROW, zexcel.TOTAL_COL + 1, test.total_num,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zexcel.TOTAL_PASS_ROW, zexcel.TOTAL_PASS_COL + 1, test.pass_num,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    excel.sheet_fd.write(zexcel.TOTAL_FAIL_ROW, zexcel.TOTAL_FAIL_COL + 1, test.fail_num,
                         style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))

    filename = "../results/" + test.output_file + ".xls"
    excel.excel_fd.save(filename)  # 保存xls
    logging.info("test end!")
    exit()


if __name__ == '__main__':
    test_start()

    if not test_json_init("zgateway"):
        logging.error("json init error")
        test_end()

    run_test_case("zgateway")

    test_end()

