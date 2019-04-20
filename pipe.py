from subprocess import check_output, call, Popen, PIPE, STDOUT

def open_pipe(micros_between_readings, samples, sample_set_frequency):
    try:
        path = '/home/pi/underground-locator/read_adc_daemon'
        print(path)
        command = 'sudo {} {} {} {}'.format(path, micros_between_readings, samples, sample_set_frequency)
        print(command)

        process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
        return process
    except Exception as e:
        close_pipe()
        print(e)
        sys.exit(1)

def close_pipe():
    call('sudo killall read_adc_daemon', shell=True)