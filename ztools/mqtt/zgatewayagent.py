#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author: ye.lin
# Time: 2019/10/21
# Describe：

import logging
import json
import time
import paho.mqtt.client as mqtt


MQTTHOST = "192.168.18.1"
MQTTPORT = 6885

CLINET_TOPIC_OFFLINE = "local/iot/ziroom/onoffline"
CLINET_TOPIC_BROADCAST = "local/iot/ziroom/broadcast"
CLINET_TOPIC_CONTROL = "local/iot/ziroom/PYTHON/112233445566/control"
CLINET_TOPIC_NOTIFY = "local/iot/ziroom/PYTHON/112233445566/notify"
CLINET_TOPIC_QOS = 1

mqttClient = mqtt.Client("ZGATEWAY_PYTHON")


def logging_init():
    logging.basicConfig(  # filename="log/test.log", # 指定输出的文件
        level=logging.DEBUG,
        format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

    return True


# 连接MQTT服务器
def on_mqtt_connect():
    will_payload = {
        "msgType":      "DEVICE_DISCONNECT",
        "devId":        "112233445566",
        "prodTypeId":   "PYTHON",
        "swVersion":    "1.63",
        "hwVersion":    "1.00"
}

    # mqtt.MQTT_ERR_SUCCESS = 0
    mqttClient.username_pw_set("python", "python")
    # cacert.pem certificate.pfx
    mqttClient.tls_set(ca_certs="zgateway_cacert.pem", certfile=None, keyfile=None, cert_reqs=mqtt.ssl.CERT_REQUIRED,
                       tls_version=mqtt.ssl.PROTOCOL_TLSv1, ciphers=None)
    mqttClient.tls_insecure_set(True)
    mqttClient.will_set(CLINET_TOPIC_OFFLINE, payload=json.dumps(will_payload), qos=CLINET_TOPIC_QOS)
    mqttClient.on_connect = on_connect
    mqttClient.on_disconnect = on_disconnect
    mqttClient.on_message = on_message_come
    mqttClient.connect(MQTTHOST, MQTTPORT, 60)


def publish_device_info():
    info_payload = {
        "msgType":      "DEVICE_INFO_REPORT",
        "devId":        "112233445566",
        "prodTypeId":   "PYTHON",
        "softversion":    "1.63",
        "hardwareversion":    "1.00"
    }
    mqttClient.publish(CLINET_TOPIC_NOTIFY, payload=json.dumps(info_payload), qos=CLINET_TOPIC_QOS)


def on_disconnect(client, userdata, rc):
    print("mqtt broker lost "+str(rc))
    while mqttClient.reconnect() != 0:
        time.sleep(0.2)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    mqttClient.subscribe(CLINET_TOPIC_BROADCAST, qos=CLINET_TOPIC_QOS)
    mqttClient.subscribe(CLINET_TOPIC_CONTROL, qos=CLINET_TOPIC_QOS)
    publish_device_info()


# 消息处理函数
def on_message_come(lient, userdata, msg):
    print(msg.topic + " " + ":" + str(msg.payload))


if __name__ == '__main__':
    logging_init()
    on_mqtt_connect()
    mqttClient.loop_forever()

