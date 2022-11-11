import asyncio
from bleak import BleakScanner
from time import sleep, time
from datetime import datetime
from mod_sensors_mqtt import send_mqtt_data as send_mqtt
from mod_sensors_mqtt import send_mqtt_data_secure as send_mqtt_secure
import mod_read_config as read_config


#Get parameters out of Config-File
config_file = "server_config_pattern.yaml"
config = read_config.get_server_config(config_file)

MQTT_SERVER = config['mqtt_config']['mqtt_server']
MQTT_PORT = config['mqtt_config']['mqtt_port']
MQTT_TIMEOUT = config['mqtt_config']['mqtt_timeout']
MQTT_ROOM_TOPIC = config['mqtt_config']['mqtt_room_topic']
MQTT_SECURE = False
MQTT_CA_FILE = None
MQTT_SECURE_USER = None
MQTT_SECURE_PW = None
MQTT_SECURE_PORT = None

#try to get security config
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


#async function for BLE Advertising Broadcast Packages
async def main():
    devices = await BleakScanner.discover()
    for device in devices:
        #Device name should be something with Sedus
        if ("SEDUS" in device.name) or ("Sedus" in device.name):
            log_time = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
            print("{} - {}".format(log_time,device))
            try:
                #the choose between secured or unsecured data transmission
                if MQTT_SECURE == False:
                    send_mqtt(MQTT_SERVER,device,port=MQTT_PORT,timeout=MQTT_TIMEOUT,mqtt_room=MQTT_ROOM_TOPIC)
                else:
                    send_mqtt_secure(MQTT_SERVER,
                                        device,
                                        port=MQTT_SECURE_PORT,
                                        mqtt_ca_file=MQTT_CA_FILE,
                                        mqtt_secure_username=MQTT_SECURE_USER,
                                        mqtt_secure_pw=MQTT_SECURE_PW,
                                        timeout=MQTT_TIMEOUT,
                                        mqtt_room=MQTT_ROOM_TOPIC)
            except:
                print("Error while transacting Data")
        else:
            try:
                #Scan for Servicedata with 0000feaa-0000-1000-8000-00805f9b34fb (Eddystone Service UUID)
                if (device.details['props']['ServiceData']['0000feaa-0000-1000-8000-00805f9b34fb']):
                    log_time = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
                    print("{} - {}".format(log_time,device))
                    try:
                        if MQTT_SECURE == False:
                            send_mqtt(MQTT_SERVER,device,port=MQTT_PORT,timeout=MQTT_TIMEOUT,mqtt_room=MQTT_ROOM_TOPIC)
                        else:
                            send_mqtt_secure(MQTT_SERVER,
                                                device,
                                                port=MQTT_SECURE_PORT,
                                                mqtt_ca_file=MQTT_CA_FILE,
                                                mqtt_secure_username=MQTT_SECURE_USER,
                                                mqtt_secure_pw=MQTT_SECURE_PW,
                                                timeout=MQTT_TIMEOUT,
                                                mqtt_room=MQTT_ROOM_TOPIC)
                    except:
                        print("Error while transacting Data")
            except:
                pass
            
#Run forever as a Service
while True:
    try:
        asyncio.run(main())
    except:
        log_time = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
        print("{} - Error with BLE-Interface occured".format(log_time))
        sleep(5.0)