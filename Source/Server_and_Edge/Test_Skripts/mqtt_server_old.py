import paho.mqtt.client as mqtt
from time import sleep
from time import time
from time import strftime
from time import localtime
from datetime import datetime
import mod_sendData
import mod_read_config as read_config

#Läuft auf MQTT Server und dient als MQTT zu Influx Gateway

#Lese Config-File
config_file = "server_config.yaml"
config = read_config.get_server_config(config_file)


#Setze Globale Variablen
WORK_START_HOUR = config['general_config']['start_hour']
WORK_END_HOUR = config['general_config']['end_hour']
INFLUENCER = config['general_config']['influencer']

MQTT_SERVER = config['mqtt_config']['mqtt_server']
MQTT_PORT = config['mqtt_config']['mqtt_port']
MQTT_TIMEOUT = config['mqtt_config']['mqtt_timeout']

INFLUXDB_SERVER = config['influxdb_config']['influxdb_server']
INFLUXDB_TOKEN = config['influxdb_config']['influxdb_api_token']
INFLUXDB_BUCKET = config['influxdb_config']['influx_bucket']
INFLUXDB_ORG = config['influxdb_config']['influx_org']



#Modus - Noch gebraucht?
old_mode = 0
switch_counter = 0

#Liste für MQTT-Subcriptions
MQTT_Subscriptions = []

#Erstellt eine Liste aller Subcriptions aus der Config
for sub in config['mqtt_config']['mqtt_subs']:
        MQTT_Subscriptions.append((sub,config['mqtt_config']['mqtt_qos']))


def on_message(client,userdata,msg):
    #Abfangen des Sensor_Mode wechsels
    
    if msg.topic == "testroom/sensor_mode":
        global old_mode
        curent_mode = msg.payload.decode()
        if curent_mode != old_mode:
            print("Sensor_Mode changed: {} -> {}".format(old_mode,curent_mode))
            old_mode = curent_mode

            #client.unsubscribe(msg.topic)
    
    client.unsubscribe("/testroom/sensor_mode")


    for topic in MQTT_Subscriptions:

        if msg.topic == topic[0]:
        #if topic[0] in msg.topic:
            log_time = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
            print("{} | Write Data for {}".format(log_time,msg.topic))

            #if msg.topic == "testroom/sensor/people_counter/count":
            if (str(msg.topic).find('people_counter') > 0):
                    #print(msg.topic)
                    count = msg.payload.decode().split(":")[1]
                    timestamp = msg.payload.decode().split(":")[0]
                    mod_sendData.sendInfluxData(count,timestamp,msg.topic,influx_server=INFLUXDB_SERVER,influx_token=INFLUXDB_TOKEN,influx_org=INFLUXDB_ORG,influx_bucket=INFLUXDB_BUCKET)
                    #break

            elif msg.topic in config['general_config']['influencer']:
                    
                    influencer_usage = int(msg.payload.decode())
                    #mod_sendData.sendInfluxData(int(msg.payload.decode()),int(time()),msg.topic,influx_server=INFLUXDB_SERVER,influx_token=INFLUXDB_TOKEN,influx_org=INFLUXDB_ORG,influx_bucket=INFLUXDB_BUCKET)
                    
                    if influencer_usage > 0:
                        mod_sendData.sendMQTTData(MQTT_SERVER,"testroom/sensor_mode",payload=2,port=MQTT_PORT,mqtt_retain=True)
                        #break
                    
                    elif msg.topic in config['general_config']['switch_master']:
                        global switch_counter
                        switch_counter = switch_counter+1
                        if switch_counter >= config['general_config']['switch_max_counter']:
                            mod_sendData.sendMQTTData(MQTT_SERVER,"testroom/sensor_mode",payload=int(config['general_config']['switch_back_mode']),port=MQTT_PORT,mqtt_retain=True)
                            switch_counter = 0
                            #break

            else:
                mod_sendData.sendInfluxData(int(msg.payload.decode()),int(time()),msg.topic,influx_server=INFLUXDB_SERVER,influx_token=INFLUXDB_TOKEN,influx_org=INFLUXDB_ORG,influx_bucket=INFLUXDB_BUCKET)
                #break
    client.disconnect()
    #sleep(0.1)

while True:
    client = mqtt.Client("")
    try:
        client.connect(MQTT_SERVER,MQTT_PORT,MQTT_TIMEOUT)
        
        current_hour = int(strftime("%H",localtime()))
        
        #Setze Sensor Modus über nacht auf 0, damit die Sensoren strom sparen
        if  (current_hour >= WORK_END_HOUR) and (current_hour < WORK_START_HOUR):
            mod_sendData.sendMQTTData(MQTT_SERVER,"testroom/sensor_mode",payload=0,port=MQTT_PORT,mqtt_retain=True)

        client.subscribe(MQTT_Subscriptions)
        client.on_message = on_message
        sleep(0.5)
        client.loop_forever()
    except:
        print("WARNING: \tMQTT_Endpoint or InfluxDB not reachable")
        sleep(5.0)
