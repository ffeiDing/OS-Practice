#!/usr/bin/env python2.7
from __future__ import print_function

import sys
from random import random
import time
from threading import Thread

from pymesos import MesosExecutorDriver, Executor, decode_data, encode_data
from addict import Dict


class PiExecutor(Executor):
    def launchTask(self, driver, task):
        def run_task(task):
            update = Dict()
            update.task_id.value = task.task_id.value
            update.state = 'TASK_RUNNING'
            update.timestamp = time.time()
            driver.sendStatusUpdate(update)

            # 保留以作测试用
            print(decode_data(task.data), file=sys.stderr)
            cnt = 0 
            N = 2000000
            for i in range(N) :  
                x = random()
                y = random()
                if (x*x + y*y) < 1 :  
                    cnt += 1  
            vPi = 4.0 * cnt / N 
            print(vPi)
            driver.sendFrameworkMessage(encode_data(str(vPi)))

            time.sleep(30)

            update = Dict()
            update.task_id.value = task.task_id.value
            update.state = 'TASK_FINISHED'
            update.timestamp = time.time()
            driver.sendStatusUpdate(update)

        thread = Thread(target=run_task, args=(task,))
        thread.start()


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    driver = MesosExecutorDriver(PiExecutor(), use_addict=True)
    driver.run()