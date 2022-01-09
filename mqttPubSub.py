import time
import os
import json
import threading
import paho.mqtt.client as mqtt

from collections import deque

from globals import publishQueue, settingsCLASS, checkPaswd, decrypt
#####################

hostname = os.uname().nodename
broker_address = settingsCLASS.mqtt_broker
broker_port = int(settingsCLASS.mqtt_port)
username = settingsCLASS.mqtt_user
password = settingsCLASS.mqtt_paswd
encryptedPwd = checkPaswd(password)
# if the password is encrypted
if encryptedPwd[0]:
    password = decrypt(password.encode())

jsonData = {}

client = mqtt.Client(f'mqtt-{hostname}') #create new instance
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
        print(jsonQueue.popleft()['OSC'])

def on_connect(client, userdata, flags, rc):
    if rc==0:
        topic = 'connection'
        print("MQTT Broker connected ok")
        subscribe(topic)
        publish(topic, f'{hostname} connected ok')
        subscribe(hostname)
    elif rc==5:
        print("Authentication Error")
    else:
        print(rc)

def on_publish(client, userdata, mid):
    print('Published')

def subscribe(topic):
    client.subscribe(topic)
    print(f"Subscribing to topic {topic}")

def publish(topic, message):
    client.publish(topic,message)
    print(f"Publishing {message} to topic {topic}")

def connectBroker():
    print(f"connecting to MQTT broker at {broker_address}:{broker_port}")
    client.on_message=on_message #attach function to callback
    client.on_connect=on_connect
    client.on_publish=on_publish
    client.username_pw_set(username,password)
    client.connect(broker_address, port=broker_port) #connect to broker
    client.loop_start()

def publishQueueHandler():
    while True:
        try:
            queuedPub = publishQueue.get(1)
            topic = str(queuedPub[0])
            message = str(queuedPub[1])
            if message[0] == '/':
                message = json.dumps({"OSC":message})
            publish(topic, message)
        except: pass


#####################
if __name__ != '__main__':
    publishQueuelistener = threading.Thread(target=publishQueueHandler)
    publishQueuelistener.start()
    connectBroker()

########################################
if __name__ == '__main__':
    import threading
    try:
        clientThread = threading.Thread(target=connectBroker)
        clientThread.start()
    except ConnectionRefusedError as e:
        print(e)
    except Exception as e:
        print(e)
    time.sleep(1000) # wait
    client.loop_stop() #stop the loop
