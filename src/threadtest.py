#!/usr/bin/python


from multiprocessing import Process, Lock, JoinableQueue
import time
import logging
import array
import numpy as np

import src.Cfuncs as cf
import src.Cyarr as cy
#import src.Cyphys as cph

LOGGING_LEVEL = logging.INFO
logging.basicConfig(level=LOGGING_LEVEL,
                    format='%(asctime)s:[%(levelname)s]-(%(processName)-15s): %(message)s',
                    )

lampdim = [77, 50]
beta = 1/8
updates = 0
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
            time.sleep(0.1)

def head(kwargs):
    cy.roll_rows_pointer(-1, kwargs['dim_h'], kwargs['arr_h'])
    cf.basic_update_buffer(
                    kwargs['updates'], kwargs['beta'], kwargs['threshold'],
                    kwargs['rules'], kwargs['head_position'],
                    kwargs['buffer_length'],
                    kwargs['dim_h'], kwargs['arr_h'], kwargs['buf_h'],
                    kwargs['bounds'], kwargs['bars'], kwargs['fuzz'],
                )
    arr_h = cf.update_array_positions(kwargs['head_position'], kwargs['buffer_length'],
                                      kwargs['buffer_status'], kwargs['buf_h'], 0)
    with queueLock:
        if arr_h is None:
            workQueue.put((retry_update_position, head, kwargs))
            logging.debug("Queue full, waiting and retrying.")
        else:
            kwargs['arr_h'] = np.asarray(arr_h)
            workQueue.put((head, kwargs))
            logging.debug("Head done, next queued up.")


def retry_update_position(func, kwargs):
    time.sleep(0.1)
    if func is tail:
        arr = cf.update_array_positions(kwargs['tail_position'], kwargs['buffer_length'],
                                        kwargs['buffer_status'], kwargs['buf_h'], 0)
    elif func is head:
        arr = cf.update_array_positions(kwargs['head_position'], kwargs['buffer_length'],
                                        kwargs['buffer_status'], kwargs['buf_h'], 0)
    with queueLock:
        if arr is None:
                workQueue.put((retry_update_position, func, kwargs))
                logging.debug("Queue full, waiting and retrying.")
        else:
            if func is tail:
                kwargs['arr_t'] = np.asarray(arr)
            elif func is head:
                kwargs['arr_h'] = np.asarray(arr)
            workQueue.put((func, kwargs))
            logging.debug("Queue has emptied! Continuing.")

def tail(kwargs):
    cf.basic_print(kwargs['dim_t'], kwargs['arr_t'], kwargs['bounds'], kwargs['bars'],
                   kwargs['fuzz'])
    cf.scroll_instruction_update(kwargs['bars'], kwargs['dim_t'])
    cf.scroll_instruction_update(kwargs['fuzz'], kwargs['dim_t'])
    arr_t = cf.update_array_positions(kwargs['tail_position'], kwargs['buffer_length'],
                                      kwargs['buffer_status'], kwargs['buf_t'], 0)
    with queueLock:
        if arr_t is None:
            workQueue.put((retry_update_position, tail, kwargs))
            logging.debug("Queue full, waiting and retrying.")
        else:
            kwargs['arr_t'] = np.asarray(arr_t)
            workQueue.put((tail, kwargs))
            logging.debug("Tail done, next queued up.")


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
kwargs={}
rules={'updates':updates,
       'beta':beta,
       'threshold':threshold,
       'rules':rules,
       'bounds':bounds,
       'bars':bars,
       'fuzz':fuzz,
       }
kwargs.update(rules)
buffers={'head_position':np.asarray(head_position),
         'tail_position':np.asarray(tail_position),
         'buffer_length':np.asarray(buffer_length),
         'buffer_status':np.asarray(buffer_status),
        }
kwargs.update(buffers)
head_pointers={'dim_h':np.asarray(dim_h),
               'arr_h':np.asarray(arr_h),
               'buf_h':np.asarray(buf_h),
              }
kwargs.update(head_pointers)
tail_pointers={'dim_t':np.asarray(dim_t),
               'arr_t':np.asarray(arr_t),
               'buf_t':np.asarray(buf_t),
               }
kwargs.update(tail_pointers)
with queueLock:
    workQueue.put((head, kwargs))
    workQueue.put((tail, kwargs))

# Wait for queue to empty
workQueue.join()

# Notify threads it's time to exit
# and wait for all threads to complete
for t in threads:
    t.terminate()
    t.join()
logging.debug("alles Fertig")
