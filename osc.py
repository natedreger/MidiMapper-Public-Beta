import socketio
import os

from logger import *
from globals import connectSocket, owner
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

oscSocket = socketio.Client()

def socket_handler(address, *args):
    oscSocket.emit('incomingOSC', address, *args)

dispatcher = Dispatcher()
# dispatcher.map("/something/*", print_handler)
dispatcher.set_default_handler(socket_handler)

ip = "0.0.0.0" #allow external
port = 9001

def osc_main(settings):
    socket_addr = 'localhost'
    socket_port = int(settings['socket_port'])
    logs.debug(f'osc.py running as PID: {os.getpid()} as User: {owner(os.getpid())}')
    connectSocket(oscSocket, socket_addr, socket_port)
    server = BlockingOSCUDPServer((ip, port), dispatcher)
    server.serve_forever()  # Blocks forever
