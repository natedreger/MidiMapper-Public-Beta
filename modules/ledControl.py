
from gpiozero import RGBLED
from colorzero import Color
from time import sleep
import sys
import threading
from globals import ledQueue

sys.path.insert(0, '/usr/lib/python3/dist-packages')


# dummyLED if no GPIO available
class dummyLED():
    def __init__(self):
        pass
    def Color(colorName):
        print(f'Dummy LED is {colorName}')
        pass
    def pulse(self,a,b,**kwargs):
        print(f'Dummy LED is pulsing {kwargs}')
        pass
    def blink(self,a,b,**kwargs):
        print(f'LED is blinking {kwargs}')
        pass
    def on(self):
        pass
    def off(self):
        pass

# RaspberryPI gpio LED
class customRGBLED(RGBLED):
    def __init__(self, RedPin, GreenPin, BluePin):
        # attempt to create RGBLED object on GPIO pins
        try:
            super().__init__(RedPin,GreenPin,BluePin)
            self.light = self
            print('OK!')
        # if fail i.e. device has no GPIO pins, like a desktop
        except Exception as err:
            print(f'!! {err} !!')
            self.light = dummyLED()
    def blue(self):
        print('LED is blue')
        self.light.color = Color('blue')
    def green(self):
        print('LED is green')
        self.light.color = Color('green')
    def red(self):
        self.light.color = Color('red')
        print('LED is red')
    def yellow(self):
        self.light.color = Color('yellow')
        print('LED is yellow')
    def orange(self):
        print('LED is orange')
        self.light.color = Color('orange')
    def customColor(self, color):
        self.light.color = Color(color)
    def blinkFast(self, color):
        print(f'LED is blinking fast on {color}')
        self.light.blink(.25, .25, on_color=Color(color))
    def blinkSlow(self, color):
        print(f'LED is blinking slow on {color}')
        self.light.blink(.5, .5, on_color=Color(color))
    def pulseSlow(self, color):
        print(f'LED is pulsing slow on {color}')
        self.light.pulse(2,2, on_color=Color(color), background=True)
    def pulseFast(self, color):
        print(f'LED is pulsing fast on {color}')
        self.light.pulse(.75, .75, on_color=Color(color), background=True)

led1 = customRGBLED(17,27,22)
led1.pulseFast('yellow')

def ledQueueHandler():
    while True:
        try:
            ledCmd = ledQueue.get(1)
            eval(ledCmd)
            sleep(.25)
        except: pass
