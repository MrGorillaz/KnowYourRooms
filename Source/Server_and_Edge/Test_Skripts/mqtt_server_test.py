import paho.mqtt.client as mqtt
from time import sleep
from time import time
import mod_sendData as influx

#Dieses Modul soll auf dem Server der INFLUXDB-Instanz laufen
#Es soll alle Daten, welche per MQTT von den Sateliten kommen
#lesen und in die INFLUXDB schreiben.

MQTT_SERVER = '192.168.178.36'

#MQTT-Syntax aus Influxdb
#point/tag1/tag2/field
#z.B. : testroom/sensor/sensorxx/usage


#Subscriptions für MQTT
MQTT_Subscriptions = [
                        ("topic/test/sensorxy/data",0),
                        ("topic/test/sensorxy1/data",0),
                        ("topic/test/sensorxy2/data",0),
                        ("topic/test/sensorxy3/data",0),
                        ("testroom/sensor/people_counter/count",0),
                        ("topic/end",0)
                        ]


# Wenn eine MQTT-Publish Nachricht empfangen wird.
def on_message(client,userdata,msg):
    # wenn /topic/end empfangen wird, dann soll der MQTT Client
    # die verbidnung trennen.
    if(msg.topic == "topic/end"):
        client.disconnect()
    else:
        #Lesen des MQTT-Payloads
        print(msg.payload.decode())
        payload_data = msg.payload.decode().split(':')
        #payload_data[0] = unixtimestamp für influxdb
        #payload_data[1] = sensorwert
        influx.sendInfluxData(timestamp=payload_data[0],data=payload_data[1],mqtt_msg=msg.topic)
    #print("hi")
    #client.disconnect()
    
    #    print(msg.payload.decode())
    #client.disconnect()

while(True):
    #print("client")
    client = mqtt.Client("MQTT")
    client.connect(MQTT_SERVER,1883,60)
    
    client.publish("topic/test", "{}:10".format(int(time())))
    
    #client.loop_forever()
    #print("next")
    #client.disconnect()
    #client.loop_start()

    sub = client.subscribe(MQTT_Subscriptions)
    client.on_message = on_message
    sleep(1.0)
    #client.disconnect()

    #client.disconnect()
   # client.loop_stop()
    client.loop_forever()
    sleep(1.0)