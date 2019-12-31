#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2019/12/29
# Describe：1一分钟获取一次进程的内存信息，将内存信息保存在excel中，一个sheet对应一个进程

import logging
import base64
import time
import configparser
import sys
import os
import paramiko

sys.path.append("../../../..")
from zutils import zexcel


CASE_TIME_COL = 0
CASE_MEM_COL = 1


class SshInfo(object):
    hostname = ''
    port = 22
    username = ''
    password = ''


class TestInfo(object):
    project = ''
    version = ''
    mac = ''
    date = ''
    name = ''
    process = []
    output_file = ''


class ExcelInfo(object):
    excel_fd = 0
    sheet_fd = {}
    row_point = {}


ssh = SshInfo
test = TestInfo
excel = ExcelInfo


def data_init(module_name):
    # 获取配置文件信息
    config = configparser.ConfigParser()
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

    config_path = os.path.join(os.path.dirname(__file__) + '/../conf/' + module_name + '.conf')
    config.read(config_path, encoding="utf-8")
    if config.has_option(test.name, "process"):
        test.process = config.get(test.name, "process").split(",")
    else:
        print("miss process")
        exit()

    if config.has_option("ssh", "hostname"):
        ssh.hostname = config.get("ssh", "hostname")
    else:
        print("miss hostname")
        exit()

    if config.has_option("ssh", "port"):
        ssh.port = config.get("ssh", "port")
    else:
        print("miss port")
        exit()

    if config.has_option("ssh", "username"):
        ssh.username = config.get("ssh", "username")
    else:
        print("miss username")
        exit()

    if config.has_option("ssh", "password"):
        ssh.password = config.get("ssh", "password")
    else:
        print("miss password")
        exit()

    test.date = time.strftime("%Y/%m/%d", time.localtime())
    test.output_file = time.strftime("%Y%m%d_%H%M%S", time.localtime()) + "_" + module_name + "_test"


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


def excel_init():
    excel.excel_fd = zexcel.excel_init()

    # 每个线程一个sheet
    for process in test.process:
        logging.info(process)
        excel.sheet_fd[process] = excel.excel_fd.add_sheet(process)  # 增加sheet
        excel.sheet_fd[process].col(CASE_TIME_COL).width = 200 * 25  # 设置第1列列宽
        excel.sheet_fd[process].col(CASE_MEM_COL).width = 200 * 25  # 设置第2列列宽
        excel.row_point[process] = 0

        rows = ['时间(分钟)', '内存（Kb）']
        for index, val in enumerate(rows):
            excel.sheet_fd[process].write(excel.row_point[process], index, val,
                                          style=zexcel.set_style(zexcel.BLACK, 280, bold=True, pattern_color='gray25'))

    filename = os.path.join(os.path.dirname(__file__) + "/../results/" + test.output_file + ".xls")
    excel.excel_fd.save(filename)  # 保存xls


def start_connect_ssh(process):
    ret = 0
    # 实例化SSHClient
    client = paramiko.SSHClient()

    # 自动添加策略，保存服务器的主机名和密钥信息，如果不添加，那么不再本地know_hosts文件中记录的主机将无法连接
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname=ssh.hostname, port=int(ssh.port), username=ssh.username, password=ssh.password)
    except Exception as e:
        print("---异常---：", e)
        return ret

    if client:
        # 打开一个Channel并执行命令
        command = "ps | grep " + process + "| grep -v grep | awk '{print $3}'"
        stdin, stdout, stderr = client.exec_command(command)  # stdout 为正确输出，stderr为错误输出，同时是有1个变量有值

        # 打印执行结果
        command_result = stdout.read().decode('utf-8')
        logging.info(command_result)

        if command_result:
            ret = int(command_result.replace("\n", ""))
        else:
            ret = 0

        # 关闭SSHClient
        client.close()

    return ret


def run_test_case():
    test_time = 0
    while True:
        # 每个线程一个sheet
        for process in test.process:

            mem_result = start_connect_ssh(process)

            excel.row_point[process] += 1
            excel.sheet_fd[process].write(excel.row_point[process], CASE_TIME_COL, test_time,
                                          style=zexcel.set_style(zexcel.BLACK, 240, bold=False, align=''))
            excel.sheet_fd[process].write(excel.row_point[process], CASE_MEM_COL, mem_result,
                                          style=zexcel.set_style(zexcel.BLACK, 240, bold=False, align=''))

            filename = os.path.join(os.path.dirname(__file__) + "/../results/" + test.output_file + ".xls")
            excel.excel_fd.save(filename)  # 保存xls

        test_time += 1
        logging.info("time: %d", test_time)
        time.sleep(6)


def test_start(module_name):
    data_init(module_name)
    logging_init()
    logging.info("test start...")
    excel_init()


def test_end():
    filename = os.path.join(os.path.dirname(__file__) + "/../results/" + test.output_file + ".xls")
    excel.excel_fd.save(filename)  # 保存xls
    logging.info("test end!")
    exit()


if __name__ == '__main__':
    # if 2 != len(sys.argv) or (sys.argv[1] != 'zrouter' and sys.argv[1] != 'zgateway'):
    #     print("please enter zrouter/zgateway")
    #     exit()
    # else:
    #     test.name = sys.argv[1]

    test.name = "zgateway"
    test_start("mem")
    run_test_case()
    test_end()


