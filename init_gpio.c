#include <pigpio.h>

int main(int argc, char *argv[]){
    gpioCfgClock(/* micros */ 1, /* PWM */ 1, 0);
    if (gpioInitialise() < 0) return 1;
    
    return 0;
}