import socket
import time
import errno
import os

start_time = int(time.time())

class UTime():
    def time(self):
        return int(time.time()) - start_time

utime = UTime()

deviceid = 1234567
device = {'socket': None, 'connected': False, 'registered': False}
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
device['socket'] = s
base_time = 0

if 'data' not in os.listdir(): os.mkdir('data')

def connect_sock():
    if not device['connected']:
        try:
            s = device['socket']
            s.settimeout(0)
            s.connect(('localhost', 8888))
            s.send(b'\x00' + deviceid.to_bytes(4, 'big'))
            print('connected')
            device['connected'] = True
        except Exception as e:
            if e.args[0] == 106:
                device['socket'] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                connect_sock()

data_collect_interval = 3
data_send_interval = 9

last_event_times = {}

data = []

def record_data(d):
    if base_time:
        event_time = base_time + (utime.time() * 1000)
        filename = '%d' % event_time
    else:
        filename = '%d_%d' % (base_time, (utime.time() * 1000))
    f = open(filename, 'w')
    f.write(d)
    f.close()

def clear_data():
    data.clear()

def invalidate_connection():
    device['connected'] = False
    device['registered'] = False

def recv():
    try:
        return device['socket'].recv(10)
    except Exception as e:
        if e.args[0] == errno.EAGAIN:
            do = 'nothing'
        else:
            invalidate_connection()

def send(data):
    try:
        device['socket'].send(data)
        return 'OK'
    except Exception as e:
        invalidate_connection()
        return ''

def send_data(now):
    if device['registered'] and base_time:
        try:
            files = os.listdir('data')
            for i in files:
                filename = 'data/' + i
                f = open(filename, 'w')
                data = f.read()
                f.close()
                ba = bytes([1] + data)
                device['socket'].send()
                os.remove(filename)
            print('sent data', len(files))
            last_event_times.update({'data_send': now})
        except Exception as e:
            if e.args[0] == errno.EPIPE:
                invalidate_connection()

def send_collected_data():
    now = utime.time()
    last_time = last_event_times.get('data_send', 0)
    threshold = last_time + data_send_interval
    if now >= threshold:
        # print('trying to send data')
        send_data(now)

def collect_data():
    now = utime.time()
    last_time = last_event_times.get('data_collect', 0)
    threshold = last_time + data_collect_interval
    if now >= threshold:
        print('collect data')
        data = bytearray([100, 100, 100])
        record_data(data.decode('utf-8'))
        last_event_times.update({'data_collect': now})

def do_pending_tasks():
    connect_sock()
    collect_data()
    send_collected_data()

connect_sock()
while True:
    rsp = recv()
    if rsp:
        if rsp[0] == 0:
            print('data ACK')
        elif rsp[0] == 6:
            stime = rsp[1:]
            stime = int.from_bytes(stime, 'big')
            print('server time %d' % stime)
            base_time = stime
            
            device['registered'] = True
            for f in os.listdir('data'):
                if '_' in f:
                    times = f.split('_')
                    filename = 'data/%s' % f
                    ldiff = utime.time() - times[1]
                    event_time = base_time - ldiff
                    new_filename = 'data/%d' % event_time
                    os.rename(filename, new_filename)

    do_pending_tasks()
    time.sleep(1)