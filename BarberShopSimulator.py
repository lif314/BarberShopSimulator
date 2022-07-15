import random
import re
import sys
from builtins import super, str, range

from PySide2 import QtWidgets, QtCore
from PySide2.QtCore import Qt
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QWidget, QHBoxLayout, QTableWidget, QPushButton, QApplication, QVBoxLayout, \
    QTableWidgetItem, QCheckBox, QAbstractItemView, QLabel
from faker import Factory

RANDOM_SEED = 42  # 随机种子

_CUSTOMER_TEMPLATE = "Customer-{:d}:{:s}"
_OPEN_TIME = 9 * 60  # Minutes
_SHIFT_LEN = 60 * 4  # Minutes
_CLOSING_TIME = 17 * 60  # Minutes
_SHOP_TIME = 0  # Minutes
_CUSTOMER_FREQ = 10  # Minutes


##############################################################################
#                                  Classes
# ----------*----------*----------*----------*----------*----------*----------*
class Customer(object):
    def __repr__(self):
        return """{} - status '{}', waiting {} minutes""".format(self.name, self.status, self.wait_time)

    def __init__(self, customer_number, name, arrive_time, serve_time):
        self.name = _CUSTOMER_TEMPLATE.format(customer_number, name)
        self.status = 'Waiting'
        self.arrive_time = arrive_time  # 到达时间
        self.serve_time = serve_time  # 服务时间
        self.wait_time = 0

    def proceed(self, minutes=1):
        self.wait_time += minutes

        ## Customer is triggered after 30 minutes of waiting!
        if self.status == "Waiting" and self.wait_time > 30:
            self.status = "unfulfilled"


class WaitingArea(object):
    """FIFO-like customer queue object
    [(recently arrived) ... (waiting) ... (waiting a long time)]
    """

    def __init__(self, MAX_SIZE=0):
        self.customers = []
        self._MAX_CUSTOMERS = MAX_SIZE

    def add_customer(self, customer):
        """Add customer to waiting area if there is room. Otherwise send back to management
        """
        ## If shop is full, return customer to management
        if len(self.customers) >= self._MAX_CUSTOMERS:
            customer.status = "impatient"
            return customer

        ## Add to waiting area
        self.customers = [customer] + self.customers

    def get_patient_customer(self):
        """Retunrs longest waiting customer
        """
        return self.customers.pop()

    def proceed(self, minutes=1):
        """Simulate time
        * Have each customer wait a minute
        * If they've been waiting for too long, or the shop has closed, boot em back out to management
        """
        rejects = []
        for ix, customer in enumerate(self.customers):
            customer.proceed()
            if customer.status == "unfulfilled":
                rejects.append(self.customers.pop(ix))
            ## Closing time, kick em all out
            elif _SHOP_TIME > 2 * _SHIFT_LEN:
                customer.status = "furious"
                rejects.append(self.customers.pop(ix))
        return rejects


class Barber(object):
    """Barber gets instantiated at begining of shift. Cuts hair until his shift is done. Standard fare
    """

    def __init__(self, name):
        self.name = name
        self.cut_time_left = 0
        self.time_on_shift = 0
        self.status = "Ready"  # Ready, Cutting, Done, Leaving
        self.customer = None
        print("{} {} started shift".format(clock(), self.name))

    def cut(self, customer):
        """Start cutting a new customer's hair.
        """
        if self.status != "Ready":
            print("WOAH! Management screwed up, you can't give a barber a customer when they're already with one")
            return "WOAH! Management screwed up, you can't give a barber a customer when they're already with one"
        ## Reset the time left barber has to cut hair (20-40 minutes randomly)
        self.cut_time_left = customer.serve_time
        self.customer = customer
        self.status = "Cutting"
        print("{} {} started cutting {}'s hair".format(clock(), self.name, self.customer.name))
        return "{} {} started cutting {}'s hair".format(clock(), self.name, self.customer.name)

    def proceed(self, minutes=1):
        """Simulate time
        Proceed 1 minute:
            * Cut hair if cutting
            * Tell manager you're done if the haircut is finished
            * Go home if no customer and theyve been working long enough
        """
        self.time_on_shift += minutes

        ## Cut hair if you have a customer
        if self.customer is not None:
            self.cut_time_left -= minutes
            if self.cut_time_left <= 0:
                self.status = "Done"
                self.customer.status = "satisfied"
                print("{} {} ended cutting {}'s hair".format(clock(), self.name, self.customer.name))
                return "{} {} ended cutting {}'s hair".format(clock(), self.name, self.customer.name)
        else:
            if (self.time_on_shift > _SHIFT_LEN) or (_SHOP_TIME + _OPEN_TIME >= _CLOSING_TIME):
                self.status = "Leaving"
                return None


##############################################################################
#                                   Functions
# ----------*----------*----------*----------*----------*----------*----------*
def clock(minutes=None):
    """Format `minutes` into HH:MM string

    Examples:
    >>> clock(30)
    '00:30'
    >>> clock(150)
    '02:30'
    """
    if minutes is None:
        minutes = _SHOP_TIME + _OPEN_TIME

    return "{:0>2d}:{:0>2d}".format(minutes // 60, minutes % 60)


def unclock(time=None):
    """Format HH:MM string into `minutes`"""
    s = time.split(":")
    return (int(s[0]) * 60 - _SHOP_TIME) + int(s[1])


# 消息提示
def message_dialog(type, msg):
    msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, type, msg)
    msg_box.exec_()


# 日期正则判断
def is_date_time(string):
    return True if (
                       re.match("([01]?[0-9]|2[0-3]):[0-5][0-9]", string)
                   ) is not None else False


class ui(QWidget):
    def __init__(self):
        super(ui, self).__init__()
        self.id = 1
        self.lines = []
        self.editable = True
        self.des_sort = True
        self.faker = Factory.create()

        # 全局参数
        self.NUM_BARBERS = 2  # 理发师数量
        self.NUM_WAITING = 5  # 等待容量
        self.T_START = 9  # 开店时间
        self.T_END = 17  # 关店时间
        self._SHIFT_1 = []  # 理发师列表

        self.current_time = self.T_START * 60

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

        self.table.cellChanged.connect(self.cell_change)

        global original_processes  # 这里我们定义全局变量 - 原始进程列表，是一个二维列表

    def setupUI(self):
        self.setWindowTitle('理发店模拟')
        self.resize(906, 640)

        self.table = QTableWidget(self)

        # 初始参数设置
        self.barber = QtWidgets.QLabel("理发师人数：")
        self.wait_num = QtWidgets.QLabel("等待容量：")
        self.start = QtWidgets.QLabel("开店时间(HH:MM)：")
        self.end = QtWidgets.QLabel("关店时间(HH:MM)：")

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
        self.btn_get_info = QPushButton('启动模拟')

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
        self.headers = ['ID', '选择', '顾客名', '到达时间', '服务时间(min)']  # 设置每列标题
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
            if not is_date_time(start):
                message_dialog("参数错误", "开店时间格式错误，应为HH:MM！")
            else:
                s = start.split(":")
                self.T_START = int(s[0]) * 60 + int(s[1])
            if not is_date_time(end):
                message_dialog("参数错误", "关闭时间格式错误，应为HH:MM！")
            else:
                s = end.split(":")
                self.T_END = int(s[0]) * 60 + int(s[1])
            if self.T_END <= self.T_START:
                message_dialog("参数错误", "开店时间必须小于关店时间！")
            else:
                self.current_time = self.T_START
            # 清空面板数据
            self.over_Edit.setText("")
            # 初始化理发师列表
            for i in range(self.NUM_BARBERS):
                name = self.faker.name()
                self._SHIFT_1.append(name)

            # 初始化开店时间和关店时间
            global _OPEN_TIME, _CLOSING_TIME
            _OPEN_TIME = self.T_START  # Minutes
            _CLOSING_TIME = self.T_END # Minutes
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
        arr_time = random.randint(self.current_time, self.current_time + 60)  # 到达时间
        ser_time = random.randint(10, 30)  # 服务时间

        # 设置新建行的数据
        self.table.setItem(row, 0, QTableWidgetItem(id))
        self.table.setCellWidget(row, 1, w)
        self.table.setItem(row, 2, QTableWidgetItem(name))
        self.table.setItem(row, 3, QTableWidgetItem(clock(arr_time)))
        self.table.setItem(row, 4, QTableWidgetItem(str(ser_time)))

        self.id += 1  # 设置完不要忘记id加一
        self.current_time = arr_time  # 重置当前时间
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

    def manage_day(self, customers):
        """This is the manager's job. Watch the clock and take care of customers
        0. Clear out impatient customers from the waiting area
        1. Usher new customers into the waiting area
        2. Check on the barbers, see if they are done with a customer
        3. Get customer from waiting area into that seat!
        """
        ## Start the shift clock
        global _SHOP_TIME
        _SHOP_TIME = 0  # Ick. Globals. Shoulda made a Manager() or BarberShop() class that handles all this
        print("{} Barber shop opened".format(clock()))
        self.over_Edit.append("{} Barber shop opened".format(clock()))

        ## Have all of the shift_1 barbers clock in
        barbers = [Barber(name) for name in self._SHIFT_1]

        ## Dust and freshen the waiting area
        waitingArea = WaitingArea(MAX_SIZE=self.NUM_WAITING)

        ## Get nametags ready
        customer_number = 1

        # while (_SHOP_TIME < 2 * _SHIFT_LEN) or barbers:
        while _SHOP_TIME < (_CLOSING_TIME - _OPEN_TIME):
            ###### 0. Clear out waiting area (except beginning of day)
            if _SHOP_TIME != 0:
                rejects = waitingArea.proceed()
                ## Usher any out that are unfulfilled
                if rejects:
                    for customer in rejects:
                        print("{} {} left {}".format(clock(), customer.name, customer.status))
                        self.over_Edit.append("{} {} left {}".format(clock(), customer.name, customer.status))

            for customer in customers:
                if _SHOP_TIME == customer.arrive_time - self.T_START:
                    self.over_Edit.append("{} {} entered".format(clock(), customer.name))
                    ## Too late though?
                    if _SHOP_TIME >= 2 * _SHIFT_LEN:
                        customer.status = "cursing himself"
                        print("{} {} leaves {}".format(clock(), customer.name, customer.status))
                        self.over_Edit.append("{} {} leaves {}".format(clock(), customer.name, customer.status))

                    else:
                        ## Add to waiting area
                        reject = waitingArea.add_customer(customer)
                        if reject:
                            print("{} {} left {}".format(clock(), reject.name, reject.status))
                            self.over_Edit.append("{} {} left {}".format(clock(), reject.name, reject.status))

            ###### 2./3. Check on barbers, put customers in seats
            for ix, barber in enumerate(barbers):
                res = barber.proceed()
                if res:
                    self.over_Edit.append(res)
                ## Finished with a customer?
                if barber.status == "Done":
                    ## Usher his customer out.
                    print("{} {} left {}".format(clock(), barber.customer.name, barber.customer.status))
                    self.over_Edit.append("{} {} left {}".format(clock(), barber.customer.name, barber.customer.status))
                    barber.status = "Ready"
                    barber.customer = None

                ## Ready for a new one (can happen after finshed with previous)
                if barber.status == "Ready":
                    ## Bring any waiting customers to this barber
                    if waitingArea.customers:
                        res = barber.cut(waitingArea.get_patient_customer())
                        self.over_Edit.append(res)

                ## Done with shift? Sub in a new one
                if barber.status == "Leaving":
                    print("{} {} ended shift".format(clock(), barber.name))
                    self.over_Edit.append("{} {} ended shift".format(clock(), barber.name))

                    ## Remove this barber from the list of barbers
                    barbers.pop(ix)

                    ## Add a new barber to those on shift from any _SHIFT_2 ones ready and waiting
                    # if _SHIFT_2:
                    #     barbers.append(Barber(_SHIFT_2.pop()))

                ## Otherwise keep at it
                # else:

            ###### All checks done, whew, it's a new minute already
            _SHOP_TIME += 1
        print("{} Barber shop closed".format(clock()))
        self.over_Edit.append("{} Barber shop closed".format(clock()))
        return None

    # 手动模拟
    def hand_sim(self):
        # 我们每次使用这个功能时先把全变量原始进程列表 -- original_processes --清空好吧
        original_processes = []
        row = self.table.rowCount()

        # 获取顾客数据
        for j in range(row):
            na = self.table.item(j, 2).text()
            at = unclock(self.table.item(j, 3).text())
            st = int(self.table.item(j, 4).text())
            c = Customer(j, na, at, st)
            original_processes.append(c)

        '''
        由于第一个进程不一定就是到达时间最短的进程，所以我们先按照
        到达时间给进程排个序
        '''
        _sorted_processes = original_processes[:]

        self.manage_day(_sorted_processes)
        self.set_text('获取表格信息，生成调度序列，并显示')

    # 设置字体
    def set_text(self, txt):
        font = QFont('微软雅黑', 10)
        self.txt.setFont(font)
        self.txt.setText(txt)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = ui()
    sys.exit(app.exec_())
