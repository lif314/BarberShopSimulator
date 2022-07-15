import random
import time

from queue import Empty, Queue
from threading import Thread

"""
Single producer multiple consumers
"""

max_product = 10
cur_product = 0

done = False


def produce(queue):
    global cur_product, done
    nums = range(5)
    while True:
        if cur_product >= max_product:
            done = True
            break

        num = random.choice(nums)
        queue.put(num)
        print('Produced:', num)
        time.sleep(random.randint(0, 5))

        cur_product += 1

    print('Exiting producer thread...')


def consume(name, queue):
    while not done:
        try:
            num = queue.get(timeout=0.1)
            queue.task_done()
            print('{} consumed: {}'.format(name, num))
            time.sleep(random.randint(0, 5))
        except Empty:
            pass

    print('Exiting consumer thread', name)


def main():
    q = Queue(10)

    producer = Thread(target=produce, args=(q,))
    producer.start()

    consumers = []
    for i in range(3):
        name = 'Consumer-{}'.format(i)
        consumer = Thread(target=consume, args=(name, q))
        consumer.start()
        consumers.append(consumer)

    producer.join()

    for consumer in consumers:
        consumer.join()


if __name__ == '__main__':
    main()
