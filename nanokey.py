#!/usr/bin/env python3

import time
import rtmidi
import queue

from rtmidi.midiutil import open_midioutput, open_midiinput

from rtmidi import (MidiIn, MidiOut)

from probe_ports import probe_ports, getAvailableIO

class MidiInput:
    def handle_midi_in(self, event, data):
        message, deltatime = event
        q.put(message)
        print(self.device)

    def close_MidiInput(self):
        self.mi.close_port()
        #self.mi.delete()

    def delete_MidiInput(self):
        self.mi.delete()

    def __init__(self, pn, q):
        self.pn=pn
        self.q = q
        self.mi = open_midiinput(pn)
        self.mi = self.mi[0]
        self.mi.ignore_types(sysex=False, timing=True, active_sense=True)
        self.device = self.mi.get_port_name(pn, encoding=u'auto').split(':')[0]
        self.mi.set_callback(self.handle_midi_in)

q = queue.Queue()

outports = getAvailableIO(MidiOut)
inports = getAvailableIO(MidiIn)
print(f'{len(inports)} available inputs')

# Dynamicly open midi inputs
for i in range (0, len(inports)):
    x = f'm{i}'
    globals()[x] = MidiInput(i, q)

try:
    timer = time.time()
    while True:
        m = q.get(1)
        print(m)
except KeyboardInterrupt:
    print('')
finally:
    print("Exit.")
    for i in range (0, len(inports)):
        x = f'm{i}'
        globals()[x].close_MidiInput()
        del globals()[x]
