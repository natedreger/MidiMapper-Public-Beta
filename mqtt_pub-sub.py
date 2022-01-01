import paho.mqtt.client as mqtt #import the client1
import time
import threading
import os
import json

#####################

hostname = os.uname().nodename
broker_address="midimapper.local"

client = mqtt.Client("P2") #create new instance

############

def on_message(client, userdata, message):
    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)

def on_connect(client, userdata, flags, rc):
    if rc==0:
        topic = 'connection'
        print("connected ok")
        subscribe(topic)
        publish(topic, f'{__file__} {hostname} connected ok')
    else:
        print(rc)

def subscribe(topic):
    client.subscribe(topic)
    print(f"Subscribing to topic {topic}")

def publish(topic, message):
    client.publish(topic,message)
    print(f"Publishing {message} to topic {topic}")

#####################

client.on_message=on_message #attach function to callback
client.on_connect=on_connect

########################################
print("connecting to broker")
client.username_pw_set(username='test',password='test')
client.connect(broker_address) #connect to broker

clientThread = threading.Thread(target=client.loop_start)
clientThread.start()

i = 0
while True:
    topic = "TheFlanderses"
    message = {"data":f'/app/Spotify/{i}'}
    publish(topic,json.dumps(message))
    time.sleep(5)
    i += 1
