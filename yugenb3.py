# pywebview
import webview
import serial
import serial.tools.list_ports
from scipy.fftpack import fft
import numpy as np
import math

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Circle


def getSerialPort(baudrate):
    """
    自动获取串口号
    :param baudrate: 波特率
    :return: 串口名
    """
    port_list = list(serial.tools.list_ports.comports())
    port_list_0 = list(port_list[0])
    port_serial = port_list_0[0]
    ser = serial.Serial(port_serial, baudrate, timeout=0.5)
    return ser

def circleFitting(points_x, points_y):
    # 最小二乘拟合圆
    sum_x = sum_y = 0
    sum_x2 = sum_y2 = 0
    sum_x3 = sum_y3 = 0
    sum_xy = sum_x1y2 = sum_x2y1 = 0

    N = 0
    if len(points_x) >= 3:
        for i in range(len(points_y)):
            x = points_x[i]
            y = points_y[i]

            N += 1
            x2 = x * x
            y2 = y * y
            sum_x += x
            sum_y += y
            sum_x2 += x2
            sum_y2 += y2
            sum_x3 += x2 * x
            sum_y3 += y2 * y
            sum_xy += x * y
            sum_x1y2 += x * y2
            sum_x2y1 += x2 * y
        C = N * sum_x2 - sum_x * sum_x
        D = N * sum_xy - sum_x * sum_y
        E = N * sum_x3 + N * sum_x1y2 - (sum_x2 + sum_y2) * sum_x
        G = N * sum_y2 - sum_y * sum_y
        H = N * sum_x2y1 + N * sum_y3 - (sum_x2 + sum_y2) * sum_y
        if (C * G - D * D) == 0:
            print('!!!error')
        a = (H * D - E * G) / (C * G - D * D)
        b = (H * C - E * D) / (D * D - G * C)
        c = -(a * sum_x + b * sum_y + sum_x2 + sum_y2) / N

        center_x = a / (-2)
        center_y = b / (-2)
        radius = math.sqrt(a * a + b * b - 4 * c) / 2
    radius = float("%.2f" % radius)
    center_x = float("%.2f" % center_x)
    center_y = float("%.2f" % center_y)
    return (center_x, center_y, radius)

class Api():
    def __init__(self):
        return
    def getData(self, params):
        ser = getSerialPort(921600)
        ser.write(b"start")
        # 验证头
        temp = ser.readall()
        if temp == b'\xb2\xe2\xca\xd4\r\n':
            print("----------start----------")
            while True:
                temp = ser.readall()
                if temp != b'':
                    if temp == b'\r\nover':
                        break
                    else:
                        data = temp  # 获得数据

        points = []  # 保存数据点
        for i in range(0, len(data), 2):
            dataHigh = hex(data[i])[2:]
            dataLow = hex(data[i + 1])[2:]
            if len(dataLow) == 1:
                dataLow = "0" + dataLow  # 前面补0
            num = int(dataHigh + dataLow, 16)
            points.append(num - 2058)

        points_temp = points.copy()
        points_min = min(points)
        while True:
            i = points_temp.index(min(points_temp))
            if points_temp[i] != points_min:
                break
            else:
                index = i
                points_temp[i] += 1
        points = [0] + points[index:]

        # 做差分
        diff = [points[i] - points[i + 1] for i in range(len(points) - 1)]

        f = np.conj(1 / fft(diff))
        res = 1.1 * 0.9 * 348800 * f
        res = res[2:2000]

        cir = circleFitting(res.real, res.imag)


        # 画图
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.scatter(res.real, res.imag, c='r', marker='.')
        plt.axis("equal")
        # plt.show()

        # 拟合圆
        print("radius:", cir[2])
        circle = Circle(xy=(cir[0], cir[1]), radius=cir[2], alpha=0.5)
        ax.add_patch(circle)
        plt.show()
        return cir[2]


if __name__ == "__main__":
    api = Api()
    webview.create_window("Window Title",
                          "./templates/index.html",
                          # fullscreen=True,
                          js_api=api)
    webview.start(gui='cef', debug=True)