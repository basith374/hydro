import socket
import sys

if len(sys.argv) < 2:
    print('usage: %s <deviceid> <cmd> [<params>]' % (sys.argv[0]))
    exit()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('13.250.41.251', 8008))

deviceid = int(sys.argv[1])
cmd = int(sys.argv[2])
data = bytearray([200])
data = data + deviceid.to_bytes(4, 'big')
data.append(cmd)

if cmd == 4:
    for i in sys.argv[3:]:
        data.append(int(i))
else:
    for i in sys.argv[3:]:
        data = data + int(i).to_bytes(4, 'big')

print(data)

s.send(data)