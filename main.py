import usocket
from urandom import getrandbits
import utime
import network
import errno
from ubinascii import unhexlify
import os
from machine import Pin

print('init')

connections = [
    (('18.223.99.121', 8888)),
    ('area 51', 'ahoythere', ('192.168.43.32', 8888)),
    ('area 51', 'ahoythere', ('192.168.43.217', 8008)),
    ('Autobot-5G', '1s2shunmu', ('192.168.2.43', 8888)),
    ('Decepticon', '1s2shunmu', ('192.168.11.18', 8888)),
    ('HAXX', 'random123', ('192.168.2.2', 8888)),
    ('One Plus 6', 'ahoythere', ('192.168.43.32', 8888)),
]

con = connections[4]

air_pin = Pin(5, Pin.OUT)
nut_pin = Pin(4, Pin.OUT)

if 'data' not in os.listdir(): os.mkdir('data')

f = open('deviceid')
deviceid = int(f.read().strip()) # 24 bits
f.close()

if 'interval' not in os.listdir():
    interval = 1
else:
    f = open('interval')
    interval = int(f.read().strip())
    f.close()

# print('interval', interval)

if 'airinterval' not in os.listdir():
    air_interval = [1800, 60]
else:
    f = open('airinterval')
    txt = f.read().strip()
    air_interval = list(map(int, txt.split(',')))
    f.close()

if 'nutinterval' not in os.listdir():
    nut_interval = [259200, 4]
else:
    f = open('nutinterval')
    txt = f.read().strip()
    nut_interval = list(map(int, txt.split(',')))
    f.close()

def connect_sock():
    s = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
    s.connect(con[2])
    s.settimeout(0)
    return s
    
def send_data(s):
    ba = bytearray([1])
    wtr = getrandbits(8)
    ba.append(wtr) # wtr
    nut = getrandbits(8)
    ba.append(nut) # nut
    s.send(ba)

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(con[0], con[1])
while not sta.isconnected():
    pass

print('connected to hotspot')
while True:
    try:
        s = connect_sock()
        print('socket connected')
        register = bytearray([0]) + int.to_bytes(deviceid, 4, 'big')
        s.send(register)
        reconnect = False
        while True:
            if reconnect:
                reconnect = False
                break
            try:
                rsp = s.recv(1)
                if rsp[0] == 0:
                    print('registered on server')
                now = utime.ticks_ms()
                last_send_time = now
                last_nut_time = now
                last_nut_on_time = 0
                last_air_time = now
                last_air_on_time = 0
                while True:
                    try:
                        rsp = s.recv(1)
                        if len(rsp) == 0:
                            print('connection lost')
                            reconnect = True
                            break
                        if rsp[0] == 0:
                            foo = rsp[0]
                            continue
                        cmd = rsp[0]
                        # print(cmd, type(cmd))
                        if cmd == 0:
                            foo = 'data sent'
                        elif cmd == 1: # set data interval
                            interval = s.recv(4)
                            interval = int.from_bytes(interval, 'big')
                            f = open('interval', 'w')
                            f.write(str(interval))
                            f.close()
                            print('changing interval to', interval)
                        elif cmd == 2: # set air interval
                            rsp = s.recv(8)
                            air_interval[0] = int.from_bytes(rsp[:4], 'big')
                            air_interval[1] = int.from_bytes(rsp[4:8], 'big')
                            f = open('airinterval', 'w')
                            f.write('%d,%d' % tuple(air_interval))
                            f.close()
                            print('changing air interval to', air_interval)
                        elif cmd == 3: # set nutrient interval
                            rsp = s.recv(8)
                            nut_interval[0] = int.from_bytes(rsp[:4], 'big')
                            nut_interval[1] = int.from_bytes(rsp[4:8], 'big')
                            f = open('nutinterval', 'w')
                            f.write('%d,%d' % tuple(nut_interval))
                            f.close()
                            print('changing nut interval to', nut_interval)
                        elif cmd == 4:
                            act = s.recv(1)
                            print('turning air pin', act[0])
                            air_pin.on() if act[0] else air_pin.off()
                        elif cmd == 5:
                            act = s.recv(1)
                            print('turning nut pin', act[0])
                            nut_pin.on() if act[0] else nut_pin.off()
                        else:
                            print(rsp)
                    except Exception as e:
                        if e.args[0] == errno.EAGAIN:
                            now = utime.ticks_ms()
                            if last_send_time + (int(interval) * 1000) <= now:
                                send_data(s)
                                last_send_time = now
                            if last_air_time + (int(air_interval[0]) * 1000) <= now:
                                # do air
                                air_pin.on()
                                last_air_time = now
                            if last_air_time + (int(air_interval[1]) * 1000) <= now:
                                air_pin.off()
                            if last_nut_time + (int(nut_interval[0]) * 1000) <= now:
                                # do air
                                nut_pin.on()
                                last_nut_time = now
                            if last_nut_time + (int(nut_interval[1]) * 1000) <= now:
                                nut_pin.off()
                            pass
                        else:
                            print('connection lost', e)
                            reconnect = True
                            break
                s.close()
            # except OSError as e:
            except Exception as e:
                # if e.args[0] == errno.EAGAIN:
                #     print('no data yet')
                pass
                # else:
                #     print(e)
    except Exception as e:
        if e.args[0] == errno.EAGAIN:
            print('no data yet')
        print('cannot connect to server')
    utime.sleep(1)