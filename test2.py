import socket
from _thread import start_new_thread
import sys
import random
import time

def new_client():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('192.168.43.217', 8008))
    b = bytes([0]) + int(random.random() * 10000000).to_bytes(4, 'big')
    s.send(b)
    while True:
        s.send(bytes([1, random.getrandbits(8), random.getrandbits(8)]))
        # time.sleep(1)

try:
    while True:
        start_new_thread(new_client, ())
        # print('new client')
        # time.sleep(1)
except KeyboardInterrupt:
    sys.exit()