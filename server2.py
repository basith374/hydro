from twisted.internet import reactor, protocol, endpoints, task
from twisted.protocols import basic
import time

class HydroProtocol(basic.LineReceiver):
    def __init__(self, devices):
        self.devices = devices
        self.deviceid = 0

    def dataReceived(self, data):
        cmd = data[0]
        if cmd == 0:
            deviceid = int.from_bytes(data[1:5],  'big')
            self.devices[deviceid] = self
            self.deviceid = deviceid
            now = int(time.time() * 1000)
            self.transport.write(bytes([6]) + now.to_bytes(8, 'big'))
            # self.transport.write(b'\x00')
            print('registered', deviceid)
            
        elif cmd == 1:
            wtr = data[1]
            nut = data[2]
            print('data from', self.deviceid, data)
            # print('data from', self.deviceid, (wtr, nut))
            self.transport.write(b'\x00')

        elif cmd == 5:
            now = int(time.time() * 1000)
            self.transport.write(bytes([6]) + now.to_bytes(8, 'big'))

        elif cmd == 200:
            devid = int.from_bytes(data[1:5], 'big')
            if devid in self.devices:
                print('command for ', devid, data[5:])
                self.devices[devid].transport.write(data[5:])
            else:
                print('cannot find', devid)

        else:
            print('cmd', cmd)

class HydroFactory(protocol.Factory):
    devices = {}

    def buildProtocol(self, addr):
        return HydroProtocol(self.devices)

factory = HydroFactory()
endpoint = endpoints.serverFromString(reactor, 'tcp:8888')
endpoint.listen(factory)
reactor.run()