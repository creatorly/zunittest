#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2019/10/21
# Describe：

import logging
import json
import paho.mqtt.client as mqtt
from paho.mqtt.client import Client


MQTTHOST = "link.t.zihome.com"
MQTTPORT = 6885
# MQTTHOST = "192.168.62.128"
# MQTTPORT = 1883
mqttClient: Client = mqtt.Client()


def logging_init():
    logging.basicConfig(  # filename="log/test.log", # 指定输出的文件
        level=logging.DEBUG,
        format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

    return True


# 连接MQTT服务器
def on_mqtt_connect():
    # mqtt.MQTT_ERR_SUCCESS = 0
    mqttClient.username_pw_set("client", "123456")
    # cacert.pem certificate.pfx
    mqttClient.tls_set(ca_certs="cacert.pem", certfile=None, keyfile=None, cert_reqs=mqtt.ssl.CERT_REQUIRED,
                       tls_version=mqtt.ssl.PROTOCOL_TLSv1, ciphers=None)
    mqttClient.tls_insecure_set(True)

    conn_result = mqttClient.connect(MQTTHOST, MQTTPORT, 15)
    logging.info(conn_result)
    mqttClient.loop_start()
    # mqttClient.loop_forever()


# publish 消息
def on_publish(topic, payload, qos):
    mqttClient.publish(topic, payload, qos)


# 消息处理函数
def on_message_come(lient, userdata, msg):
    print(msg.topic + " " + ":" + str(msg.payload))


# subscribe 消息
def on_subscribe():
    mqttClient.subscribe("local/iot/ziroom/+/+/notify", 1)
    mqttClient.on_message = on_message_come  # 消息到来处理函数


if __name__ == '__main__':
    logging_init()

    on_mqtt_connect()
    publish_data = {
        "msgType": "DEVICE_INFO_REPORT",
        "devId": "80987834",
        "prodTypeId": "KONGTIAO",
        "hardwareversion": "",
        "softversion": "0.0.1",
        "clientId": "XXXXX"
    }
    publist_result = on_publish("local/iot/ziroom/window/client1/notify", json.dumps(publish_data), 0)
    logging.info(publist_result)
    on_subscribe()
    while True:
        pass
