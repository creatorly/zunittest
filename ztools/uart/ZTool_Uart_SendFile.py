#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2019/09/17
# Describe：

import serial  # 导入模块
import time
import logging
import sys


class UartInfo(object):
    def __init__(self, fd, count, fail):
        self.fd = fd
        self.count = count  # 测试次数
        self.fail = fail  # 失败次数

    response = False
    file = ""
    size = 1
    looptime = 1


uart = UartInfo(-1, 0, 0)


def logging_init():
    logging.basicConfig(  # filename="log/test.log", # 指定输出的文件
        level=logging.DEBUG,
        format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

    return True


# 打开串口
def fd_open(uart, bps, timeout):
    try:
        # 打开串口，并得到串口对象
        fd = serial.Serial(uart, bps, timeout=timeout)
        # 判断是否打开成功
        if not fd.is_open:
           fd = -1
    except Exception as e:
        print("---异常---：", e)

    return fd


# 关闭串口
def fd_close(uartfd):
    uartfd.close()


# 写数据
def fd_write(uartfd, data):
    result = uartfd.write(data)  # 写数据
    return result


def crc_sum(data, data_len):
    crc = 0
    i = 0
    while(i < data_len):
        crc += data[i]
        i += 1
    return crc & 0x00FF


def crc_oxr(data, data_len):
    crc = 0
    i = 0
    while(i < data_len):
        crc ^= data[i]
        i += 1
    return crc & 0x00FF


# 十六进制显示
def hex_show(argv):
    result = ''
    hLen = len(argv)
    for i in range(hLen):
        hvol = argv[i]
        hhex = '%02x' % hvol
        result += hhex+' '

    return result


def send_file(ser, file, size, looptime):
    logging.info("send_file")
    with open(file, 'rb') as otafd:
        sendSize = 0
        # bin len
        otafd.seek(0, 0)  # 0代表从文件开头开始算起，1代表从当前位置开始算起，2代表从文件末尾算起。
        otafd.seek(0, 2)
        fileSize = otafd.tell()  # 读取总文件长度
        logging.info("total len:%x", fileSize)
        otafd.seek(0, 0)
        while (sendSize < fileSize):
            writebuf = bytearray([0xAA])
            otafd.seek(sendSize, 0)  # 0代表从文件开头开始算起，1代表从当前位置开始算起，2代表从文件末尾算起。
            readBuffer = otafd.read(size)
            writebuf.append(10 + len(readBuffer))
            writebuf.append(0x74)
            writebuf.append(0x00)
            writebuf.append(0x00)
            writebuf.append(0x00)
            writebuf.append(0x01)
            writebuf.append(0x00)
            writebuf.append(0xAA)
            writebuf.append(0x10)
            writebuf.append(0x22)
            # data len
            data_len = len(readBuffer) + 4
            writebuf.append(data_len)
            # image addr
            byte_hexlength = (sendSize & 0xFF000000) >> 24
            writebuf.append(byte_hexlength)
            byte_hexlength = (sendSize & 0xFF0000) >> 16
            writebuf.append(byte_hexlength)
            byte_hexlength = (sendSize & 0x00FF00) >> 8
            writebuf.append(byte_hexlength)
            byte_hexlength = (sendSize & 0x0000FF)
            writebuf.append(byte_hexlength)

            # image data
            i = 0
            while i < len(readBuffer):
                writebuf.append(readBuffer[i])
                i += 1

            # crc data
            i = 0
            crc_data = []
            while i < (8 + len(readBuffer)):
                crc_data.append(writebuf[8 + i])
                i += 1

            writebuf.append(crc_sum(crc_data, len(crc_data)))
            writebuf.append(0x16)
            writebuf.append(crc_oxr(writebuf, len(writebuf)))
            writebuf.append(0x55)

            fd_write(ser, writebuf)
            logging.info(writebuf.hex())
            sendSize += len(readBuffer)

            time.sleep(looptime)
        return True


if __name__ == '__main__':
    if 5 != len(sys.argv):
        print("please enter COM file size looptime(sec)")
        print("as:COM4 test.bin 8 3")
    else:
        uart.tty = sys.argv[1]
        uart.file = sys.argv[2]
        uart.size = int(sys.argv[3])
        uart.looptime = float(sys.argv[4])

    logging_init()

    uart.fd = fd_open(uart.tty, 115200, None)
    send_file(uart.fd, uart.file, uart.size, uart.looptime)
    fd_close(uart.fd)



