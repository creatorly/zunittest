#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2019/08/16
# Describe：wifi相关接口

import logging
import time
import pywifi


# 获取无线网卡接口
def get_wifi_interfaces():
    wifi = pywifi.PyWiFi()  # 创建一个无限对象
    num = len(wifi.interfaces())
    if num <= 0:
        logging.info("未找到无线网卡接口!\n")
        exit()
    if num == 1:
        wifi_iface = wifi.interfaces()[0]  # 取一个无限网卡
        logging.info(u"无线网卡接口: %s\n" % (wifi_iface.name()))
        return wifi_iface
    else:
        logging.info('%-4s   %s\n' % (u'序号', u'网卡接口名称'))
        for i, w in enumerate(wifi.interfaces()):
            logging.info('%-4s   %s' % (i, w.name()))
        while True:
            iface_no = input('请选择网卡接口序号：'.decode('utf-8').encode('gbk'))
            no = int(iface_no)
            if no >= 0 and no < num:
                return wifi.interfaces()[no]


# 扫描周围wifi
def scan_wifi(self):
    self.scan()   # 扫描
    time.sleep(3)
    wifi_info = self.scan_results()
    wifi_list = []
    for i in wifi_info:
        if i.signal > -90:  # 信号强度<-90的wifi几乎连不上
            wifi_list.append((i.ssid, i.signal, i.freq, i.bssid, i.akm))  # 添加到wifi列表
            logging.info("ssid: %s, 信号: %s, freq: %s, mac: %s, 加密方式: %s",
                         i.ssid.encode('raw_unicode_escape', 'strict').decode('utf-8'), i.signal, i.freq, i.bssid, i.akm)

    return sorted(wifi_list, key=lambda x: x[1], reverse=True)  # 按信号强度由高到低排序


# 查看无线网卡是否处于连接状态
def check_interfaces(self):
    if self.status() == pywifi.const.IFACE_CONNECTED:
        logging.info('无线网卡：%s 已连接。' % self.name())
        return True
    else:
        logging.info('无线网卡：%s 未连接。' % self.name())
        return False


# 连接wifi
def connect_wifi(self, profile_info):
    self.remove_all_network_profiles()  # 删除其他配置文件
    tmp_profile = self.add_network_profile(profile_info)  # 加载配置文件

    self.connect(tmp_profile)  # 连接
    time.sleep(8)  # 尝试8秒能否成功连接

    logging.info(self.status())
    if self.status() == pywifi.const.IFACE_CONNECTED:
        logging.info("成功连接")
        return True
    else:
        logging.info("失败")
        self.disconnect()  # 断开连接
        time.sleep(2)
        return False


# 断开无线网卡已连接状态
def disconnect_wifi(self):
    self.disconnect()
    time.sleep(2)
    if self.status() in [pywifi.const.IFACE_DISCONNECTED, pywifi.const.IFACE_INACTIVE]:
        logging.info(u'无线网卡：%s 已断开。' % self.name())
        return True
    else:
        logging.info(u'无线网卡：%s 未断开。' % self.name())
        return False


if __name__ == '__main__':
    print("请开始你的表演")
    pywifi.set_loglevel(logging.INFO)
