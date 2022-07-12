import sys
import random
from PySide2 import QtCore, QtWidgets, QtGui
from multiprocessing import Process

"""
定义状态码：
    -1: 队列满了
    1: 队列空了
    0: 添加成功

"""


# 循环队列
class Queue:
    def __init__(self, max_size):
        self.max_size = max_size + 1  # 容量 循环队列需要空出一个位置
        self.queue = [None] * self.max_size  # 队列
        self.front = 0
        self.rear = 0

    # 队列长度
    def size(self):
        return (self.rear - self.front + self.max_size) % self.max_size

    # 判断是否为空
    def is_empty(self):
        return self.rear == self.front

    # 判断是否满
    def is_full(self):
        return (self.rear + 1) % self.max_size == self.front

    # 添加元素
    def put(self, item):
        if self.is_full():
            return -1
        self.queue[self.rear] = item
        self.rear = (self.rear + 1) % self.max_size
        return 0

    # 删除元素
    def pop(self):
        if self.is_empty():
            return 1  # 队列空了
        item = self.queue[self.front]
        self.queue[self.front] = None
        self.front = (self.front + 1) % self.max_size
        return item

    # 查看队头元素
    def get_item(self):
        if self.is_empty():
            return 1
        return self.queue[self.front]


def message_dialog(type, msg):
    msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, type, msg)
    msg_box.exec_()


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # 数据元素
        self.K = 0  # K个理发师
        self.L = -1  # 长凳上可以容纳等待人的数量。为0表示不能等待，一来就直接理发
        self.t_start = -1  # 理发店开店时间，整型数字模拟表示
        self.t_end = -1  # 理发店关店时间，整型数字表示。必须满足t_start < t_end
        self.queue = Queue(max_size=0)  # 等待队列
        self.current_time = 0  # 当前开始时间
        self.no = 0  # 顾客编号
        self.notice = []  # 顾客处理结果的数组，保存每一个顾客i的处理结果信息

        self.barberEdit = QtWidgets.QLineEdit()
        self.waitEdit = QtWidgets.QLineEdit()
        self.startEdit = QtWidgets.QLineEdit()
        self.endEdit = QtWidgets.QLineEdit()

        self.initUi()
        self.controller()

    # 初始化界面
    def initUi(self):
        # 页面元素
        barber = QtWidgets.QLabel("理发师人数：")
        wait_num = QtWidgets.QLabel("等待容量：")
        start = QtWidgets.QLabel("开店时间：")
        end = QtWidgets.QLabel("关店时间：")

        # 初始值占位符
        # self.barberEdit.setPlaceholderText(str(self.K))
        # self.waitEdit.setPlaceholderText(str(self.L))
        # self.startEdit.setPlaceholderText(str(self.t_start))
        # self.endEdit.setPlaceholderText(str(self.t_end))

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(barber, 1, 0)
        grid.addWidget(self.barberEdit, 1, 1)

        grid.addWidget(wait_num, 1, 2)
        grid.addWidget(self.waitEdit, 1, 3)

        grid.addWidget(start, 1, 4)
        grid.addWidget(self.startEdit, 1, 5)

        grid.addWidget(end, 1, 6)
        grid.addWidget(self.endEdit, 1, 7)

        addButton = QtWidgets.QPushButton("Add Guest!")
        grid.addWidget(addButton, 2, 0)

        wait_list = QtWidgets.QLabel("等待队列：")
        waitListEdit = QtWidgets.QListView()

        grid.addWidget(wait_list, 3, 0)
        grid.addWidget(waitListEdit, 4, 0)

        res = QtWidgets.QLabel("理发通告：")
        resEdit = QtWidgets.QListView()

        grid.addWidget(res, 3, 3)
        grid.addWidget(resEdit, 4, 3)

        self.setLayout(grid)
        # 触发事件
        addButton.clicked.connect(self.producer)

    # 消息提示框

    # 初始化数据
    def init_data(self):
        k = self.barberEdit.text()
        l = self.waitEdit.text()
        start = self.startEdit.text()
        end = self.endEdit.text()
        if k and l and start and end:
            self.K = int(k)
            self.L = int(l)
            self.t_start = int(start)
            self.t_end = int(end)
            self.queue = Queue(max_size=self.L)  # 初始化顾客等待队列
            self.current_time = self.t_start  # 下一个顾客到达的最小时间
            return True
        else:
            message_dialog("参数错误", "初始参数不能为空！")
            return False

    # 随机生成顾客--生产者方法
    def producer(self):
        self.init_data()
        # 随机生成顾客i的到达时间和理发时间
        t_arv_i = self.current_time + random.randint(1, self.t_end)  # 到达时间, 原则上到达时间应该在开店期间，不然也没有处理的意义
        t_cut_i = random.randint(5, 30)  # 剪发时间, 假设在5-30的一个随机数
        self.current_time = self.current_time + t_arv_i  # 下一个到来时间应该在当前时间之后
        self.queue.put([self.no, t_arv_i, t_cut_i])  # 添加在队列中
        self.no = self.no + 1
        print("生产者：", [self.no, t_arv_i, t_cut_i])

    #  消费者方法
    def consumer(self):
        if not self.queue.is_empty():  # 队列非空
            current_guest = self.queue.get_item()
            print("消费者：", current_guest)

    def controller(self):
        if self.init_data():
            if self.K <= 0:
                message_dialog("参数错误", '理发师人数必须大于0！')
            if self.L < 0:
                message_dialog("参数错误", "等待容量不能小于0！")
            if self.t_start < 0:
                message_dialog("参数错误", "开店时间不能小于0！")
            if self.t_end < 0:
                message_dialog("参数错误", "关店时间不能小于0！")
            if self.t_start >= self.t_end:
                message_dialog("参数错误", "开店时间必须小于关店时间！")
            # 启动进程
            p = Process(target=self.producer)
            c = Process(target=self.consumer)
            p.start()
            c.start()


# 运行窗口
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    app.setApplicationName("理发店模拟")
    widget = MyWidget()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec_())
