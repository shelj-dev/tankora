# import _thread
# import time

# def core1_task():
#     while True:
#         print("Running on Core 1")
#         time.sleep(1)

# # _thread.start_new_thread(core1_task, ())

# while True:
#     print("Running on Core 0")
#     time.sleep(2)


import _thread
import time

def core1_task():
    while True:
        print("Running on Core 1")
        time.sleep(1)

def thread_core1():
    _thread.start_new_thread(core1_task, ())

def core2_task():
    while True:
        print("Running on Core 2")
        time.sleep(1)

thread_core1()
core2_task()
