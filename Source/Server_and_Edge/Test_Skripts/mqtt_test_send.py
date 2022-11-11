import paho.mqtt.client as mqtt
from time import sleep
from time import time
import random

#MQTT_SERVER = '192.168.178.36'
MQTT_SERVER = 'test.mosquitto.org'
mqtt_sleep = 1.0
while True:
    client = mqtt.Client("s")
    client.connect(MQTT_SERVER,1883,60)
    counter = 0.0
    #client.tls_set('my_ca.crt')
    #client.tls_insecure_set(True)
    #client.username_pw_set('influencer','influenceME')
    #client.connect(MQTT_SERVER,8888,60)
    for i in range(5):
        print("publish Testdata")
        #client.publish("testroom/sensor_mode",0,retain=True)
        #sleep(mqtt_sleep)
        #client.publish("testroom/sensor/se_lab_hopper/usage",random.randrange(0,20))
        client.publish("hpd/DetectedPersons","{\"DetectedPersons\": 4 }")
        #sleep(mqtt_sleep)
        #client.publish("testroom/sensor/se_lab_table/usage",random.randrange(0,20))
        #sleep(mqtt_sleep)
        #client.publish("testroom/sensor/se_lab_board/usage",random.randrange(0,20))
        #sleep(mqtt_sleep)
        #client.publish("testroom/sensor/people_counter/count","{}:{}".format(int(time()),random.randrange(0,20)))
        sleep(mqtt_sleep)
        #client.publish("cisco_room/sensor/people_counter/usage","{}:{}".format(int(time()),counter))
        counter=counter+1
        #client.publish("testroom/end",0)
        sleep(mqtt_sleep)
    client.disconnect()
    sleep(10.0)
print("---finished---")