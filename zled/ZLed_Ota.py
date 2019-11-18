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
    image_addr = 0x00
    image_crc = 0x00
    version = 0
    write_event = threading.Event()


uart = UartInfo(-1, 0, 0)


def logging_init():
    logging.basicConfig(#  filename="test.log", # 指定输出的文件
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
            hhex = '%02x' % hvol
            result += hhex+' '

        logging.info('Led Read:%s', result)
        return result
    except Exception as e:
        print("---异常---：", e)


def crc_sum(data, data_len):
    crc = 0
    i = 0
    while(i < data_len):
        crc += data[i]
        i += 1
    return crc & 0x00FF


def crc_sum_u32(data, data_len):
    crc = 0
    i = 0
    while(i < data_len):
        crc += data[i]
        i += 1
    return crc

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
    uart.fdstate = -1
    ser.close()


# 写数据
def DWritePort(ser, data):
    result = ser.write(data)  # 写数据
    logging.info(ser)
    logging.info("Led Write %s(%d)" % (data.hex(), result))
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

                hexShow(readstr)

                if (readstr[3] == 0x01) and (len(readstr) > 10):
                    uart.version = readstr[16]
                    uart.response = True
                    uart.write_event.set()
                elif (readstr[3] == 0x21) and (readstr[4] == 0x00) and (readstr[5] == 0x00):
                    uart.response = True
                    uart.write_event.set()
                elif (readstr[3] == 0x22) and (len(readstr) > 10):
                    uart.image_addr = (readstr[6] << 24 & 0xFF000000)
                    uart.image_addr += (readstr[7] << 16 & 0x00FF0000)
                    uart.image_addr += (readstr[8] << 8 & 0x0000FF00)
                    uart.image_addr += (readstr[9] << 0 & 0x000000FF)
                    uart.response = True
                    uart.write_event.set()
                elif (readstr[3] == 0x23) and (len(readstr) > 10):
                    uart.response = True
                    uart.write_event.set()

            except:  # --则将其作为字符串读取
                readbuf = ser.read(ser.in_waiting)
                hexShow(readbuf)


def Led2_4_GetVersion(ser):
    print("Led2_4_GetVersion")
    writebuf = bytearray([0x55, 0xaa, 0x00, 0x01, 0x00, 0x00])
    # crc
    writebuf.append(crc_sum(writebuf, len(writebuf)))
    DWritePort(ser, writebuf)

    logging.info("take")
    uart.response = False
    uart.write_event.clear()
    uart.write_event.wait(timeout=3)
    uart.write_event.clear()
    logging.info("give")
    if uart.response == False:
        logging.info("fail")
        return False
    else:
        return True

def Led2_4_GetOtaVersion():
    print("Led2_4_GetOtaVersion")
    with open(uart.otafile, 'rb') as otafd:
        otafd.seek(0, 0)
        otafd.seek(0, 2)

        if(otafd.tell() > 32):
            otafd.seek(0, 0)
            version = otafd.read(32)
            otafd.close()
            return True
        else:
            otafd.close()
            return False


def Led2_4_StartOta(ser, file):
    print("Led2_4_StartOta")
    with open(file, 'rb') as otafd:
        writebuf = bytearray([0x55, 0xaa, 0x00, 0x21])
        # data len
        writebuf.append(0x00)
        writebuf.append(0x24)
        # bin len
        otafd.seek(0, 0)  # 0代表从文件开头开始算起，1代表从当前位置开始算起，2代表从文件末尾算起。
        otafd.seek(0, 2)
        fileSize = otafd.tell() - 32  # 读取总文件长度,减去头部32
        byte_hexlength = (fileSize & 0xFF000000) >> 24
        writebuf.append(byte_hexlength)
        byte_hexlength = (fileSize & 0xFF0000) >> 16
        writebuf.append(byte_hexlength)
        byte_hexlength = (fileSize & 0x00FF00) >> 8
        writebuf.append(byte_hexlength)
        byte_hexlength = (fileSize & 0x0000FF)
        writebuf.append(byte_hexlength)
        # data
        otafd.seek(0, 0)
        readBuffer = otafd.read(32)
        i = 0
        while i < len(readBuffer):
            writebuf.append(readBuffer[i])
            i += 1
        # crc
        writebuf.append(crc_sum(writebuf, len(writebuf)))
        DWritePort(ser, writebuf)

        logging.info("take")
        uart.response = False
        uart.write_event.clear()
        uart.write_event.wait(timeout=30)
        uart.write_event.clear()
        logging.info("give")
        if uart.response == False:
            logging.info("fail")
            return False
        else:
            return True


def Led2_4_sendOta(ser, file):
    print("Led2_4_sendOta")
    with open(file, 'rb') as otafd:
        sendSize = 0
        # bin len
        otafd.seek(0, 0)  # 0代表从文件开头开始算起，1代表从当前位置开始算起，2代表从文件末尾算起。
        otafd.seek(0, 2)
        fileSize = otafd.tell() - 32  # 读取总文件长度

        otafd.seek(0, 0)
        while (sendSize < fileSize):
            writebuf = bytearray([0x55, 0xaa, 0x00, 0x22])

            otafd.seek(sendSize + 32, 0)  # 0代表从文件开头开始算起，1代表从当前位置开始算起，2代表从文件末尾算起。
            readBuffer = ""
            readBuffer = otafd.read(128)
            datalength = len(readBuffer) + 4
            # data len
            byte_hexlength = (datalength & 0xFF00) >> 8
            writebuf.append(byte_hexlength)
            byte_hexlength = (datalength & 0x00FF)
            writebuf.append(byte_hexlength)
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

            writebuf.append(crc_sum(writebuf, len(writebuf)))
            DWritePort(ser, writebuf)

            logging.info("take")
            uart.response = False
            uart.write_event.clear()
            uart.write_event.wait(timeout=30)
            uart.write_event.clear()
            logging.info("give")
            if uart.response == False:
                logging.info("fail")
                return False
            else:
                sendSize += len(readBuffer)
                uart.image_crc += crc_sum_u32(readBuffer, len(readBuffer))
                if uart.image_addr == sendSize:
                    continue
                else:
                    return False

        return True


def Led2_4_StopOta(ser):
    print("Led2_4_StopOta")
    writebuf = bytearray([0x55, 0xaa, 0x00, 0x23])

    # data len
    writebuf.append(0x00)
    writebuf.append(0x04)
    # image addr
    byte_hexlength = (uart.image_crc & 0xFF000000) >> 24
    writebuf.append(byte_hexlength)
    byte_hexlength = (uart.image_crc & 0xFF0000) >> 16
    writebuf.append(byte_hexlength)
    byte_hexlength = (uart.image_crc & 0x00FF00) >> 8
    writebuf.append(byte_hexlength)
    byte_hexlength = (uart.image_crc & 0x0000FF)
    writebuf.append(byte_hexlength)
    writebuf.append(crc_sum(writebuf, len(writebuf)))
    DWritePort(ser, writebuf)

    logging.info("take")
    uart.response = False
    uart.write_event.clear()
    uart.write_event.wait(timeout=30)
    uart.write_event.clear()
    logging.info("give")
    if uart.response == False:
        logging.info("fail")
        return False
    else:
        return True

# 测试任务
def Led2_4_TestProcess(ser):
    while (-1 != ser):
        uart.response = False
        uart.image_addr = 0x00
        uart.image_crc = 0x00
        uart.version = 0

        if Led2_4_GetVersion(ser):
            logging.info(uart.version)

        print("ota:", uart.otafile)
        logging.info("ota:%s", uart.otafile)
        time.sleep(2)

        if not Led2_4_StartOta(ser, uart.otafile):
            logging.info("fail")
            break


        if not Led2_4_sendOta(ser, uart.otafile):
            logging.info("fail")
            break

        time.sleep(2)
        if not Led2_4_StopOta(ser):
            logging.info("fail")
            break

        time.sleep(2)

        logging.info("ota ok")
        break


def Led2_4_TestStop(ser):
    DColsePort(uart.fd)  # 关闭串口


if __name__ == "__main__":
    if 3 != len(sys.argv):
        print("please enter COM ota")
        exit()
    else:
        uart.tty = sys.argv[1]
        uart.otafile = sys.argv[2]

    logging_init()
    uart.fd = DOpenPort(uart.tty, 115200, None)

    if(uart.fd != -1):  # 判断串口是否成功打开
        threading.Thread(target=Led2_4_TestProcess, args=(uart.fd,)).start()
        threading.Thread(target=Led2_4_ReadData, args=(uart.fd,)).start()

