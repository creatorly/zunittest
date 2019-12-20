#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2019/06/26
# Describe：提供excel表的设置接口

import xlwt


# Define excel position.
PROJECT_COL = 6
PROJECT_ROW = 0
VERSION_COL = 6
VERSION_ROW = 1
MAC_COL = 6
MAC_ROW = 2
DATE_COL = 6
DATE_ROW = 3
TOTAL_COL = 6
TOTAL_ROW = 4
TOTAL_PASS_COL = 6
TOTAL_PASS_ROW = 5
TOTAL_FAIL_COL = 6
TOTAL_FAIL_ROW = 6
CASE_NAME_COL = 0
CASE_RESULT_COL = 1
COUNT_COL = 2
PASS_COL = 3
FAIL_COL = 4


# Define excel color.
RED = 0x0A
GREEN = 0x11
BLACK = 0X7FFF


def set_style(font_color, height, bold=False, pattern_color='', align='center'):
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
    excel_fd = xlwt.Workbook()
    return excel_fd


def sheet_init(excel_fd, sheet_name):
    sheet_fd = excel_fd.add_sheet(sheet_name)  # 增加sheet
    sheet_fd.col(CASE_NAME_COL).width = 200 * 40  # 设置第1列列宽
    sheet_fd.col(CASE_RESULT_COL).width = 200 * 15  # 设置第2列列宽
    sheet_fd.col(COUNT_COL).width = 200 * 15  # 设置第3列列宽
    sheet_fd.col(PASS_COL).width = 200 * 15  # 设置第4列列宽
    sheet_fd.col(FAIL_COL).width = 200 * 15  # 设置第5列列宽
    sheet_fd.col(PROJECT_COL).width = 180 * 15  # 设置第7列列宽
    sheet_fd.col(PROJECT_COL + 1).width = 360 * 15  # 设置第8列列宽

    # 写第一行数据
    sheet_fd.write_merge(0, 0, 0, 4, sheet_name, set_style(0x7FFF, 320, bold=True))

    sheet_fd.write(PROJECT_ROW, PROJECT_COL, "project:",
                   style=set_style(BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    sheet_fd.write(VERSION_ROW, VERSION_COL, "version:",
                   style=set_style(BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    sheet_fd.write(MAC_ROW, MAC_COL, "mac:",
                   style=set_style(BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    sheet_fd.write(DATE_ROW, DATE_COL, "date:",
                   style=set_style(BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    sheet_fd.write(TOTAL_ROW, TOTAL_COL, "total:",
                   style=set_style(BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    sheet_fd.write(TOTAL_PASS_ROW, TOTAL_PASS_COL, "pass:",
                   style=set_style(BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    sheet_fd.write(TOTAL_FAIL_ROW, TOTAL_FAIL_COL, "fail:",
                   style=set_style(BLACK, 260, bold=True, align='', pattern_color='light_orange'))

    # 写第二行数据
    rows = ['', 'Result', 'Count', 'Pass', 'Fail']
    for index, val in enumerate(rows):
        sheet_fd.write(1, index, val, style=set_style(BLACK, 280, bold=True, pattern_color='gray25'))

    return sheet_fd


def common_sheet_init(excel_fd, sheet_name):
    sheet_fd = excel_fd.add_sheet(sheet_name)  # 增加sheet
    sheet_fd.col(CASE_NAME_COL).width = 200 * 40  # 设置第1列列宽
    sheet_fd.col(CASE_RESULT_COL).width = 200 * 15  # 设置第2列列宽
    sheet_fd.col(COUNT_COL).width = 200 * 15  # 设置第3列列宽
    sheet_fd.col(PASS_COL).width = 200 * 15  # 设置第4列列宽
    sheet_fd.col(FAIL_COL).width = 200 * 15  # 设置第5列列宽
    sheet_fd.col(PROJECT_COL).width = 180 * 15  # 设置第7列列宽
    sheet_fd.col(PROJECT_COL + 1).width = 360 * 15  # 设置第8列列宽

    # 写第一行数据
    sheet_fd.write_merge(0, 0, 0, 4, sheet_name, set_style(0x7FFF, 320, bold=True))

    # 写项目信息
    sheet_fd.write(PROJECT_ROW, PROJECT_COL, "project:",
                   style=set_style(BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    sheet_fd.write(VERSION_ROW, VERSION_COL, "version:",
                   style=set_style(BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    sheet_fd.write(MAC_ROW, MAC_COL, "mac:",
                   style=set_style(BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    sheet_fd.write(DATE_ROW, DATE_COL, "date:",
                   style=set_style(BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    sheet_fd.write(TOTAL_ROW, TOTAL_COL, "total:",
                   style=set_style(BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    sheet_fd.write(TOTAL_PASS_ROW, TOTAL_PASS_COL, "pass:",
                   style=set_style(BLACK, 260, bold=True, align='', pattern_color='light_orange'))
    sheet_fd.write(TOTAL_FAIL_ROW, TOTAL_FAIL_COL, "fail:",
                   style=set_style(BLACK, 260, bold=True, align='', pattern_color='light_orange'))

    return sheet_fd


if __name__ == '__main__':
    print("请开始你的表演")
