from subprocess import check_output, call, Popen, PIPE, STDOUT
import sys
import time
import os

from threading  import Thread
from queue import Queue, Empty

from flask import Flask, jsonify

app = Flask(__name__)

current_value = 0

def enqueue_output(process, queue):
    while process.poll() is None:
        for line in iter(process.stdout.readline, ""):
            line = line.decode('UTF-8').replace('\n', '')
            queue.put(line)
    process.close()

def open_pipe(micros_between_readings, samples, sample_set_frequency):
    try:
        command = 'sudo ./read_adc_daemon {} {} {}'.format(micros_between_readings, samples, sample_set_frequency)
        print(command)

        process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
        return process
    except Exception as e:
        close_pipe()
        print(e)
        sys.exit(1)

def close_pipe():
    call('sudo killall read_adc_daemon', shell=True)

def read_adc_pipe(micros_between_readings, samples):
    process = open_pipe(micros_between_readings, samples)

    while process.poll() is None:
        for line in iter(process.stdout.readline, ""):
            line = line.decode('UTF-8').replace('\n', '')
            process_line(line)

def to_voltage(x):
    ADCRESOLUTION = 4095
    SYSTEMVOLTAGE = 5
    return (x/ADCRESOLUTION)*SYSTEMVOLTAGE

def process_line(line):
    global current_value
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
        voltages = list(map(to_voltage, values))
        formatted_voltages = ["%.3f" % voltage for voltage in voltages]
        print(adjusted_timestamps)
        print(timestamps)
        print(values)
        print(voltages)

        index_max = max(range(len(values)), key=values.__getitem__)
        #print(str(voltages[index_max]) + 'V', str(timestamps[index_max]) + 'us')
        current_value = ("%.3f" % voltages[index_max]) + 'V'
        print(current_value)

def process_queue(queue):
     while True:
            try:
                line = queue.get_nowait()
            except Empty:
                continue
            else:
                process_line(line)

@app.route('/api', methods=['GET'])
def get_value():
    return jsonify(title='Locating', value=current_value)

def main():
    close_pipe()
    p = open_pipe(35,10,30)
    q = Queue()
    t1 = Thread(target=enqueue_output, args=(p,q))
    t1.daemon = True
    t1.start()

    t2 = Thread(target=process_queue, args=(q,))
    t2.daemon = True
    t2.start()

if __name__== '__main__':
    main()

    app.run("0.0.0.0")

    while(True):
        continue
    