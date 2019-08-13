#### 0.环境
 - 版本：python3
 - 包：requests、json5、base64、xlwt

#### 1.运行
执行api.py后面添加static/dynamic即可运行
```
python api.py static
```
根据api.conf配置文件进行修改运行参数，如下：
```
[server]
host = http://192.168.18.1/zapi
passwd = admin

[test]
static_modules = wan
dynamic_modules = ligon_in
```
要测试那些模块在modules后面添加用,隔开即可，如下：
```
[test]
static_modules = wan,dhcp,lan
```

#### 2.添加测试模块
每增加一个模块需要添加两个json5文件，一个在input_json目录下，一个在output_json目录下，添加json模块的名称要一致，input_json下面代表要发送的请求，output_json下面代表预期返回的数据
```
input_json/wan.json5
output_json/wan.json5
```


json内部的数据以case为基础，一个case为一条list，list的命名要以test_开头，编号递增
```
test_001_get_wan
test_002_set_dhcp_auto_dns
test_003_set_dhcp_hand_dns
test_004_set_static
```

json5头部需要注明每个case的含义

|    单元测试      |post请求次数 |描述|
|------------------|-------------|----|
|test_001_get_wan  | 1 | 获取默认上网方式|
|test_002_set_dhcp_auto_dns  | 2 | 设置dhcp方式上网，自动获取dns|
|test_003_set_dhcp_hand_dns  | 2 | 设置dhcp方式上网，手动设置dns|
|test_004_set_static | 2 | 设置static方式上网，手动设置dns(静态无自动dns)|



#### 3.测试结果
测试完毕后会生成当前时间的api_test.xls报告文件和api_test.log日志文件
```
20190621_135232_api_test.xls
20190621_135232_api_test.log
```

#### 4.注意事项
##### 4.1 测试跟wan相关的api，需要先将设备恢复出厂设置，否则会有一些遗留的默认值导致output_json校验不对
##### 4.2 system接口会导致设备重启，会恢复出厂设置，所以放在最后一个测试
