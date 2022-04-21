from threading import Thread
from time import sleep


def test(t):
    for i in range(100):
        print(i)
        sleep(t)


th = Thread(target=test, args=(5,))
th.start()
th2 = Thread(target=test, args=(2,))
th2.start()
