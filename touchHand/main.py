from pymodbus.client.sync import ModbusTcpClient  # pip3 install pymodbus==2.5.3
import time
import numpy as np
import cv2
import sys
# 寄存器字典
regdict = {
    'ID': 1000,
    'baudrate': 1001,
    'clearErr': 1004,
    'forceClb': 1009,
    'angleSet': 1486,
    'forceSet': 1498,
    'speedSet': 1522,
    'angleAct': 1546,
    'forceAct': 1582,
    'errCode': 1606,
    'statusCode': 1612,
    'temp': 1618,
    'actionSeq': 2320,
    'actionRun': 2322,
    'index': 4320,  #选定的触觉位置对应的初始地址
}


def open_modbus(ip, port):
    client = ModbusTcpClient(ip, port)
    client.connect()
    return client


def write_register(client, address, values):
    # Modbus 写入寄存器，传入寄存器地址和要写入的值列表
    client.write_registers(address, values)


def read_register(client, address, count):
    # Modbus 读取寄存器
    response = client.read_holding_registers(address, count)
    return response.registers if response.isError() is False else []

def write6(client, reg_name, val):
    if reg_name in ['angleSet', 'forceSet', 'speedSet']:
        val_reg = []
        for i in range(6):
            val_reg.append(val[i] & 0xFFFF)  # 取低16位
        write_register(client, regdict[reg_name], val_reg)
    else:
        print(
            '函数调用错误，正确方式：str的值为\'angleSet\'/\'forceSet\'/\'speedSet\'，val为长度为6的list，值为0~1000，允许使用-1作为占位符')

def read6(client, reg_name):
    # 检查寄存器名称是否在允许的范围内
    if reg_name in ['angleSet', 'forceSet', 'speedSet', 'angleAct', 'forceAct']:
        # 直接读取与reg_name对应的寄存器，读取的数量为6
        val = read_register(client, regdict[reg_name], 6)
        if len(val) < 6:
            print('没有读到数据')
            return
        print('读到的值依次为：', end='')
        for v in val:
            print(v, end=' ')
        print()

    elif reg_name in ['errCode', 'statusCode', 'temp']:
        # 读取错误代码、状态代码或温度，每次读取3个寄存器
        val_act = read_register(client, regdict[reg_name], 3)
        if len(val_act) < 3:
            print('没有读到数据')
            return

        # 初始化存储高低位的数组
        results = []

        # 将每个寄存器的高位和低位分开存储
        for i in range(len(val_act)):
            # 读取当前寄存器和下一个寄存器
            low_byte = val_act[i] & 0xFF  # 低八位
            high_byte = (val_act[i] >> 8) & 0xFF  # 高八位

            results.append(low_byte)  # 存储低八位
            results.append(high_byte)  # 存储高八位

        print('读到的值依次为：', end='')
        for v in results:
            print(v, end=' ')
        print()

    else:
        print(
            '函数调用错误，正确方式：str的值为\'angleSet\'/\'forceSet\'/\'speedSet\'/\'angleAct\'/\'forceAct\'/\'errCode\'/\'statusCode\'/\'temp\'')


def create_2d_array(m, n, elements):
    if len(elements) != m * n:
        raise ValueError("元素数量与指定的行数和列数不匹配")
    array_2d = np.array(elements).reshape(m, n)
    return array_2d

def read96(client, reg_name):
    if reg_name in ['index']:
        # 直接读取与reg_name对应的寄存器，读取的数量为96/80
        val = read_register(client, regdict[reg_name], 80)
        return val

def array_to_image(array):
    normalized_array = array / 2000.0
    red_channel = (normalized_array * 255).astype(np.uint8)
    image = np.zeros((10, 8, 3), dtype=np.uint8)
    image[:, :, 0] = red_channel
    return image

if __name__ == '__main__':
    ip_address = '192.168.11.210'
    port = 6000
    print('打开Modbus TCP连接！')
    client = open_modbus(ip_address, port)
    # print('设置灵巧手运动速度参数，-1为不设置该运动速度！')
    # write6(client, 'speedSet', [100, 100, 100, 100, 100, 100])
    # time.sleep(2)
    # print('设置灵巧手抓握力度参数！')
    # write6(client, 'forceSet', [500, 500, 500, 500, 500, 500])
    # time.sleep(1)
    # print('设置灵巧手运动角度参数0，-1为不设置该运动角度！')
    # write6(client, 'angleSet', [1000, 1000, 1000, 1000, 1000, 1000])
    time.sleep(1)
    # 设置图像放大倍数
    scale = 50
    cv2.namedWindow("Real-time Image", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Real-time Image", 10 * scale, 8 * scale)
    try:
        while True:
            val = read96(client, 'index')
            array = create_2d_array(10, 8, val)
            print(array)
            image = array_to_image(array)
            enlarged_image = cv2.resize(image, (10 * scale, 8 * scale), interpolation=cv2.INTER_NEAREST)
            cv2.imshow("Real-time Image", enlarged_image)
            # 等待 0.2 秒
            if cv2.waitKey(200) & 0xFF == ord('q'):  # 按 'q' 退出
                break
    except KeyboardInterrupt:
        print("程序已停止")

    cv2.destroyAllWindows()
    # 关闭 Modbus TCP 连接
    client.close()

