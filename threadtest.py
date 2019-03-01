#!/usr/bin/python


from multiprocessing import Process, Lock, JoinableQueue
import time
import logging
import array
import numpy as np

import src.Cfuncs as cf
import src.Cyarr as cy
#import src.Cyphys as cph

LOGGING_LEVEL = logging.DEBUG
logging.basicConfig(level=LOGGING_LEVEL,
                    format='%(asctime)s:[%(levelname)s]-(%(processName)-15s): %(message)s',
                    )

lampdim = [77, 50]
beta = 1/8
updates = 100
threshold = 0
rules = np.array([[2, 3, 3, 3], [2, 3, 3, 3]], np.intc)
bounds = array.array('i', [0, -1, 0, -1])
bars = np.array([
                [0, 4, 1, 0, 1, -1],
                [0, 4, 1, 1, 1, -1],
                ], np.double)
fuzz = np.array([
                [70, 7, 0, 0, 1, 0.5, 1],
                [0, 4, 1, 1, 1, 0.5, -2],
                ], np.double)

class myProcess (Process):
    def __init__(self, threadID, name, q):
        super().__init__()
        self.threadID = threadID
        self.name = name
        self.q = q

    def run(self):
        logging.debug("starting up.")
        process_data(self.q)
        logging.debug("shutting down.")
        time.sleep(1)

def process_data(q):
    while True:
        queueLock.acquire()
        if not workQueue.empty():
            f, *args = q.get()
            queueLock.release()
            f(*args)
            queueLock.acquire()
            q.task_done()
            queueLock.release()
        else:
            queueLock.release()
            time.sleep(1)

def head(updates, beta, threshold, rules, head_position, tail_position,
         buffer_length, buffer_status,
         dim_h, arr_h, buf_h, bounds, bars, fuzz):
    cy.roll_rows_pointer(-1, dim_h, arr_h)
    cf.basic_update_buffer(
                    updates, beta, threshold,
                    rules, head_position,
                    buffer_length,
                    dim_h, arr_h, buf_h,
                    bounds, bars, fuzz,
                )
    arr_h = cf.update_array_positions(head_position, buffer_length, buffer_status,
                                      buf_h, 1)
    queueLock.acquire()
    if arr_h is None:
        workQueue.put((retry_update_position, head, updates, beta, threshold, rules,
                       head_position, tail_position, buffer_length,
                       buffer_status, dim_h, np.asarray(arr_h), buf_h,
                       bounds, bars, fuzz))
        logging.debug("Queue full, waiting and retrying.")
        queueLock.release()
    else:
        workQueue.put((head, updates, beta, threshold, rules,
                       head_position, tail_position, buffer_length,
                       buffer_status, dim_h, np.asarray(arr_h), buf_h,
                       bounds, bars, fuzz))
        logging.debug("Head done, next queued up.")
        queueLock.release()


def retry_update_position(func, updates, beta, threshold, rules, head_position, tail_position,
                          buffer_length, buffer_status,
                          dim, arr, buf, bounds, bars, fuzz):
    time.sleep(1)
    arr = cf.update_array_positions(head_position, buffer_length, buffer_status,
                                      buf, 1)
    queueLock.acquire()
    if arr is None:
        workQueue.put((retry_update_position, updates, beta, threshold, rules,
                       head_position, tail_position, buffer_length,
                       buffer_status, dim, np.asarray(arr), buf,
                       bounds, bars, fuzz))
        logging.debug("Queue still full, waiting and retrying.")
        queueLock.release()
    else:
        workQueue.put((func, updates, beta, threshold, rules,
                       head_position, tail_position, buffer_length,
                       buffer_status, dim, np.asarray(arr), buf,
                       bounds, bars, fuzz))
        logging.debug("Queue has emptied! Continuing.")
        queueLock.release()


def tail(updates, beta, threshold, rules, head_position, tail_position,
         buffer_length, buffer_status, dim_t, arr_t, buf_t,
         bounds, bars, fuzz):
    cf.basic_print(dim_t, arr_t, bounds, bars, fuzz)
    cf.scroll_instruction_update(bars, dim_t)
    cf.scroll_instruction_update(fuzz, dim_t)
    arr_t = cf.update_array_positions(tail_position, buffer_length,
                                                  buffer_status, buf_t, 0)
    queueLock.acquire()
    if arr_t is None:
        workQueue.put((retry_update_position, tail, updates, beta, threshold, rules,
                       head_position, tail_position, buffer_length,
                       buffer_status, dim_t, np.asarray(arr_t), buf_t,
                       bounds, bars, fuzz))
        logging.debug("Queue full, waiting and retrying.")
        queueLock.release()
    else:
        workQueue.put((tail, updates, beta, threshold, rules,
                       head_position, tail_position, buffer_length,
                       buffer_status, dim_t, np.asarray(arr_t), buf_t,
                       bounds, bars, fuzz))
        logging.debug("Tail done, next queued up.")
        queueLock.release()


threadList = ["BOSSTHREAD", "CHAMPTHREAD", "BROTHREAD", "GIRLPOWERTHREAD"]
queueLock = Lock()
workQueue = JoinableQueue()
threads = []
threadID = 1

# Create new threads
for tName in threadList:
    thread = myProcess(threadID, tName, workQueue)
    thread.start()
    threads.append(thread)
    threadID += 1

# Fill the queue
head_position, tail_position, buffer_length, buffer_status,\
    dim_t, arr_t, buf_t, dim_h, arr_h, buf_h = cf.init(lampdim)
queueLock.acquire()
workQueue.put((head, updates, beta, threshold, rules, np.asarray(head_position),
               np.asarray(tail_position), np.asarray(buffer_length),
               np.asarray(buffer_status),
               np.asarray(dim_h), np.asarray(arr_h), np.asarray(buf_h),
               bounds, bars, fuzz))
workQueue.put((tail, updates, beta, threshold, rules, np.asarray(head_position),
               np.asarray(tail_position), np.asarray(buffer_length),
               np.asarray(buffer_status),
               np.asarray(dim_h), np.asarray(arr_h), np.asarray(buf_h),
               bounds, bars, fuzz))
queueLock.release()

# Wait for queue to empty
workQueue.join()

# Notify threads it's time to exit
# and wait for all threads to complete
for t in threads:
    t.terminate()
    t.join()
logging.debug("alles Fertig")
