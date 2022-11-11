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
config_file = "server_config_pattern.yaml"
config = read_config.get_server_config(config_file)


#Setze Globale Variablen
WORK_START_HOUR = config['general_config']['start_hour']
WORK_END_HOUR = config['general_config']['end_hour']
INFLUENCER = config['general_config']['influencer']

MQTT_SERVER = config['mqtt_config']['mqtt_server']
MQTT_PORT = config['mqtt_config']['mqtt_port']
MQTT_TIMEOUT = config['mqtt_config']['mqtt_timeout']
MQTT_SECURE = False
MQTT_CA_FILE = None
MQTT_SECURE_USER = None
MQTT_SECURE_PW = None
MQTT_SECURE_PORT = None


try:
    MQTT_SECURE = config['mqtt_config']['mqtt_tls_enable']
    
    if MQTT_SECURE == True:
        MQTT_CA_FILE = config['mqtt_config']['mqtt_tls_ca_cert_file']
        MQTT_SECURE_USER = config['mqtt_config']['mqtt_tls_user_name']
        MQTT_SECURE_PW = config['mqtt_config']['mqtt_tls_user_pass']
        MQTT_SECURE_PORT = config['mqtt_config']['mqtt_tls_port']
except:
    print("ERROR in MQTT-Secure Configuration")
    exit(-1)


INFLUXDB_SERVER = config['influxdb_config']['influxdb_server']
INFLUXDB_TOKEN = config['influxdb_config']['influxdb_api_token']
INFLUXDB_BUCKET = config['influxdb_config']['influx_bucket']
INFLUXDB_ORG = config['influxdb_config']['influx_org']
INFLUXDB_SECURE = False

try:
    INFLUXDB_SECURE = config['influxdb_config']['influxdb_tls_enable']
except:
    pass



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
    
    #client.unsubscribe("/testroom/sensor_mode")


    for topic in MQTT_Subscriptions:
            
        #if msg.topic == topic[0]:
        #if topic[0] in msg.topic:
            log_time = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
            print("{} | Write Data for {}".format(log_time,msg.topic))
            SKIP_IMPORT = False

            #if msg.topic == "testroom/sensor/people_counter/count":
            if (str(msg.topic).find('people_counter') > 0):
                    #print(msg.topic)
                        count = msg.payload.decode().split(":")[1]
                        timestamp = msg.payload.decode().split(":")[0]
                        sleep(0.1)
                        mod_sendData.sendInfluxData(count,
                                                    timestamp,
                                                    msg.topic,
                                                    influx_server=INFLUXDB_SERVER,
                                                    influx_token=INFLUXDB_TOKEN,
                                                    influx_org=INFLUXDB_ORG,
                                                    influx_bucket=INFLUXDB_BUCKET,
                                                    use_tls=INFLUXDB_SECURE)
                        SKIP_IMPORT = True
                        #break

            if msg.topic in config['general_config']['influencer']:
                    
                    try:
                        influencer_usage = int(msg.payload.decode())
                    except:
                        try:
                            influencer_usage = int(msg.payload.decode().split(":")[1])
                        except:
                            print("ERROR: Getting Valid Value")
                    #mod_sendData.sendInfluxData(int(msg.payload.decode()),int(time()),msg.topic,influx_server=INFLUXDB_SERVER,influx_token=INFLUXDB_TOKEN,influx_org=INFLUXDB_ORG,influx_bucket=INFLUXDB_BUCKET)
                    
                    if influencer_usage > 0:
                        if MQTT_SECURE == True:
                            mod_sendData.sendMQTTData_secure(MQTT_SERVER,
                                                    "testroom/sensor_mode",
                                                    payload=2,
                                                    port=MQTT_PORT,
                                                    mqtt_retain=True,
                                                    mqtt_secure=MQTT_SECURE,
                                                    mqtt_ca_cert=MQTT_CA_FILE,
                                                    mqtt_secure_user=MQTT_SECURE_USER,
                                                    mqtt_secure_pw=MQTT_SECURE_PW)
                        else:
                            mod_sendData.sendMQTTData(MQTT_SERVER,"testroom/sensor_mode",payload=2,port=MQTT_PORT,mqtt_retain=True)

                        break
                    
                    elif msg.topic in config['general_config']['switch_master']:
                        global switch_counter
                        switch_counter = switch_counter+1
                        print("switch_counter set to ",switch_counter)
                        if switch_counter >= config['general_config']['switch_max_counter']:
                            print("Switching Modus back to ",int(config['general_config']['switch_back_mode']))
                            if MQTT_SECURE == True:
                                mod_sendData.sendMQTTData_secure(MQTT_SERVER,
                                                        "testroom/sensor_mode",
                                                        payload=int(config['general_config']['switch_back_mode']),
                                                        port=MQTT_PORT,
                                                        mqtt_retain=True,
                                                        mqtt_secure=MQTT_SECURE,
                                                        mqtt_ca_cert=MQTT_CA_FILE,
                                                        mqtt_secure_user=MQTT_SECURE_USER,
                                                        mqtt_secure_pw=MQTT_SECURE_PW)
                            
                            else:

                                mod_sendData.sendMQTTData(MQTT_SERVER,"testroom/sensor_mode",payload=int(config['general_config']['switch_back_mode']),port=MQTT_PORT,mqtt_retain=True)
                            
                            switch_counter = 0
                            break
                        else:
                            break

            elif SKIP_IMPORT == False:
                mod_sendData.sendInfluxData(int(msg.payload.decode()),
                                            int(time()),msg.topic,
                                            influx_server=INFLUXDB_SERVER,
                                            influx_token=INFLUXDB_TOKEN,
                                            influx_org=INFLUXDB_ORG,
                                            influx_bucket=INFLUXDB_BUCKET,
                                            use_tls=INFLUXDB_SECURE)
                break
            else:
                break
    client.loop_stop()
    client.disconnect()
    sleep(0.1)


print("MQTT_INFLUX_BROKER - Started")

while True:
    client = mqtt.Client("")
    
    if MQTT_SECURE == True:
        client.tls_set(MQTT_CA_FILE)
        client.tls_insecure_set(True)
        client.username_pw_set(MQTT_SECURE_USER,MQTT_SECURE_PW)
        MQTT_PORT = MQTT_SECURE_PORT
    try:
        client.connect(MQTT_SERVER,MQTT_PORT,MQTT_TIMEOUT)
        
        current_hour = int(strftime("%H",localtime()))
        
        #Setze Sensor Modus über nacht auf 0, damit die Sensoren strom sparen
        if  (current_hour >= WORK_END_HOUR) and (current_hour < WORK_START_HOUR):
            
            if MQTT_SECURE == True:
                mod_sendData.sendMQTTData_secure(MQTT_SERVER,
                                            "testroom/sensor_mode",
                                            payload=0,
                                            port=MQTT_PORT,
                                            mqtt_retain=True,
                                            mqtt_secure=MQTT_SECURE,
                                            mqtt_ca_cert=MQTT_CA_FILE,
                                            mqtt_secure_user=MQTT_SECURE_USER,
                                            mqtt_secure_pw=MQTT_SECURE_PW)

            else:
                mod_sendData.sendMQTTData(MQTT_SERVER,"testroom/sensor_mode",payload=0,port=MQTT_PORT,mqtt_retain=True)

        client.subscribe(MQTT_Subscriptions)
        client.on_message = on_message
        sleep(0.5)
        client.loop_start()
    except:
        print("WARNING: \tMQTT_Endpoint or InfluxDB not reachable")
        sleep(5.0)
