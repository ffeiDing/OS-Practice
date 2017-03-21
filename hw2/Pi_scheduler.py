#!/usr/bin/env python2.7
from __future__ import print_function

import sys
import uuid
import time
import socket
import signal
import getpass
from threading import Thread
from os.path import abspath, join, dirname

from pymesos import MesosSchedulerDriver, Scheduler, encode_data, decode_data
from addict import Dict

TASK_CPU = 1
TASK_MEM = 32
EXECUTOR_CPUS = 0.5
EXECUTOR_MEM = 32


class PiScheduler(Scheduler):
    # 初始化一些变量
    Pi = 0
    sumPi = 0
    count = 20
    i = 0
    temp = 0
    nums = 2000000

    def __init__(self, executor):
        self.executor = executor

    # 计算Pi的值，判断何时停止运行
    def frameworkMessage(self, driver, executorId, slaveId, message):
        self.sumPi = self.sumPi + float(decode_data(message))
        self.temp = self.temp + 1
        if self.temp >= self.count:
            self.Pi = self.sumPi/self.count
            print(self.Pi)
            driver.stop()

    def resourceOffers(self, driver, offers):
        if self.i >= self.count:
            return None
        filters = {'refuse_seconds': 5}

        for offer in offers:
            if self.i >= self.count:
                break
            cpus = self.getResource(offer.resources, 'cpus')
            mem = self.getResource(offer.resources, 'mem')
            if cpus < TASK_CPU or mem < TASK_MEM:
                continue

            task = Dict()
            task_id = str(uuid.uuid4())
            task.task_id.value = task_id
            task.agent_id.value = offer.agent_id.value
            task.name = 'task {}'.format(task_id)
            task.executor = self.executor
            # 保留以作测试用 ：）
            task.data = encode_data('Hello from task {}!'.format(task_id))

            task.resources = [
                dict(name='cpus', type='SCALAR', scalar={'value': TASK_CPU}),
                dict(name='mem', type='SCALAR', scalar={'value': TASK_MEM}),
            ]

            driver.launchTasks(offer.id, [task], filters)
            self.i = self.i + 1

    def getResource(self, res, name):
        for r in res:
            if r.name == name:
                return r.scalar.value
        return 0.0

    def statusUpdate(self, driver, update):
        logging.debug('Status update TID %s %s',
                      update.task_id.value,
                      update.state)


def main(master):
    executor = Dict()
    executor.executor_id.value = 'PiExecutor'
    executor.name = executor.executor_id.value
    executor.command.value = '%s %s' % (
        sys.executable,
        abspath(join(dirname(__file__), 'executor.py'))
    )
    executor.resources = [
        dict(name='mem', type='SCALAR', scalar={'value': EXECUTOR_MEM}),
        dict(name='cpus', type='SCALAR', scalar={'value': EXECUTOR_CPUS}),
    ]

    framework = Dict()
    framework.user = getpass.getuser()
    framework.name = "PiFramework"
    framework.hostname = socket.gethostname()

    driver = MesosSchedulerDriver(
        PiScheduler(executor),
        framework,
        master,
        use_addict=True,
    )

    def signal_handler(signal, frame):
        driver.stop()

    def run_driver_thread():
        driver.run()

    driver_thread = Thread(target=run_driver_thread, args=())
    driver_thread.start()

    print('Scheduler running, wait :).')
    signal.signal(signal.SIGINT, signal_handler)

    while driver_thread.is_alive():
        time.sleep(1)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) != 2:
        print("Usage: {} <mesos_master>".format(sys.argv[0]))
        sys.exit(1)
    else:
        main(sys.argv[1])