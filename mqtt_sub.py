import time
import threading
import os
import json
import paho.mqtt.client as mqtt #import the client1

from collections import deque

#####################

hostname = os.uname().nodename
broker_address="midimapper.local"
broker_port = 1883
username = 'test'
password = 'test'
jsonData = {}

client = mqtt.Client(hostname) #create new instance
msgQueue = deque()
jsonQueue = deque()

############

def on_message(client, userdata, message):
    global jsonData
    msg = str(message.payload.decode("utf-8","ignore"))
    # print("data Received",msg)
    try:
        # if message is json make a dict
        jsonData=json.loads(msg) #decode json data
        msg = ''
    except:
        pass
    if bool(msg):
        msgQueue.append(msg)
        print(msgQueue.popleft())
    if bool(jsonData):
        jsonQueue.append(jsonData)
        print(jsonQueue.popleft()['data'])

def on_connect(client, userdata, flags, rc):
    if rc==0:
        topic = 'connection'
        print("connected ok")
        subscribe(topic)
        publish(topic, f'{__file__} {hostname} connected ok')
        subscribe(hostname)
    elif rc==5:
        print("Authentication Error")
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
try:
    print("connecting to broker")
    client.username_pw_set(username,password)
    client.connect(broker_address, port=broker_port) #connect to broker
    clientThread = threading.Thread(target=client.loop_start)
    clientThread.start()
except ConnectionRefusedError as e:
    print(e)
except Exception as e:
    print(e)


time.sleep(1000) # wait
client.loop_stop() #stop the loop
