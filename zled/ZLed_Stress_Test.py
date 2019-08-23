import serial  # 导入模块
import threading
import time
import logging
import sys


class UartInfo(object):
    def __init__(self, fd, count, fail):
        self.fd = fd
        self.count = count  # 测试次数
        self.fail = fail  # 失败次数

    response = False


uart = UartInfo(-1, 0, 0)


def logging_init():
    logging.basicConfig(  # filename="log/test.log", # 指定输出的文件
        level=logging.DEBUG,
        format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

    return True


# 十六进制显示
def hex_show(argv):
    result = ''
    hLen = len(argv)
    for i in range(hLen):
        hvol = argv[i]
        hhex = '%02x'%hvol
        result += hhex+' '

    logging.info('Led Read:%s(%d)', result, hLen)


def crc_sum(data, data_len):
    crc = 0
    i = 0
    while(i < data_len):
        crc += data[i]
        i += 1
    return crc & 0x00FF


# 打开串口
def uart_open(uart, bps, timeout):
    try:
        # 打开串口，并得到串口对象
        ser = serial.Serial(uart, bps, timeout=timeout)
        # 判断是否打开成功
        if not ser.is_open:
           ser = -1
    except Exception as e:
        print("---异常---：", e)

    return ser


# 关闭串口
def uart_close(ser):
    uart.fdstate = -1
    ser.close()


# 写数据
def uart_write(ser, data):
    result = ser.write(data)  # 写数据
    return result


# 读数据
def Led2_4_ReadData(ser):
    # 循环接收数据，此为死循环，可用线程实现
    readstr = ""
    while(-1 != ser):
        if ser.in_waiting:
            try:  # 如果读取的不是十六进制数据--
                readbuf = ser.read(ser.in_waiting)
                if readbuf[0] == 0x55 and readbuf[1] == 0xaa:
                    readstr = readbuf
                else:
                    readstr = readstr + readbuf

                hex_show(readstr)
                if readbuf[3] == 0x20:
                    readstr = ''
                    print("disconnect")
                    continue
                elif len(readstr) > 25:
                    uart.response = True

            except:  # --则将其作为字符串读取
                readbuf = ser.read(ser.in_waiting)
                hex_show(readbuf)


# 设置power
def Led2_4_SetPower(ser, sn, power):
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

    count = uart_write(ser, writebuf)
    logging.info("Led Write %s(%d)" % (writebuf.hex(), count))


# 测试任务
def Led2_4_TestProcess(ser):
    # sn = {}
    # i = 0
    # while i < len(uart.sn):
    #     sn[i] = ord(uart.sn[i])
    #     i += 1
    # print(sn)

    sn = uart.sn.split(" ")
    i = 0
    while i < len(sn):
        sn[i] = int(sn[i], base=16)
        i += 1

    status = 1
    while (-1 != ser):
        uart.response = False
        logging.info("count:%d", uart.count)
        logging.info("fail:%d", uart.fail)
        if status == 1:
            status = 0
            Led2_4_SetPower(ser, sn, 0)
        else:
            status = 1
            Led2_4_SetPower(ser, sn, 1)

        time.sleep(2)
        uart.count += 1
        if not uart.response:
            time.sleep(1)
            if not uart.response:
                uart.fail += 1


def Led2_4_TestStop(ser):
    uart_close(uart.fd)  # 关闭串口


if __name__ == "__main__":
    if 3 != len(sys.argv):
        print("please enter COM sn")
        print("as:COM4 \"30 31 31 30 30 31 32 32 32 61\"")
        exit()
    else:
        uart.tty = sys.argv[1]
        uart.sn = sys.argv[2]

    logging_init()
    uart.fd = uart_open(uart.tty, 115200, None)

    if(uart.fd != -1):  # 判断串口是否成功打开
        threading.Thread(target=Led2_4_TestProcess, args=(uart.fd,)).start()
        threading.Thread(target=Led2_4_ReadData, args=(uart.fd,)).start()

