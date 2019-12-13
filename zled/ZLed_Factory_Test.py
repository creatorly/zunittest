#!/usr/bin/python

import sys
import serial
import threading
import time
import logging
import msvcrt


class UartInfo(object):
    def __init__(self, fd):
        self.fd = fd

    tty = 0
    response = False
    step = 0
    sn = {}
    write_event = threading.Event()


uart = UartInfo(-1)


def logging_init():
    logging.basicConfig(  # filename="log/test.log", # 指定输出的文件
        level=logging.DEBUG,
        format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

    return True


# 十六进制显示
def hexShow(argv):
    try:
        result = ''
        hLen = len(argv)
        for i in range(hLen):
            hvol = argv[i]
            hhex = '%02x'%hvol
            result += hhex+' '

        logging.info('Led Read:%s', result)
        return result
    except Exception as e:
        print("---异常---：", e)


def crc_sum(puchMsg, usDataLen):
    sum = 0
    i = 0
    while(i < usDataLen):
        sum += puchMsg[i]
        i += 1
    return sum & 0x00FF


# 打开串口
def DOpenPort(portx, bps, timeout):
    try:
        # 打开串口，并得到串口对象
        ser = serial.Serial(portx, bps, timeout=timeout)
        # 判断是否打开成功
        if(False == ser.is_open):
           ser = -1
    except Exception as e:
        print("---异常---：", e)

    return ser


# 关闭串口
def DColsePort(ser):
    uart.fd = -1
    ser.close()


# 写数据
def DWritePort(ser, data):
    result = ser.write(data)  # 写数据
    logging.info(ser)
    logging.info("Led Write %s(%d)" % (data.hex(), result))
    return result


def start_add_light(ser):
     # 55 AA 00 06 00 00 05
    writebuf = bytearray([0x55, 0xaa, 0x00, 0x06, 0x00, 0x00])
    writebuf.append(crc_sum(writebuf, len(writebuf)))
    DWritePort(ser, writebuf)


def stop_add_light(ser):
    writebuf = bytearray([0x55, 0xaa, 0x00, 0x07, 0x00, 0x00])

    writebuf.append(crc_sum(writebuf, len(writebuf)))

    DWritePort(ser, writebuf)


def send_add_ack(ser):
    writebuf = bytearray([0x55, 0xaa, 0x00, 0x08, 0x00, 0x00])

    writebuf.append(crc_sum(writebuf, len(writebuf)))
    DWritePort(ser, writebuf)

    stop_add_light(ser)

    time.sleep(15)
    logging.info("start control")
    uart.step = 0x0c
    uart.response = True
    uart.write_event.set()


def send_set_power(ser, sn, power):
    # 55 AA 00 0C 00 12 00 00 0A 30 31 31 30 30 31 32 32 32 61 01 01 00 01 00 44
    writebuf = bytearray([0x55, 0xaa, 0x00, 0x0C, 0x00, 0x12, 0x00, 0x00, 0x0A])

    i = 0
    while i < len(sn):
        writebuf.append(sn[i])
        i += 1

    if power == 1:
        setpower = [0x01, 0x01, 0x00, 0x01, 0x01]
        i = 0
        while i < len(setpower):
            writebuf.append(setpower[i])
            i += 1
    else:
        setpower = [0x01, 0x01, 0x00, 0x01, 0x00]
        i = 0
        while i < len(setpower):
            writebuf.append(setpower[i])
            i += 1

    writebuf.append(crc_sum(writebuf, len(writebuf)))

    DWritePort(ser, writebuf)


def start_del_light(ser, sn):
    # 55 AA 00 09 00 17 7B 22 73 75 62 5F 69 64 22 3A 22 30 31 31 30 30 31 32 37 35 38 22 7D 47
    #  30 31 31 30 30 30 31 38 31 39
    writebuf = bytearray([0x55, 0xaa, 0x00, 0x09, 0x00, 0x17, 0x7b, 0x22, 0x73, 0x75, 0x62, 0x5f, 0x69, 0x64, 0x22, 0x3a, 0x22])
    i = 0
    while i < len(sn):
        writebuf.append(sn[i])
        i += 1

    writebuf.append(0x22)
    writebuf.append(0x7d)
    writebuf.append(crc_sum(writebuf, len(writebuf)))
    DWritePort(ser, writebuf)


# 读数据
def uart_read_data(ser):
    logging.info("uart_read_data")
    # 循环接收数据，此为死循环，可用线程实现
    readstr = ""
    while (-1 != ser):
        if ser.in_waiting:
            logging.info(ser)
            readbuf = ser.read(ser.in_waiting)
            if readbuf[0] == 0x55 and readbuf[1] == 0xaa:
                readstr = readbuf
            else:
                readstr = readstr + readbuf

            hexShow(readstr)
            # logging.info("step:%d", uart.step)
            # logging.info("len:%d", len(readstr))
            if uart.step == 0:
                if (readstr[3] == 0x08) and (len(readstr) > 70):
                    uart.sn[0] = readstr[29]
                    uart.sn[1] = readstr[30]
                    uart.sn[2] = readstr[31]
                    uart.sn[3] = readstr[32]
                    uart.sn[4] = readstr[33]
                    uart.sn[5] = readstr[34]
                    uart.sn[6] = readstr[35]
                    uart.sn[7] = readstr[36]
                    uart.sn[8] = readstr[37]
                    uart.sn[9] = readstr[38]
                    logging.info("add succuss")
                    uart.step = 0x08
                    uart.response = True
                    uart.write_event.set()

            elif uart.step == 0x0c:
                if (readstr[3] == 0x0D) and (len(readstr) > 25):
                    logging.info("control success")
                    uart.step = 0x09
                    uart.response = True
                    uart.write_event.set()
            elif uart.step == 0x09:
                if readbuf[3] == 0x09:
                    if uart.fd == 1:
                        uart.fd = 2
                    elif uart.fd == 2:
                        uart.fd = 1

                    logging.info("del succuss")
                    uart.step = 0
                    uart.response = True
                    uart.write_event.set()


# 测试任务
def uart_send_data(ser):
    while (-1 != ser):
        if uart.step == 0:
            time.sleep(1)
            logging.info("输入Enter键开始。。。")
            enter_key = msvcrt.getch()
            if 13 == ord(enter_key):
                logging.info("开始测试")
            else:
                continue

            stop_add_light(ser)
            time.sleep(1)
            start_add_light(ser)
        elif uart.step == 0x08:
            send_add_ack(ser)
            continue
        elif uart.step == 0x0c:
            send_set_power(ser, uart.sn, 0)
        elif uart.step == 0x09:
            start_del_light(ser, uart.sn)

        logging.info("take")
        uart.response = False
        uart.write_event.clear()
        uart.write_event.wait(timeout=30)
        uart.write_event.clear()
        logging.info("give")
        if uart.response == False:
            logging.info("测试失败")
            uart.step = 0


if __name__ == "__main__":
    if 2 != len(sys.argv):
        print("please enter COM")
        exit()
    else:
        uart.tty = sys.argv[1]

    uart.step = 0
    logging_init()
    uart.fd = DOpenPort(uart.tty, 115200, None)
    logging.info(uart.fd)
    if(uart.fd != -1):  # 判断串口是否成功打开
        threading.Thread(target=uart_read_data, args=(uart.fd,)).start()
        threading.Thread(target=uart_send_data, args=(uart.fd,)).start()
