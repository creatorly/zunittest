#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2020/04/30
# Describe：跑流

import logging
import base64
import time
import configparser
import os
import sys
import signal
import pyautogui
from PIL import Image
import pytesseract
import telnetlib
import xlsxwriter

sys.path.append("../../../..")
from zutils import zexcel


class ServerInfo(object):
    url = ''
    headers = {}
    sid = ''
    password = ''
    input_dict = {}
    output_dict = {}


class RadioRackInfo(object):
    ip = '192.168.1.18'
    port = 50000
    attenuation = []
    channel = []
    wait_time = 60


class TestInfo(object):
    project = ''
    version = ''
    mac = ''
    date = ''
    name = ''
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
radio_rack = RadioRackInfo
CASE_NAME_COL = 0
CASE_UPLINK_COL = 1
CASE_DOWNLINK_COL = 2

excel_type = "xlsx"


def data_init(module_name):
    # 获取配置文件信息
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__) + '/../../../zrouter.conf')
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

    config_path = os.path.join(os.path.dirname(__file__) + '/../conf/' + module_name + '.conf')
    config.read(config_path, encoding="utf-8")

    if config.has_option("radio_rack", "ip"):
        radio_rack.ip = config.get("radio_rack", "ip")
    else:
        print("miss radio_rack ip")
        exit()

    if config.has_option("radio_rack", "port"):
        radio_rack.port = config.get("radio_rack", "port")
    else:
        print("miss radio_rack port")
        exit()

    if config.has_option("radio_rack", "attenuation"):
        radio_rack.attenuation = config.get("radio_rack", "attenuation").split(",")
    else:
        print("miss radio_rack attenuation")
        exit()

    if config.has_option("radio_rack", "channel"):
        radio_rack.channel = config.get("radio_rack", "channel").split(",")
    else:
        print("miss radio_rack channel")
        exit()

    if config.has_option("IxChariot", "wait_time"):
        radio_rack.wait_time = int(config.get("IxChariot", "wait_time"))
    else:
        print("miss wait_time")
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
    if excel_type == "xlsx":
        filename = os.path.join(os.path.dirname(__file__) + "/../results/" + test.output_file + ".xlsx")
        excel.excel_fd = xlsxwriter.Workbook(filename)

        sheet_name = module_name + "测试结果"

        excel.sheet_fd = excel.excel_fd.add_worksheet(sheet_name)  # 增加sheet
        excel.sheet_fd.set_column(0, 3, 10)

    elif excel_type == "xls":
        sheet_name = module_name + "测试结果"
        excel.excel_fd = zexcel.excel_init()
        excel.sheet_fd = excel.excel_fd.add_sheet(sheet_name)  # 增加sheet
        excel.sheet_fd.col(zexcel.CASE_NAME_COL).width = 200 * 15  # 设置第1列列宽
        excel.sheet_fd.col(zexcel.CASE_RESULT_COL).width = 200 * 15  # 设置第2列列宽
        excel.sheet_fd.col(zexcel.COUNT_COL).width = 200 * 15  # 设置第3列列宽
        excel.sheet_fd.col(zexcel.PASS_COL).width = 200 * 15  # 设置第4列列宽
        excel.sheet_fd.col(zexcel.FAIL_COL).width = 200 * 15  # 设置第5列列宽
        excel.sheet_fd.col(zexcel.PROJECT_COL).width = 180 * 15  # 设置第7列列宽
        excel.sheet_fd.col(zexcel.PROJECT_COL + 1).width = 360 * 15  # 设置第8列列宽

        # 写第一行数据
        excel.sheet_fd.write_merge(0, 0, 0, 4, sheet_name, zexcel.set_style(0x7FFF, 320, bold=True))

        excel.sheet_fd.write(zexcel.PROJECT_ROW, zexcel.PROJECT_COL, "project:",
                             style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
        excel.sheet_fd.write(zexcel.VERSION_ROW, zexcel.VERSION_COL, "version:",
                             style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
        excel.sheet_fd.write(zexcel.MAC_ROW, zexcel.MAC_COL, "mac:",
                             style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))
        excel.sheet_fd.write(zexcel.DATE_ROW, zexcel.DATE_COL, "date:",
                             style=zexcel.set_style(zexcel.BLACK, 260, bold=True, align='', pattern_color='light_orange'))

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


def test_top_write(module_name):
    excel.row_point += 1
    if excel_type == "xlsx":
        excel.sheet_fd.write(excel.row_point, 0, "Atten")
        excel.sheet_fd.write(excel.row_point, 1, "Downlink")
        excel.sheet_fd.write(excel.row_point, 2, "Uplink")
    elif excel_type == "xls":
        excel.sheet_fd.write(excel.row_point, 0, "Atten",
                             style=zexcel.set_style(zexcel.BLACK, 280, bold=False, align='', pattern_color='gray25'))
        excel.sheet_fd.write(excel.row_point, 1, "Downlink",
                             style=zexcel.set_style(zexcel.BLACK, 280, bold=False, align='', pattern_color='gray25'))
        excel.sheet_fd.write(excel.row_point, 2, "Uplink",
                             style=zexcel.set_style(zexcel.BLACK, 280, bold=False, align='', pattern_color='gray25'))


def set_RadioRack(command):
    try:
        # tn = telnetlib.Telnet(radio_rack.ip, radio_rack.port)
        time.sleep(2)
        # 执行命令
        logging.info('send %s' % command)
        # tn.write(command.encode('ascii') + b'\n')
        # # 获取命令结果
        # time.sleep(2)
        # command_result = tn.read_very_eager().decode('ascii')
        # logging.info('%s' % command_result)
        # time.sleep(2)
        # tn.close()
    except Exception as err:
        logging.warning('%s failed to connect !' % radio_rack.ip)
        return False


def run_IxChariot(name, wait_time):
    location = pyautogui.locateOnScreen(image='../conf/image/Run.png')
    logging.info("Run location %s", location)
    try:
        x, y = pyautogui.center(location)
        pyautogui.moveTo(x, y, duration=1)
        pyautogui.click()
        logging.info("click run...")

    except Exception as err:
        logging.info(err)

    time.sleep(1)  # 两次点击之间延迟一会儿
    location = pyautogui.locateOnScreen(image='../conf/image/Throughput.png')
    logging.info("Throughput location %s", location)
    try:
        x, y = pyautogui.center(location)
        pyautogui.moveTo(x, y, duration=1)
        pyautogui.click()
        logging.info("click Throughput...")

    except Exception as err:
        logging.info(err)

    time.sleep(wait_time)

    wait_i = 0
    while wait_i < wait_time:  # 2秒一次，尝试5次
        time.sleep(2)
        wait_i += 2
        logging.info("等待测试结束...")
        error_location = pyautogui.locateOnScreen(image='../conf/image/Error.png')
        if error_location:
            logging.info("Error location %s", error_location)
            logging.info("测试出错,关闭窗口再次测试")
            ok_location = pyautogui.locateOnScreen(image='../conf/image/Error_Ok.png')
            logging.info("ok_location location %s", ok_location)
            try:
                # 为了去掉Throughput的选中，点击一下Average
                x, y = pyautogui.center(ok_location)
                pyautogui.moveTo(x, y, duration=1)
                pyautogui.click()
                logging.info("click ok...")
                return "error"
            except Exception as err:
                logging.info(err)
                return "error"
        else:
            run_location = pyautogui.locateOnScreen(image='../conf/image/Run.png')
            if run_location:
                logging.info("Run location %s", run_location)
                logging.info("测试已经停止，获取测试结果")
                break
            else:
                logging.info("%d...", wait_i)

    Pair10_on = pyautogui.locateOnScreen(image='../conf/image/Pair10_on.png')
    logging.info("Pair10_on location %s", Pair10_on)

    if Pair10_on:
        # 点击一下Pair,去掉Throughput的选择和蓝色的全选，提高识别率
        x, y = pyautogui.center(Pair10_on)
        pyautogui.moveTo(x, y, duration=1)
        pyautogui.click()
        logging.info("click Pair10_on...")
    else:
        Pair10_off = pyautogui.locateOnScreen(image='../conf/image/Pair10_off.png')
        logging.info("Pair10_off location %s", Pair10_off)

        if Pair10_off:
            # 点击一下Pair,去掉Throughput的选择和蓝色的全选，提高识别率
            x, y = pyautogui.center(Pair10_off)
            pyautogui.moveTo(x, y, duration=1)
            pyautogui.click()
            logging.info("click Pair10_off...")

    location = pyautogui.locateOnScreen(image='../conf/image/Average_4.png')
    logging.info("Average location %s", location)
    try:
        # Average的图片大小50 * 30，向下移动5个点，获取数据长度: 70 * 15
        # average_data_x = location[0] - 10
        # average_data_y = location[1] + 32
        # Average_4的图片大小60 * 40，向下移动5个点，获取数据长度: 60 * 15
        average_data_x = location[0] - 2
        average_data_y = location[1] + 44

        average_img = '../results/image/' + test.output_file + name + '.png'
        logging.info("save img %s", average_img)
        img = pyautogui.screenshot(region=[average_data_x, average_data_y, 62, 17])  # x,y,w,h
        img.save(average_img)

        time.sleep(2)

        pytesseract.pytesseract.tesseract_cmd = 'D:\\Program Files\\Tesseract-OCR\\tesseract.exe'
        image = Image.open(average_img)

        content = pytesseract.image_to_string(image)  # 解析图片
        logging.info(content)
        data = ''.join(list(filter(lambda ch: ch in '0123456789.', content)))
        try:
            float(data)
        except Exception as err:
            logging.info(err)
            content = pytesseract.image_to_string(image)  # 解析图片
            logging.info(content)
            data = ''.join(list(filter(lambda ch: ch in '0123456789.', content)))

        return float(data)

    except Exception as err:
        logging.info(err)


def change_direction():
    location = pyautogui.locateOnScreen(image='../conf/image/Allpairs.png')
    logging.info("Allpairs location %s", location)
    try:
        x, y = pyautogui.center(location)
        pyautogui.moveTo(x, y, duration=1)
        pyautogui.click()
        logging.info("click run...")

    except Exception as err:
        logging.info(err)

    time.sleep(1)  # 两次点击之间延迟一会儿

    location = pyautogui.locateOnScreen(image='../conf/image/Swap.png')
    logging.info("Swap location %s", location)
    try:
        x, y = pyautogui.center(location)
        pyautogui.moveTo(x, y, duration=1)
        pyautogui.click()
        logging.info("click Swap...")
    except Exception as err:
        logging.info(err)


def run_test_case(module_name):
    # 写excel表,test case的头部
    test_top_write(module_name)

    for attenuation in radio_rack.attenuation:

        set_command = "ATT "
        for channel in radio_rack.channel:
            set_command += channel + " " + attenuation + ";"
        set_command = set_command[:-1] + "<CR><LF>"
        set_RadioRack(set_command)

        logging.info(" ############ Uplink : %s dB", attenuation)
        uplink_data = run_IxChariot(attenuation + "db_uplink", radio_rack.wait_time)
        change_direction()

        logging.info(" ############ Downlink : %s dB", attenuation)
        downlink_data = run_IxChariot(attenuation + "db_downlink", radio_rack.wait_time)
        change_direction()

        # 写excel
        excel.row_point += 1
        if excel_type == "xlsx":
            excel.sheet_fd.write(excel.row_point, CASE_NAME_COL, attenuation + "dB")
            excel.sheet_fd.write(excel.row_point, CASE_UPLINK_COL, uplink_data)
            excel.sheet_fd.write(excel.row_point, CASE_DOWNLINK_COL, downlink_data)
        elif excel_type == "xls":
            excel.sheet_fd.write(excel.row_point, CASE_NAME_COL, attenuation + "dB",
                                 style=zexcel.set_style(zexcel.BLACK, 240, bold=False, align=''))
            excel.sheet_fd.write(excel.row_point, CASE_UPLINK_COL, uplink_data,
                                 style=zexcel.set_style(zexcel.GREEN, 240, bold=False, align=''))
            excel.sheet_fd.write(excel.row_point, CASE_DOWNLINK_COL, downlink_data,
                                 style=zexcel.set_style(zexcel.GREEN, 240, bold=False, align=''))
            filename = os.path.join(os.path.dirname(__file__) + "/../results/" + test.output_file + ".xls")
            excel.excel_fd.save(filename)  # 保存xls

        time.sleep(2)

    return True


def test_start(module_name):
    data_init(module_name)
    logging_init()
    logging.info("test start...")
    excel_init(module_name)


def test_end():
    if excel_type == "xlsx":
        excel.excel_fd.close()  # 保存xlsx
    elif excel_type == "xls":
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

    module = "throughput"

    test_start(module)

    run_test_case(module)

    test_end()




