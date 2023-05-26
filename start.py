from frame.app import start_app
from ds.main import start_ds
from vkbot.main import start_vk
from tg.main import start_tg
from threading import Thread


t1, t2, t3, t4 = Thread(target=start_ds), Thread(target=start_app), Thread(target=start_vk), Thread(target=start_tg)
t1.start()
t2.start()
t3.start()
t4.start()


t1.join()
t2.join()
t3.join()
t4.join()
