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
TASK_NUM = 1


class DockerScheduler(Scheduler):

    def __init__(self):
        self.launched_task = 0

    def resourceOffers(self, driver, offers):
        filters = {'refuse_seconds': 5}

        for offer in offers:
            cpus = self.getResource(offer.resources, 'cpus')
            mem = self.getResource(offer.resources, 'mem')
            if self.launched_task == TASK_NUM:
                return
            if cpus < TASK_CPU or mem < TASK_MEM:
                continue


            task = Dict()
            task_id = str(uuid.uuid4())
            task.task_id.value = task_id
            task.agent_id.value = offer.agent_id.value

            # Container Info
            task.name = 'docker'
            task.container.type = 'DOCKER'
            task.container.docker.image = 'ubuntu_docker2'
            task.container.docker.network = 'HOST'

            # Command Info
            task.command.shell = False
            task.command.value = 'nginx'
            task.command.arguments=['-g','daemon off;']

            task.resources = [
                dict(name='cpus', type='SCALAR', scalar={'value': TASK_CPU}),
                dict(name='mem', type='SCALAR', scalar={'value': TASK_MEM}),
            ]

            self.launched_task += 1
            driver.launchTasks(offer.id, [task], filters)
            

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
    framework = Dict()
    framework.user = getpass.getuser()
    framework.name = "DockerFramework"
    framework.hostname = socket.gethostname()

    driver = MesosSchedulerDriver(
        DockerScheduler(),
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