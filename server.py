#!/usr/bin/env python

import socket
import sys
from thread import *
import json
import yaml
from random import random
import paho.mqtt.client as mqtt
from binascii import unhexlify

HOST = ''   # Symbolic name meaning all available interfaces
PORT = 8888 # Arbitrary non-privileged port

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print 'Socket created'

#Bind socket to local host and port
try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()

print 'Socket bind complete'

#Start listening on socket
s.listen(10)
print 'Socket now listening'

def i2b (val, width, endianness='big'):
    fmt = '%%0%dx' % (width * 2)
    s = unhexlify(fmt % val)
    if endianness == 'little':
        s = s[::-1]
    return s

#Function for handling connections. This will be used to create threads
def clientthread(conn):
    #Sending message to connected client
#    conn.send('Welcome to the server. Type something and hit enter\n') #send only takes string
    #infinite loop so that function do not terminate and thread do not end.
    deviceid = ''
    try:
        while True:
            #Receiving from client
            data = conn.recv(1024)
            if not data:
                break
            if ord(data[0]) == 0:
                deviceid = data[1:4]
                deviceid = ['{0:b}'.format(ord(x)).zfill(8) for x in deviceid]
                deviceid = str(int(''.join(deviceid), 2))
                print 'device', deviceid, 'registered'
                cons[deviceid] = conn
            elif ord(data[0]) == 1:
                d = ['data received from', deviceid, ord(data[1]), ord(data[2])]
                print d
            reply = bytearray([0])
            conn.sendall(reply)

        #came out of loop
        conn.close()
    except socket.error as e:
        print e


def listen_for_connections():
    while 1:
        #wait to accept a connection - blocking call
        conn, addr = s.accept()
        # print 'Connected with ' + addr[0] + ':' + str(addr[1])

        #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
        start_new_thread(clientthread ,(conn,))

def on_message(client, userdata, msg):
    payload = ''
    try:
        payload = json.loads(msg.payload)
        payload = yaml.safe_load(json.dumps(payload))
    except Exception:
        print 'invalid message'
    if not payload: return
    deviceid = payload.get('deviceid')
    con = cons[deviceid]
    if deviceid in cons:
        if 'interval' in payload:
            change_interval(con, con)
        if 'air_pin' in payload:
            data = bytearray([4, 1 if payload['air_pin'] else 0])
            con.send(data)
        if 'nutrient_pin' in payload:
            data = bytearray([5, 1 if payload['nutrient_pin'] else 0])
            con.send(data)

def change_interval(con, interval):
    data = bytearray([1]) + bytearray(i2b(interval, 4))
    con.send(data)

cons = {}

#now keep talking with the client
try:
    start_new_thread(listen_for_connections, ())
    client = mqtt.Client()
    client.connect('localhost')
    client.on_message = on_message
    client.subscribe('hydroots/#')
    client.loop_forever()
    # while 1:
    #     cmd = raw_input()
    #     if not cmd: continue
    #     data = bytearray([int(cmd[0])])
    #     if cmd[0] == '1':
    #         data += bytearray([min(int(cmd[1:]), 255)])
    #     for deviceid, con in cons.items():
    #         try:
    #             con.send(data)
    #         except socket.error as e:
    #             con.close()
    #             del cons[deviceid]
    #             print(e)
except KeyboardInterrupt:
    print "closed"
    s.close()
