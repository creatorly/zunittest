#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2019/08/15
# Describe：zgateway测试

import logging
import requests
import json
import json5
import base64
import time
import configparser
import sys
import paramiko
import uuid
import os
import threading
import paho.mqtt.client as mqtt
from paho.mqtt.client import Client

sys.path.append("../../../..")
from zutils import zexcel
from zrouter.func.wifi.scripts import utils_wifi


class ServerInfo(object):
    url = ''
    headers = {}
    password = ''
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


class MqttClientInfo(object):
    fd = ""
    wait_event = threading.Event()
    control_response = False
    broadcast_response = False
    stop = False


server = ServerInfo
test = TestInfo
excel = ExcelInfo
mqttClient = MqttClientInfo


def data_init(module_name):
    # 获取配置文件信息
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__) + '/../conf/' + module_name + '.conf')
    config.read(config_path, encoding="utf-8")

    if config.has_option("link", "host"):
        server.url = config.get("link", "host")
    else:
        print("miss url")
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

    if config.has_option("server", "passwd"):
        server.password = config.get("server", "passwd")
    else:
        print("miss passwd")
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
    # 从第二行开始写入
    excel.row_point = 1


# 用于测试的设备版本、mac等信息是不一样，有些api需要跟新对应的信息
def test_json_update():
    sn = test.mac.split(":")
    new_str = sn[0] + sn[1] + sn[2] + sn[3] + sn[4] + sn[5]
    server.input_dict["test_002_check_gateway_version"][0]["query"]["devId"] = new_str
    server.input_dict["test_003_set_device_ssid"][0]["query"]["devId"] = new_str
    server.input_dict["test_003_set_device_ssid"][2]["query"]["data"][0]["v"] = "ZR_D" + sn[4] + sn[5]
    server.input_dict["test_003_set_device_ssid"][2]["query"]["data"][1]["v"] = "ZR_P" + sn[4] + sn[5]
    server.input_dict["test_003_set_device_ssid"][2]["query"]["devId"] = new_str
    server.input_dict["test_006_open_remote_ssh"][0]["open_remote_ssh"]["theme"] = "/com/ziroom/iot/zgateway/debug/" + new_str
    server.input_dict["test_008_close_remote_ssh"][0]["close_remote_ssh"]["theme"] = "/com/ziroom/iot/zgateway/debug/" + new_str

    server.output_dict["test_002_check_gateway_version"][0]["part_same"]["data"]["deviceMac"] = new_str
    server.output_dict["test_004_mqtt_connect"][1]["part_same"]["data"]["gatewayMac"] = new_str

    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__) + '/../conf/zgateway.conf')
    config.read(config_path, encoding="utf-8")
    if config.has_option("link", "zgateway"):
        new_str = config.get("link", "zgateway")
        server.output_dict["test_002_check_gateway_version"][0]["part_same"]["data"]["version"] = new_str
    else:
        print("miss zgateway")
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


def start_connect_ssh(info):
    # 实例化SSHClient
    client = paramiko.SSHClient()

    # 自动添加策略，保存服务器的主机名和密钥信息，如果不添加，那么不再本地know_hosts文件中记录的主机将无法连接
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # 连接SSH服务端，以用户名和密码进行认证
    logging.info(info["host"])
    logging.info(info["port"])
    logging.info(info["username"])
    logging.info(server.password)

    try:
        client.connect(hostname=info["host"], port=info["port"], username=info["username"], password=server.password)
    except Exception as e:
        print("---异常---：", e)
        return False

    if client:
        # 打开一个Channel并执行命令
        stdin, stdout, stderr = client.exec_command('cat /proc/net/arp')  # stdout 为正确输出，stderr为错误输出，同时是有1个变量有值

        # 打印执行结果
        logging.info(stdout.read().decode('utf-8'))

        # 关闭SSHClient
        client.close()
        conn_result = True

    else:
        conn_result = False

    return conn_result


def restart_zgateway(info):
    # 实例化SSHClient
    client = paramiko.SSHClient()

    # 自动添加策略，保存服务器的主机名和密钥信息，如果不添加，那么不再本地know_hosts文件中记录的主机将无法连接
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # 连接SSH服务端，以用户名和密码进行认证
    logging.info(info["host"])
    logging.info(info["port"])
    logging.info(info["username"])
    logging.info(server.password)

    try:
        client.connect(hostname=info["host"], port=info["port"], username=info["username"], password=server.password)
    except Exception as e:
        print("---异常---：", e)
        return False

    if client:
        # 使用invoke_shell方式执行脚本，用exec_command会出现问题
        chan = client.invoke_shell()
        chan.settimeout(9000)
        chan.send("/zihome/plugins/zgateway/run.sh restart" + '\n')
        # result = chan.recv(4096)
        # logging.info(result)

        time.sleep(5)
        # 关闭SSHClient
        client.close()
        conn_result = True

    else:
        conn_result = False

    return conn_result


# 消息处理函数
def mqtt_on_message_come(lient, userdata, msg):
    logging.info(msg.topic + " " + ":" + str(msg.payload))
    if msg.topic == "local/iot/ziroom/PYTHON/112233445566/control":
        mqttClient.control_response = True
    elif msg.topic == "local/iot/ziroom/broadcast":
        mqttClient.broadcast_response = True


# subscribe 消息
def mqtt_on_subscribe(mqttClient):
    mqttClient.subscribe("local/iot/ziroom/PYTHON/112233445566/control", 1)
    mqttClient.subscribe("local/iot/ziroom/broadcast", 1)
    publish_data = {
        "msgType": "DEVICE_INFO_REPORT",
        "devId": "112233445566",
        "prodTypeId": "PYTHON",
        "hardwareversion": "0.0.1",
        "softversion": "0.0.1",
        "clientId": "PYTHON_MQTT_CLIENT_112233445566"
    }

    if mqttClient.publish("local/iot/ziroom/PYTHON/112233445566/notify", json.dumps(publish_data), 0):
        logging.info("publish ok")
    else:
        logging.info("publish fail")

    mqttClient.on_message = mqtt_on_message_come  # 消息到来处理函数


def zgteway_mqtt_on_connect(info):
    mqttClient.fd = Client(client_id="PYTHON_MQTT_CLIENT_112233445566")

    # cacert.pem certificate.pfx
    mqttClient.fd.tls_set(ca_certs="zgateway_cacert.pem", certfile=None, keyfile=None, cert_reqs=mqtt.ssl.CERT_REQUIRED,
                          tls_version=mqtt.ssl.PROTOCOL_TLSv1, ciphers=None)
    mqttClient.fd.tls_insecure_set(True)
    will_payload = {
        "msgType": "DEVICE_DISCONNECT",
        "devId": "112233445566",
        "prodTypeId": "PYTHON",
        "clientId": "PYTHON_MQTT_CLIENT_112233445566"
    }
    mqttClient.fd.will_set("local/iot/ziroom/onoffline", json.dumps(will_payload), 1)

    if mqtt.MQTT_ERR_SUCCESS == mqttClient.fd.connect(info["host"], 6885, 20):
        logging.info("connect ok")
        mqttClient.fd.loop_start()
        mqtt_on_subscribe(mqttClient.fd)
    else:
        logging.info("connect fail")
        return False

    while True:
        if mqttClient.stop:
            return False
        else:
            pass


def start_connect_zgteway_mqtt(info):
    threading.Thread(target=zgteway_mqtt_on_connect, args=(info,)).start()
    return True


def open_remote_ssh(info):
    mqttClient.fd = Client()

    # cacert.pem certificate.pfx
    mqttClient.fd.tls_set(ca_certs="remote_cacert.pem", certfile=None, keyfile=None, cert_reqs=mqtt.ssl.CERT_REQUIRED,
                          tls_version=mqtt.ssl.PROTOCOL_TLSv1, ciphers=None)
    mqttClient.fd.tls_insecure_set(True)
    publish_data = {
        "content": "[common]\nserver_addr = 47.94.157.88\nserver_port = 44922\n\n\n[ssh]\ntype = tcp\nlocal_ip = 127.0.0.1\nlocal_port = 1022\nauthentication_timeout = 0\nremote_port = 44923",
        "action": "start"}
    if mqtt.MQTT_ERR_SUCCESS == mqttClient.fd.connect(info["host"], info["port"], 20):
        mqttClient.fd.loop_start()
        if mqttClient.fd.publish(info["theme"], json.dumps(publish_data), 0):
            logging.info("publish ok")
            return True
        else:
            logging.info("publish fail")
            return False
    else:
        logging.info("connect fail")
        return False


def close_remote_ssh(info):
    mqttClient.fd = Client()

    # cacert.pem certificate.pfx
    mqttClient.fd.tls_set(ca_certs="remote_cacert.pem", certfile=None, keyfile=None, cert_reqs=mqtt.ssl.CERT_REQUIRED,
                          tls_version=mqtt.ssl.PROTOCOL_TLSv1, ciphers=None)
    mqttClient.fd.tls_insecure_set(True)
    publish_data = {
        "content": "[common]\nserver_addr = 47.94.157.88\nserver_port = 44922\n\n\n[ssh]\ntype = tcp\nlocal_ip = 127.0.0.1\nlocal_port = 1022\nauthentication_timeout = 0\nremote_port = 44923",
        "action": "stop"}
    if mqtt.MQTT_ERR_SUCCESS == mqttClient.fd.connect(info["host"], info["port"], 20):
        logging.info("connect ok")
        mqttClient.fd.loop_start()
        if mqttClient.fd.publish(info["theme"], json.dumps(publish_data), 0):
            logging.info("publish ok")
            return True
        else:
            logging.info("publish fail")
            return False
    else:
        logging.info("connect fail")
        return False


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

                    # 请求事件
                    if server.input_dict[key][request_i].__contains__("query"):
                        server.wait_time = 1
                        request_data = server.input_dict[key][request_i]["query"]
                    else:
                        server.wait_time = 1

                    logging.info("%s send:%s", key, request_data)
                    resp_data = requests.post(request_url, data=json.dumps(request_data), headers=request_head, timeout=5)
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

                elif server.input_dict[key][request_i].__contains__("wifi_connect"):
                    if not utils_wifi.start_connect_wifi(server.input_dict[key][request_i]["wifi_connect"]):
                        request_result = False
                elif server.input_dict[key][request_i].__contains__("check_ssh_on"):
                    if not start_connect_ssh(server.input_dict[key][request_i]["check_ssh_on"]):
                        request_result = False
                elif server.input_dict[key][request_i].__contains__("check_ssh_off"):
                    if start_connect_ssh(server.input_dict[key][request_i]["check_ssh_off"]):
                        request_result = False
                elif server.input_dict[key][request_i].__contains__("zgateway_mqtt_connect"):
                    server.wait_time = 3
                    if not start_connect_zgteway_mqtt(server.input_dict[key][request_i]["zgateway_mqtt_connect"]):
                        request_result = False
                elif server.input_dict[key][request_i].__contains__("zgateway_mqtt_control"):
                    if not mqttClient.control_response:
                        request_result = False
                elif server.input_dict[key][request_i].__contains__("restart_zgateway"):
                    if not restart_zgateway(server.input_dict[key][request_i]["restart_zgateway"]):
                        request_result = False
                    else:
                        mqttClient.broadcast_response = False
                        server.wait_time = 15
                elif server.input_dict[key][request_i].__contains__("check_broadcast"):
                    server.wait_time = 1
                    if not mqttClient.broadcast_response:
                        request_result = False
                elif server.input_dict[key][request_i].__contains__("zgateway_mqtt_disconnect"):
                    mqttClient.stop = True
                    server.wait_time = 5
                elif server.input_dict[key][request_i].__contains__("open_remote_ssh"):
                    if not open_remote_ssh(server.input_dict[key][request_i]["open_remote_ssh"]):
                        server.wait_time = 3
                        request_result = False
                elif server.input_dict[key][request_i].__contains__("close_remote_ssh"):
                    if not close_remote_ssh(server.input_dict[key][request_i]["close_remote_ssh"]):
                        server.wait_time = 3
                        request_result = False

                else:
                    server.wait_time = 1

            except Exception as e:
                logging.info("---异常---：", e)
                request_result = False

            request_i += 1
            time.sleep(server.wait_time)

        # 填写测试结果到excel的第二列
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

    filename = os.path.join(os.path.dirname(__file__) + "/../results/" + test.output_file + ".xls")
    excel.excel_fd.save(filename)  # 保存xls
    logging.info("test end!")
    exit()


if __name__ == '__main__':
    test_start("zgateway")

    if not test_json_init("zgateway"):
        logging.error("json init error")
        test_end()

    run_test_case("zgateway")

    test_end()

