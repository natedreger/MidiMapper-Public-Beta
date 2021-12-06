from multiprocessing import Process

from web_interface import server_main
from midi_mapper import midi_main

p1 = Process(target=server_main)
p2 = Process(target=midi_main)

p1.start()
p2.start()
