"""
需求：理发店内有K个理发师，有一把长椅用于顾客等待时使用，长椅最多可容纳L个人，
    顾客到店的时间随机，到店后如果等待位置已满顾客则会直接离开，
    每位顾客的理发时间均不同（范围处于0-30内），理发店每天的开业时间（t_start）和闭店时间（t_end）可自由设定，
    开店时间前到达的顾客会直接离开，到达闭店时间时新的客人无法进入，在等待位置的顾客也需要离开。

变量：
K: K个理发师
L: 顾客长椅，最多容纳L人
t_start: 开店时间  整型数字
t_end: 闭店时间    整型数字

顾客：
    i
    t_arv_i: 到达时间
    t_cut_i: 花费时间

效果：
“顾客i到达，当前时间为x”
“顾客i离开，当前时间为x，完成理发/未完成理发”
“顾客i开始理发，当前时间为x”
“顾客i结束理发x，当前时间为x”
“顾客i完成理发，总耗时x”（包含等待时间）
"""
import random

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


class Guest:
    def __init__(self, no, t_arv, t_cut):
        self.no = no
        self.t_arv = t_arv
        self.t_cut = t_cut


if __name__ == '__main__':
    print("K: ")
    K = int(input())

    print("L:")
    L = int(input())

    print("t_start:")
    t_start = int(input())

    print("t_end:")
    t_end = int(input())

    # 随机生成理发人
    num = -1  # 理发人个数
    start = t_start  # 第一个到店的开始时间
    waiting_list = Queue(max_size=L)  # 等待区容量
    while True:
        print("add(a):")
        if input() == "a":  # 随机添加一个用户
            num = num + 1  # 顾客编号
            t_arv = start + random.randint(1, 30)  # 到达时间
            t_cut = random.randint(5, 30)  # 剪发时间
            start = t_arv  # 保证下一个顾客在上一个之后到达
            g = Guest(num, t_arv, t_cut)
            res = waiting_list.put(g)
        elif input() == 'e':
            break
        else:
            break