import random

import simpy

RANDOM_SEED = 42  # 随机种子
NUM_BARBERS = 2  # 理发师数量
CUT_TIME = 5  # 理发花费时间(min)
T_INTER = 7  # 每个大约7min随机创造一个顾客
T_START = 0  # 开店时间
T_END = 20  # 关店时间
SIM_TIME = T_END - T_START  # 模拟时间间隔


# 模拟理发店
class BarberShop(object):
    """理发店中理发师数量(NUM_BARBERS)有限，并行为顾客理发。
    顾客和理发师配对时，将占用CUT_TIME，等结束后，释放理发师
    """

    def __init__(self, env, num_barbers, cut_time):
        self.env = env
        self.barber = simpy.Resource(env, num_barbers)
        self.cut_time = cut_time

    def cut(self, guest):
        """理发过程中，花费CUT_TIME占用该process"""
        yield self.env.timeout(CUT_TIME)
        print("Barbershop cut %d%% of %s's hairs." %
              (random.randint(50, 99), guest))


# 模拟顾客
def guest(env, name, bs):
    """每个顾客到达理发店(bs)请求一个理发师，如果等待队列满了，则离开"""
    print('%s arrives at the barbershop at %.2f.' % (name, env.now))
    with bs.barber.request() as request:
        yield request

        print('%s enters the barbershop at %.2f.' % (name, env.now))
        yield env.process(bs.cut(name))

        print('%s leaves the barbershop at %.2f.' % (name, env.now))


def setup(env, num_barbers, cut_time, t_inter):
    """配置理发店：理发师个数，剪头发时间，每隔多长时间添加一个顾客"""
    # 创建一个理发店
    barbershop = BarberShop(env, num_barbers, cut_time)

    # 随机创建4个初始的顾客
    for i in range(4):
        env.process(guest(env, 'Guest %d' % i, barbershop))

    # 当进行理发时，随机创建更多的顾客
    while True:
        yield env.timeout(random.randint(t_inter - 2, t_inter + 2))
        i += 1
        env.process(guest(env, 'Guest %d' % i, barbershop))


if __name__ == '__main__':
    # 配置和启动理发店模拟器
    print('======BarberShop======')
    random.seed(RANDOM_SEED)  # 设置随机种子，可以重现结果进行测试

    # 创建环境并开始设置进程
    env = simpy.Environment()
    env.process(setup(env, NUM_BARBERS, CUT_TIME, T_INTER))

    # 执行：(模拟时长)
    env.run(until=SIM_TIME)
