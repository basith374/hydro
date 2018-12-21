import paho.mqtt.client as mqtt
import sys

def on_msg(topic, msg):
    print(topic, msg)

client = mqtt.Client()
client.connect('13.250.41.251')
client.on_message = on_msg
client.subscribe('/hydroots/server/{}'.format(sys.argv[1]))
client.loop_forever()