import sys
import random
from PySide2 import QtCore, QtWidgets, QtGui


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # 数据元素
        self.K = 0  # K个理发师
        self.L = -1  # 长凳上可以容纳等待人的数量。为0表示不能等待，一来就直接理发
        self.t_start = -1  # 理发店开店时间，整型数字模拟表示
        self.t_end = -1  # 理发店关店时间，整型数字表示。必须满足t_start < t_end

        self.barberEdit = QtWidgets.QLineEdit()
        self.waitEdit = QtWidgets.QLineEdit()
        self.startEdit = QtWidgets.QLineEdit()
        self.endEdit = QtWidgets.QLineEdit()

        self.initUi()

    # 初始化界面
    def initUi(self):
        # 页面元素
        barber = QtWidgets.QLabel("理发师人数：")
        wait_num = QtWidgets.QLabel("等待容量：")
        start = QtWidgets.QLabel("开店时间：")
        end = QtWidgets.QLabel("关店时间：")

        # 初始值占位符
        self.barberEdit.setPlaceholderText(str(self.K))
        self.waitEdit.setPlaceholderText(str(self.L))
        self.startEdit.setPlaceholderText(str(self.t_start))
        self.endEdit.setPlaceholderText(str(self.t_end))

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
        addButton.clicked.connect(self.random_create)

    # 随机生成顾客
    def random_create(self):
        self.K = int(self.barberEdit.text())
        self.L = int(self.waitEdit.text())
        self.t_start = int(self.startEdit.text())
        self.t_end = int(self.endEdit.text())

        if self.K <= 0:
            print("随机生成顾客")


# 运行窗口
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    app.setApplicationName("理发店模拟")
    widget = MyWidget()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec_())
