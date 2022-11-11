import paho.mqtt.client as mqtt
from time import sleep
from time import time
import random

MQTT_SERVER = '192.168.178.36'
mqtt_sleep = 0.2
client = mqtt.Client("s")
#client.tls_set('my_ca.crt')
client.tls_insecure_set(True)
client.username_pw_set('influencer','influenceME')
client.connect(MQTT_SERVER,8888,60)
for i in range(10):
    client.publish("testroom/sensor_mode",random.randrange(0,2),retain=True)
    sleep(mqtt_sleep)
    client.publish("testroom/sensor/se_lab_hopper/usage",random.randrange(0,20))
    sleep(mqtt_sleep)
    client.publish("testroom/sensor/se_lab_table/usage",random.randrange(0,20))
    sleep(mqtt_sleep)
    client.publish("testroom/sensor/se_lab_board/usage",random.randrange(0,20))
    sleep(mqtt_sleep)
    client.publish("testroom/sensor/people_counter/count","{}:{}".format(int(time()),random.randrange(0,20)))
    sleep(mqtt_sleep)
    #client.publish("testroom/end",0)
    #sleep(mqtt_sleep)
client.disconnect()
print("---finished---")