#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2019/06/26
# Describe：提供excel表的设置接口

import xlwt


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
    sheet_fd.col(0).width = 200 * 40  # 设置第1列列宽
    sheet_fd.col(1).width = 200 * 15  # 设置第2列列宽
    sheet_fd.col(2).width = 200 * 15  # 设置第3列列宽
    sheet_fd.col(3).width = 200 * 15  # 设置第4列列宽
    sheet_fd.col(4).width = 200 * 15  # 设置第5列列宽

    # 写第一行数据
    sheet_fd.write_merge(0, 0, 0, 4, sheet_name, set_style(0x7FFF, 320, bold=True))

    # 写第二行数据
    rows = ['', 'Result', 'Count', 'Pass', 'Fail']
    for index, val in enumerate(rows):
        sheet_fd.write(1, index, val, style=set_style(0x7FFF, 280, bold=True, pattern_color='gray25'))

    return sheet_fd


if __name__ == '__main__':
    print("请开始你的表演")
