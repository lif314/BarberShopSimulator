import simpy
from PySide2.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QTableWidget, QPushButton, QApplication, QVBoxLayout, \
    QTableWidgetItem, QCheckBox, QAbstractItemView, QHeaderView, QLabel, QFrame
from PySide2 import QtWidgets, QtCore
from PySide2.QtCore import Qt
from builtins import super, str, range
from PySide2.QtGui import QFont, QColor
from faker import Factory
import random, sys, operator

RANDOM_SEED = 42  # 随机种子
record = []  # 自动模拟记录


# 循环队列
class Queue:
    """
    定义状态码：
        -1: 队列满了
        1: 队列空了
        0: 添加成功
    """

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


# 模拟理发店
class BarberShop(object):
    """理发店中理发师数量(NUM_BARBERS)有限，并行为顾客理发。
    顾客和理发师配对时，将占用CUT_TIME，等结束后，释放理发师
    """

    def __init__(self, env, num_barbers):
        self.env = env
        self.barber = simpy.Resource(env, num_barbers)

    # 剪发
    def cut(self, guest, cut_time):
        """理发过程中，花费CUT_TIME占用该process"""
        yield self.env.timeout(cut_time)
        print("Barbershop cut %d%% of %s's hairs." %
              (random.randint(50, 99), guest))


# 模拟理发师
class Barber(object):
    def __init__(self, id, state, time):
        self.id = id
        self.state = state  # 0表示空着，1表示正在工作
        self.time = time


# 模拟顾客
def schedule_guest(env, t_start, name, cut_time, bs):
    """每个顾客到达理发店(bs)请求一个理发师，如果等待队列满了，则离开"""
    print('%s arrives at the barbershop at %.2f.' % (name, t_start + env.now))
    record.append('%s arrives at the barbershop at %.2f.\n' % (name, t_start + env.now))
    with bs.barber.request() as request:
        yield request

        print('%s enters the barbershop at %.2f.' % (name, t_start + env.now))
        record.append('%s enters the barbershop at %.2f.\n' % (name, t_start + env.now))
        yield env.process(bs.cut(name, cut_time))
        record.append('%s takes %.2f.\n' % (name, cut_time))

        print('%s leaves the barbershop at %.2f.' % (name, t_start + env.now))
        record.append('%s leaves the barbershop at %.2f.\n' % (name, t_start + env.now))


def setup(env, num_barbers, t_start, t_inter):
    """配置理发店：理发师个数，剪头发时间，每隔多长时间添加一个顾客"""
    # 创建一个理发店
    barbershop = BarberShop(env, num_barbers)

    # 随机创建4个初始的顾客
    for i in range(random.randint(3, 10)):
        env.process(schedule_guest(env, t_start, 'Guest %d' % i, random.randint(1, 10), barbershop))

    # 当进行理发时，随机创建更多的顾客
    while True:
        yield env.timeout(random.randint(t_inter - 2, t_inter + 2))
        i += 1
        env.process(schedule_guest(env, t_start, 'Guest %d' % i, random.randint(1, 10), barbershop))


# 定义每个顾客基本数据结构
class Guest:
    def __init__(self, name, arrive_time, serve_time, ready=False, over=False):
        self.name = name  # 顾客名称
        self.arrive_time = arrive_time  # 到达时间
        self.serve_time = serve_time  # 服务时间
        self.left_serve_time = serve_time  # 剩余需要服务的时间
        self.finish_time = 0  # 完成时间
        self.pre_queue = 0  # 定义现在所在的队列
        self.pre_queue_tb = 0  # 目前所在队列的时间片
        self.used_time = 0  # 已经使用的时间，也就是（服务时间 - 剩余服务时间）
        self.ready = ready  # 记录就绪状态
        self.over = over  # 记录完成状态


# 消息提示
def message_dialog(type, msg):
    msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, type, msg)
    msg_box.exec_()


class ui(QWidget):
    def __init__(self):
        super(ui, self).__init__()
        self.id = 1
        self.lines = []
        self.editable = True
        self.des_sort = True
        self.faker = Factory.create()
        self.env = simpy.Environment()  # 模拟环境

        # 全局参数
        self.NUM_BARBERS = 2  # 理发师数量
        self.CUT_TIME = 5  # 理发花费时间(min)
        self.NUM_WAITING = 5  # 等待容量
        self.T_INTER = 7  # 每个大约7min随机创造一个顾客
        self.T_START = 0  # 开店时间
        self.T_END = 20  # 关店时间
        self.SIM_TIME = self.T_END - self.T_START  # 模拟时间间隔
        self.barbershop = None  # 模拟理发店

        self.current_time = self.T_START

        self.barberEdit = QtWidgets.QLineEdit()
        self.waitEdit = QtWidgets.QLineEdit()
        self.startEdit = QtWidgets.QLineEdit()
        self.endEdit = QtWidgets.QLineEdit()

        self.setupUI()

        self.btn_setting.clicked.connect(self.init_data)  # 配置理发店初始参数
        self.btn_add.clicked.connect(self.add_line)
        self.btn_del.clicked.connect(self.del_line)
        self.btn_modify.clicked.connect(self.modify_line)
        self.btn_set_middle.clicked.connect(self.middle)
        self.btn_get_info.clicked.connect(self.hand_sim)
        self.btn_auto_info.clicked.connect(self.auto_sim)

        self.table.cellChanged.connect(self.cell_change)

        global original_processes  # 这里我们定义全局变量 - 原始进程列表，是一个二维列表

    def setupUI(self):
        self.setWindowTitle('理发店模拟')
        self.resize(906, 640)

        self.table = QTableWidget(self)

        # 初始参数设置
        self.barber = QtWidgets.QLabel("理发师人数：")
        self.wait_num = QtWidgets.QLabel("等待容量：")
        self.start = QtWidgets.QLabel("开店时间：")
        self.end = QtWidgets.QLabel("关店时间：")

        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)

        self.grid.addWidget(self.barber, 1, 0)
        self.grid.addWidget(self.barberEdit, 1, 1)

        self.grid.addWidget(self.wait_num, 1, 2)
        self.grid.addWidget(self.waitEdit, 1, 3)

        self.grid.addWidget(self.start, 1, 4)
        self.grid.addWidget(self.startEdit, 1, 5)

        self.grid.addWidget(self.end, 1, 6)
        self.grid.addWidget(self.endEdit, 1, 7)

        self.btn_setting = QPushButton('配置参数')
        self.btn_add = QPushButton('增加')
        self.btn_del = QPushButton('删除')
        self.btn_modify = QPushButton('可以编辑')
        self.btn_set_middle = QPushButton('文字居中')
        self.btn_get_info = QPushButton('静态模拟')
        self.btn_auto_info = QPushButton('自动模拟')

        # 弹簧控件
        self.spacerItem = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        # 垂直布局，使用嵌套布局方式
        # 我们把所有按钮按照盒布局-垂直布局方式，构成嵌套布局的一个块
        # 按照设置的方式依此从上到下
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.btn_setting)
        self.vbox.addWidget(self.btn_add)
        self.vbox.addWidget(self.btn_del)
        self.vbox.addWidget(self.btn_modify)
        self.vbox.addWidget(self.btn_set_middle)
        self.vbox.addWidget(self.btn_get_info)
        self.vbox.addWidget(self.btn_auto_info)
        self.vbox.addSpacerItem(self.spacerItem)

        self.txt = QLabel()  # 这是进行操作时显示在最左下角的提示信息
        self.txt.setMinimumHeight(50)  # 限定控件大小

        self.lab_over = QLabel('调度信息')  # 输出队列顺序
        self.lab_over.setMinimumHeight(20)
        self.over_Edit = QtWidgets.QTextEdit(self)
        self.over_Edit.setMinimumHeight(25)

        # 垂直布局
        # 把表格和下面的操作提示文本信息按照垂直布局设置，作为嵌套布局方式的另一部分
        self.vbox2 = QVBoxLayout()
        self.vbox2.addWidget(self.table)  # 将表格和下面的操作提示放入垂直布局，先放表格
        self.vbox2.addWidget(self.lab_over)  # 放输出队列
        self.vbox2.addWidget(self.over_Edit)

        self.vbox2.addWidget(self.txt)  # 再放文本框

        # 水平布局
        # 这是将上述两个布局方式作为整体布局的元素，vbox和vbox2共同放入水平布局
        self.hbox = QHBoxLayout()
        self.hbox.addLayout(self.vbox2)  # 将这样就会自左向右，先放表格，
        self.hbox.addLayout(self.vbox)  # 再放按钮

        # 垂直布局
        self.vbox3 = QVBoxLayout()
        self.vbox3.addLayout(self.grid)
        self.vbox3.addLayout(self.hbox)

        # 将垂直布局放入总体布局
        self.setLayout(self.vbox3)

        # 表格基本属性设置
        self.table.setColumnCount(5)  # 设置列数
        self.table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignCenter)
        self.headers = ['ID', '选择', '顾客名', '到达时间', '服务时间']  # 设置每列标题
        self.table.setHorizontalHeaderLabels(self.headers)  # 导入
        self.table.verticalHeader().setVisible(False)  # 隐藏垂直表头
        self.show()

    # 初始化全局参数
    def init_data(self):
        k = self.barberEdit.text()
        l = self.waitEdit.text()
        start = self.startEdit.text()
        end = self.endEdit.text()
        if k and l and start and end:
            if int(k) <= 0:
                message_dialog("参数错误", '理发师人数必须大于0！')
            else:
                self.NUM_BARBERS = int(k)
            if int(l) < 0:
                message_dialog("参数错误", "等待容量不能小于0！")
            else:
                self.NUM_WAITING = int(l)
            if int(start) < 0:
                message_dialog("参数错误", "开店时间不能小于0！")
            else:
                self.T_START = int(start)
            if int(end) < 0:
                message_dialog("参数错误", "关店时间不能小于0！")
            else:
                self.T_END = int(end)
            if int(end) <= int(start):
                message_dialog("参数错误", "开店时间必须小于关店时间！")
            else:
                self.SIM_TIME = self.T_END - self.T_START
                self.current_time = self.T_START
            # 清空面板数据
            self.over_Edit.setText("")
        else:
            message_dialog("参数错误", "参数不能为空")

    # 添加行
    def add_line(self):
        if self.current_time >= self.T_END:
            return
        self.table.cellChanged.disconnect()
        row = self.table.rowCount()  # 获取目前所有行的数量
        self.table.setRowCount(row + 1)
        id = str(self.id)

        # 生成复选框， 并设置居中显示
        ck = QCheckBox()
        h = QHBoxLayout()
        h.setAlignment(Qt.AlignCenter)
        h.addWidget(ck)
        w = QWidget()
        w.setLayout(h)

        # 变量由faker自动生成
        name = self.faker.name()
        arr_time = str(random.randint(self.current_time, self.T_END))  # 到达时间
        ser_time = str(random.randint(0, 9))  # 服务时间

        # 设置新建行的数据
        self.table.setItem(row, 0, QTableWidgetItem(id))
        self.table.setCellWidget(row, 1, w)
        self.table.setItem(row, 2, QTableWidgetItem(name))
        self.table.setItem(row, 3, QTableWidgetItem(arr_time))
        self.table.setItem(row, 4, QTableWidgetItem(ser_time))

        self.id += 1  # 设置完不要忘记id加一
        self.current_time = int(arr_time)  # 重置当前时间
        self.lines.append([id, ck, name, arr_time, ser_time])
        self.set_text('自动生成随机一行数据！,checkbox设置为居中显示')
        self.table.cellChanged.connect(self.cell_change)

    # 删除行
    def del_line(self):
        removeline = []
        for line in self.lines:
            if line[1].isChecked():
                row = self.table.rowCount()
                for x in range(row, 0, -1):
                    if line[0] == self.table.item(x - 1, 0).text():
                        self.table.removeRow(x - 1)
                        removeline.append(line)
        for line in removeline:
            self.lines.remove(line)
        self.set_text('删除checkbox中选中状态的行')
        self.current_time = self.T_START  # 初始化时间

    # 编辑
    def modify_line(self):
        if self.editable == True:
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.btn_modify.setText('禁止编辑')
            self.editable = False
        else:
            self.table.setEditTriggers(QAbstractItemView.AllEditTriggers)
            self.btn_modify.setText('可以编辑')
            self.editable = True
        self.set_text('设置是否可以编辑表格信息')

    # 文字居中显示
    def middle(self):
        row = self.table.rowCount()
        for x in range(row):
            for y in range(5):
                if y != 1:
                    item = self.table.item(x, y)
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    pass
        self.set_text('将文字居中显示')

    # 改变表格数据
    def cell_change(self, row, col):
        item = self.table.item(row, col)
        txt = item.text()
        self.set_text('第%s行，第%s列 , 数据改变为:%s' % (row, col, txt))

    # 先来先服务作业调度算法
    def fcfs(self, over_list):  # 到达时间小的优先
        # 创建理发师数组
        barbers = []
        for i in range(self.NUM_BARBERS):
            barbers.append(Barber(i, 0, self.T_START))
        # 等待队列
        waiting_queue = Queue(max_size=self.NUM_WAITING)

        for cur_time in range(self.T_START, self.T_END):
            for i in range(len(over_list)):
                # 无法按时完成理发，直接离开
                if over_list[i].arrive_time + over_list[i].serve_time >= self.T_END:
                    self.over_Edit.append(over_list[i].name + 'arrives the barbershop at ' + str(
                        over_list[i].arrive_time) + ' ,and left without a haircut.')

    # 手动模拟
    def hand_sim(self):
        # 我们每次使用这个功能时先把全变量原始进程列表 -- original_processes --清空好吧
        original_processes = []
        row = self.table.rowCount()

        # 获取顾客数据
        for j in range(row):
            na = self.table.item(j, 2).text()
            at = int(self.table.item(j, 3).text())
            st = int(self.table.item(j, 4).text())
            p = Guest(na, at, st)
            original_processes.append(p)

        '''
        由于第一个进程不一定就是到达时间最短的进程，所以我们先按照
        到达时间给进程排个序
        '''
        _sorted_processes = original_processes[:]
        _sorted_processes.sort(key=operator.attrgetter('arrive_time'))

        self.fcfs(_sorted_processes)
        # self.over_Edit.setText(infor_list)
        self.set_text('获取表格信息，生成调度序列，并显示')

    # 自动模拟
    def auto_sim(self):
        # 创建环境并开始设置进程
        env = simpy.Environment()
        env.process(setup(env, self.NUM_BARBERS, self.T_START, self.T_INTER))
        # 执行：(模拟时长)
        env.run(until=self.SIM_TIME)
        s = ""
        for line in record:
            s += line
        self.over_Edit.setText(s)
        record.clear()  # 清空数据

    # 设置字体
    def set_text(self, txt):
        font = QFont('微软雅黑', 10)
        self.txt.setFont(font)
        self.txt.setText(txt)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = ui()
    sys.exit(app.exec_())
