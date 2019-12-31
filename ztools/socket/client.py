#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2019/10/28
# Describe：

import socket
import time


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 建立连接:
conn_result = sock.connect(('192.168.18.1', 7777))
# conn_result = sock.connect(('127.0.0.1', 9999))
print(conn_result)
# 发送数据:
sock.send(b"KJHLKJHDLSKJHFLJSDHFLKJHDLKJH")
print(sock.recv(1024).decode('utf-8'))
time.sleep(2)
sock.send(b'exit')
time.sleep(2)
sock.close()
