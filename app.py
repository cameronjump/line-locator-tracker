from subprocess import check_output, call, Popen, PIPE, STDOUT
#from ctypes import *
#read_adc_wrapper = CDLL("./read_adc.so")
import time
import os


pid = 0

def read_adc_pipe(micros_between_readings, samples):
    global pid

    command = 'sudo ./read_adc_daemon {} {}'.format(micros_between_readings, samples)
    print(command)

    process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)

    while process.poll() is None:
        for line in iter(process.stdout.readline, ""):
            line = line.decode('UTF-8').replace('\n', '')
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
                    continue
                del values[0]
                del timestamps[0]

                adjusted_timestamps = list(map(lambda x: x-timestamps[0], timestamps))
                print(adjusted_timestamps)

                index_max = max(range(len(values)), key=values.__getitem__)
                print(values[index_max], timestamps[index_max])


def read_adc(micros_between_readings, samples):
    #parse variables into C script command
    command = 'sudo ./read_adc {} {}'.format(micros_between_readings, samples)
    print(command)

    #run compiled C script to retrieve ADC values and timestamps
    read_time_start = time.time()
    foo = str(check_output(command, shell=True))
    read_time_finish = time.time()
    print(read_time_finish-read_time_start)
    split_output = foo.split('\\n')

    #parse C script output into timestamps and values
    timestamps = []
    values = []
    recording = False
    for line in split_output:
        if line == 'DATA_OUTPUT_START':
            recording = True
        elif line == 'DATA_OUTPUT_STOP':
            recording = False
        elif recording == True:
            timestamp, value = line.split(',',1)
            timestamps.append(timestamp)
            values.append(value)
        elif 'samples in' in line or 'Initialization time' in line:
            print(line)
        else:
            continue

    print(timestamps)
    print(values)

def main():
    call('sudo killall read_adc_daemon', shell=True)

    try:
        read_adc_pipe(40, 10)
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
    