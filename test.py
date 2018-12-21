from random import random
import socket
import time
import errno
import traceback

def rand():
    return int(random() * 255)

def connect_sock():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # s.connect(('192.168.43.217', 8008))
    s.connect(('localhost', 8888))
    s.settimeout(0)
    print('connected')
    return s

data_collect_interval = 5
data_send_interval = 10

deviceid = 1234567

last_event_times = {}

def send(data):
    try:
        s.send(b)
    except Exception as e:
        traceback.print_exc()

try:
    while True:
        try:
            s = connect_sock()
            while True:
                try:
                    b = bytes([0]) + deviceid.to_bytes(4, 'big')
                    send(b)
                    try:
                        rsp = s.recv(1)
                    except Exception as e:
                        print('foofoo')
                    while True:
                        b = bytearray([1])
                        wtr = rand()
                        b.append(wtr)
                        nut = rand()
                        b.append(nut)
                        s.send(b)
                        print(wtr, nut)
                        time.sleep(1)
                except BrokenPipeError as e:
                    traceback.print_exc()
                    print('connection lost')
                    break
                time.sleep(1)
            s.close()
        except ConnectionRefusedError as e:
            print('cannot connect to server')
        time.sleep(1)
except KeyboardInterrupt:
    print('\nkilled')
    pass