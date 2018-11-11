import socket
import time
import traceback
# traceback.print_exc()
import errno

deviceid = 1234567
device = {'socket': None, 'connected': False, 'registered': False}
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
device['socket'] = s

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
    if device['registered']:
        try:
            for i in data:
                base_time = i[0]
                _data = i[1]
                ba = bytes([1] + _data)
                device['socket'].send(ba)
            print('sent data', len(data))
            data.clear()
            last_event_times.update({'data_send': now})
        except Exception as e:
            if e.args[0] == errno.EPIPE:
                invalidate_connection()

def send_collected_data():
    now = int(time.time())
    last_time = last_event_times.get('data_send', 0)
    threshold = last_time + data_send_interval
    if now >= threshold:
        # print('trying to send data')
        send_data(now)

def collect_data():
    now = int(time.time())
    last_time = last_event_times.get('data_collect', 0)
    threshold = last_time + data_collect_interval
    if now >= threshold:
        print('collect data')
        _data = [time.time(), [100, 100, 100]]
        data.append(_data)
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
            print('server time', int.from_bytes(stime, 'big'))
            device['registered'] = True
    do_pending_tasks()
    time.sleep(1)