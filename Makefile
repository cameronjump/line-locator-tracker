 # build an executable named myprog from myprog.c
all: read_adc_daemon.c 
	gcc -Wall -pthread -o read_adc_daemon read_adc_daemon.c -lpigpio
