import logging
import requests
import json
import json5
import base64
import xlwt
import time
import configparser


class ServerInfo(object):
    url = ''
    headers = {}
    sid = ''
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
    config.read("api.conf", encoding="utf-8")
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
        filename=test.output_file + ".log",  # 指定输出的文件
        level=logging.INFO,
        format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    return True


def excel_style(font_color, height, bold=False, pattern_color='', align='center'):
    style = xlwt.XFStyle()  # 初始化样式
    font = xlwt.Font()  # 为样式创建字体
    font.name = 'Times New Roman'
    font.bold = bold
    font.height = height
    font.colour_index = font_color

    borders = xlwt.Borders()  # 为样式创建边框
    borders.left = 0
    borders.right = 0
    borders.top = 0
    borders.bottom = 0

    alignment = xlwt.Alignment()  # 设置排列
    if align == 'center':
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        alignment.vert = xlwt.Alignment.VERT_CENTER
    else:
        alignment.horz = xlwt.Alignment.HORZ_LEFT
        alignment.vert = xlwt.Alignment.VERT_BOTTOM

    if pattern_color != '':
        pattern = xlwt.Pattern()  # 一个实例化的样式类
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN  # 固定的样式
        pattern.pattern_fore_colour = xlwt.Style.colour_map[pattern_color]  # 背景颜色
        style.pattern = pattern

    style.font = font
    style.borders = borders
    style.alignment = alignment

    return style


def excel_init():
    excel.excel_fd = xlwt.Workbook()
    excel.sheet_fd = excel.excel_fd.add_sheet('Api Test')  # 增加sheet
    excel.sheet_fd.col(0).width = 200 * 40  # 设置第1列列宽
    excel.sheet_fd.col(1).width = 200 * 15  # 设置第2列列宽
    excel.sheet_fd.col(2).width = 200 * 15  # 设置第3列列宽
    excel.sheet_fd.col(3).width = 200 * 15  # 设置第4列列宽
    excel.sheet_fd.col(4).width = 200 * 15  # 设置第5列列宽

    # 写第一行数据
    excel.sheet_fd.write_merge(0, 0, 0, 4, 'API测试结果', excel_style(0x7FFF, 320, bold=True))

    # 写第二行数据
    excel.row_point += 1
    logging.info("excel.row_point:%d", excel.row_point)
    rows = ['', 'Result', 'Count', 'Pass', 'Fail']
    for index, val in enumerate(rows):
        excel.sheet_fd.write(excel.row_point, index, val,
                             style=excel_style(0x7FFF, 280, bold=True, pattern_color='gray25'))


def test_json_init(module_name):
    check_name = "test_"
    # 获取所有的测试名称及请求内容
    input_file = "input_json/" + module_name + ".json5"
    output_file = "output_json/" + module_name + ".json5"
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
                         style=excel_style(0x7FFF, 280, bold=False, align='', pattern_color='sky_blue'))
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
                         style=excel_style(0x7FFF, 240, bold=False, align=''))
    excel.module_info[module_name]["count"] += 1

    logging.info(request_data)
    resp_data = requests.post(server.url, data=json.dumps(request_data), headers=server.headers)
    logging.info(resp_data.text)
    if resp_data.status_code == 200:
        msg = json.loads(resp_data.text)
        if 0 == msg["errcode"]:
            server.sid = msg["data"][0]["result"]["sid"]
            excel.sheet_fd.write(excel.row_point, 1, "pass",
                                 style=excel_style(0x11, 240, bold=False, align=''))
            excel.module_info[module_name]["pass"] += 1
            return True
        else:
            excel.sheet_fd.write(excel.row_point, 1, "fail",
                                 style=excel_style(0x0A, 240, bold=False, align=''))
            excel.module_info[module_name]["fail"] += 1
            return False
    else:
        excel.sheet_fd.write(excel.row_point, 1, "fail",
                             style=excel_style(0x0A, 240, bold=False, align=''))
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
        excel.sheet_fd.write(excel.row_point, 0, key, style=excel_style(0x7FFF, 240, bold=False, align=''))
        excel.module_info[module_name]["count"] += 1

        # 一个case里面可能会有多个请求
        request_i = 0
        request_result = 0
        while request_i < len(server.input_dict[key]):
            request_data = server.input_dict[key][request_i]
            request_data["sid"] = server.sid
            logging.info("%s send:%s", key, request_data)
            resp_data = requests.post(server.url, data=json.dumps(request_data), headers=server.headers)
            logging.info("%s recv:%s", key, resp_data.text)
            if resp_data.status_code == 200:
                msg = json.loads(resp_data.text)
                if 0 == msg["errcode"]:
                    # 判断返回的数据与output_json里面的是否一致
                    if msg != server.output_dict[key][request_i]:
                        request_result = 1
                else:
                    request_result = 1
            else:
                request_result = 1

            request_i += 1

        # 填写测试结果到excel的第二列
        if request_result == 0:
            logging.info("pass")
            print("pass")
            excel.sheet_fd.write(excel.row_point, 1, "pass",
                                 style=excel_style(0x11, 240, bold=False, align=''))
            excel.module_info[module_name]["pass"] += 1
        else:
            logging.info("fail")
            print("fail")
            excel.sheet_fd.write(excel.row_point, 1, "fail",
                                 style=excel_style(0x0A, 240, bold=False, align=''))
            excel.module_info[module_name]["fail"] += 1

    return True


def test_end():
    # 将统计的count pass fail写入excel
    for key in excel.module_info:
        excel.sheet_fd.write(excel.module_info[key]["row"], 2, excel.module_info[key]["count"],
                             style=excel_style(0x0A, 240, bold=False, align=''))
        excel.sheet_fd.write(excel.module_info[key]["row"], 3, excel.module_info[key]["pass"],
                             style=excel_style(0x0A, 240, bold=False, align=''))
        excel.sheet_fd.write(excel.module_info[key]["row"], 4, excel.module_info[key]["fail"],
                             style=excel_style(0x0A, 240, bold=False, align=''))

    filename = test.output_file + ".xls"
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
