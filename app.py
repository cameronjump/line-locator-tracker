from subprocess import check_output, call, Popen, PIPE, STDOUT
#from ctypes import *
#read_adc_wrapper = CDLL("./read_adc.so")
import time
import os

from threading  import Thread
from queue import Queue, Empty

from flask import Flask

current_value = 0

def enqueue_output(process, queue):
    while process.poll() is None:
        for line in iter(process.stdout.readline, ""):
            line = line.decode('UTF-8').replace('\n', '')
            queue.put(line)
    process.close()

def open_pipe(micros_between_readings, samples):
    command = 'sudo ./read_adc_daemon {} {}'.format(micros_between_readings, samples)
    print(command)

    process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
    return process

def read_adc_pipe(micros_between_readings, samples):
    process = open_pipe(micros_between_readings, samples)

    while process.poll() is None:
        for line in iter(process.stdout.readline, ""):
            line = line.decode('UTF-8').replace('\n', '')
            process_line(line)

def process_line(line):
    global max
    if line[0:2] == 'DS':
        timestamps = []
        values = []

        samples = line.split(';')
        for sample in samples:
            try:
                timestamp, value = sample.split(',',1)
                timestamps.append(int(timestamp))
                values.append(int(value))
            except:
                continue

        if len(values) == 0:
            return
        del values[0]
        del timestamps[0]

        adjusted_timestamps = list(map(lambda x: x-timestamps[0], timestamps))
        print(adjusted_timestamps)

        index_max = max(range(len(values)), key=values.__getitem__)
        print(values[index_max], timestamps[index_max])
        current_max = values[index_max]

def process_queue(queue):
     while True:
            try:
                line = queue.get_nowait()
            except Empty:
                continue
            else:
                process_line(line)

def main():
    call('sudo killall read_adc_daemon', shell=True)

    try:
        p = open_pipe(40,10)
        q = Queue()
        t1 = Thread(target=enqueue_output, args=(p,q))
        t1.daemon = True
        t1.start()

        t2 = Thread(target=process_queue, args=(q,))
        t2.daemon = True
        t2.start()
        
    except Exception as e:
        print(e)
        call('sudo killall read_adc_daemon', shell=True)

    #read_adc(40, 10)

    '''while True:
        time_start = time.time()
        delta_time = 1.0/30.0
        time_next = time_start + delta_time

        read_adc(40, 10)

        sleep_duration = time_next-time.time()
        print(sleep_duration)
        time.sleep(sleep_duration)'''

if __name__== '__main__':
    main()
    app = Flask(__name__)
    app.run("0.0.0.0")
    