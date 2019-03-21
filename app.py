from subprocess import check_output, call
from subprocess import Popen, PIPE
#from ctypes import *
#read_adc_wrapper = CDLL("./read_adc.so")
import time

def read_adc(micros_between_readings, samples):
    #parse variables into C script command
    command = 'sudo ./read_adc {} {}'.format(micros_between_readings, samples)
    print(command)

    '''p = Popen(command, stdout=PIPE)

    for line in iter(p.stdout.readline,""):
        print(line)


    '''#run compiled C script to retrieve ADC values and timestamps
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
    #read_adc_wrapper.init_gpio()

    while True:
        time_start = time.time()
        delta_time = 1.0/30.0
        time_next = time_start + delta_time

        read_adc(40, 10)

        sleep_duration = time_next-time.time()
        print(sleep_duration)
        time.sleep(sleep_duration)

if __name__== '__main__':
    main()
    