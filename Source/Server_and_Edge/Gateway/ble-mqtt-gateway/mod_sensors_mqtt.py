from logging import NOTSET
import paho.mqtt.client as mqtt
from time import sleep
from time import time
from mod_sensormgmt import set_sensor_working_mode
import random

#
SENSOR_MODE = 0
MQTT_CA_FILE = None
MQTT_USER_NAME = None
MQTT_USER_PW = None

#unsecured MQTT Communication
def send_mqtt_data(mqtt_server,sensor_obj,port=1883,timeout=60,mqtt_room='testroom'):

    client = mqtt.Client("")
    client.connect(mqtt_server,port,timeout)
    bytedata = sensor_obj.details['props']['ServiceData']['0000feaa-0000-1000-8000-00805f9b34fb']
    sensorID = str(sensor_obj.address).replace(':','')
    public_wait = 0.2
    mqtt_publish_data(mqtt_server,port,client,sensor_obj,bytedata,sensorID,public_wait,mqtt_room_topic=mqtt_room)

#secured MQTT COmmunication
def send_mqtt_data_secure(mqtt_server,sensor_obj,mqtt_ca_file,mqtt_secure_username,mqtt_secure_pw,port=8888,timeout=60,mqtt_room='testroom'):
    global MQTT_CA_FILE
    global MQTT_USER_NAME
    global MQTT_USER_PW

    MQTT_CA_FILE = mqtt_ca_file
    MQTT_USER_NAME = mqtt_secure_username
    MQTT_USER_PW = mqtt_secure_pw

    client = mqtt.Client("")
    client.tls_set(mqtt_ca_file)
    client.tls_insecure_set(True)
    client.username_pw_set(mqtt_secure_username,mqtt_secure_pw)
    client.connect(mqtt_server,port,timeout)
    bytedata = sensor_obj.details['props']['ServiceData']['0000feaa-0000-1000-8000-00805f9b34fb']
    sensorID = str(sensor_obj.address).replace(':','')
    public_wait = 0.2
    mqtt_publish_data(mqtt_server,port,client,sensor_obj,bytedata,sensorID,public_wait,mqtt_room_topic=mqtt_room)
   
def mqtt_publish_data(mqtt_server,mqtt_port,client,sensor_obj,bytedata,sensorID,public_wait=0.2,mqtt_room_topic='testroom'):
    
    #Room
    if chr(bytedata[3]) == 'R':
        print("\n\nRoom")
        #Send current Working-Mode of Sensor
        print("Modus: ",bytedata[2])
        client.publish("{}/sensor/room_{}/sensor_mode".format(mqtt_room_topic,sensorID),bytedata[2])
        sleep(public_wait)

        working_mode = get_current_workingmode(mqtt_server,port=mqtt_port)
        if (bytedata[2] != working_mode):
            print("Change working mode form {} to {}".format(bytedata[2],working_mode))
            set_sensor_working_mode(sensor_obj.address,working_mode)

        print("Used: ",bytedata[4])
        client.publish("{}/sensor/room_{}/usage".format(mqtt_room_topic,sensorID),bytedata[4])

        print("Temp: {}{} °C".format(chr(bytedata[6]),bytedata[7]))
        sleep(public_wait)

        #check Temperature
        temp_switch = 1
        if chr(bytedata[6]) == '-':
            temp_switch = -1
        #if temperature is negativ
        client.publish("{}/sensor/room_{}/temperature".format(mqtt_room_topic,sensorID),bytedata[7]*temp_switch)
        
        #Airqualitiy
        sleep(public_wait)
        air_bytes = bytearray()
        air_bytes.append(bytedata[9])
        air_bytes.append(bytedata[10])
        air_quality = int.from_bytes(air_bytes,'big')
        print("Air: {} ppm".format(air_quality))
        client.publish("{}/sensor/room_{}/airquality".format(mqtt_room_topic,sensorID),air_quality)

        #Humidity
        sleep(public_wait)
        print("Humidity: {}%".format(bytedata[8]))
        client.publish("{}/sensor/room_{}/humidity".format(mqtt_room_topic,sensorID),bytedata[8])

        #Battery
        sleep(public_wait)
        print("Battery: {}%".format(bytedata[13]))
        client.publish("{}/sensor/room_{}/battery".format(mqtt_room_topic,sensorID),bytedata[13])

        #PIR-Sensor-Trigger
        sleep(public_wait)
        print("PIR: ",bytedata[5])
        client.publish("{}/sensor/room_{}/trigger".format(mqtt_room_topic,sensorID),bytedata[5])
        sleep(public_wait)
        #IF PIR-Sensor is triggered, then swich to Sensor-Mode 2
        if bytedata[5] > 0:
            client.publish("{}/sensor_mode".format(mqtt_room_topic),2,retain=True)
        sleep(public_wait)
        print("RSSI: ", sensor_obj.rssi)
        client.publish("{}/sensor/room_{}/rssi".format(mqtt_room_topic,sensorID),sensor_obj.rssi)
        sleep(public_wait)
        print("Addr: ", sensor_obj.address)

    #Chair - Sensor
    if chr(bytedata[3]) == 'C':
        print("\nChair")

        print("Modus: ",bytedata[2])
        client.publish("{}/sensor/se_lab_hopper_{}/sensor_mode".format(mqtt_room_topic,sensorID),bytedata[2])
        sleep(public_wait)
        #Ask current working_mode via MQTT
        working_mode = get_current_workingmode(mqtt_server,mqtt_port)

        #If Working_mode is different then current mode of sensor it have to be switched
        if (bytedata[2] != working_mode):
            print("Change working mode form {} to {}".format(bytedata[2],working_mode))
            set_sensor_working_mode(sensor_obj.address,working_mode)

        #Used-Flag
        print("Used: ",bytedata[4])
        client.publish("{}/sensor/se_lab_hopper_{}/usage".format(mqtt_room_topic,sensorID),bytedata[4])
        sleep(public_wait)

        #Is Sensor Triggered?
        print("Seat: ",bytedata[5])
        client.publish("{}/sensor/se_lab_hopper_{}/usage_seat".format(mqtt_room_topic,sensorID),bytedata[5])
        sleep(public_wait)

        #Chair-Usability (0-4096)
        sleep(public_wait)
        seat_bytes = bytearray()
        seat_bytes.append(bytedata[8])
        seat_bytes.append(bytedata[9])
        seat_detail = int.from_bytes(seat_bytes,'big')
        print("Seat_detail: {}".format(seat_detail))
        client.publish("{}/sensor/se_lab_hopper_{}/seat_detail".format(mqtt_room_topic,sensorID),seat_detail)

        #Battery
        sleep(public_wait)
        print("Battery: {}%".format(bytedata[13]))
        client.publish("{}/sensor/se_lab_hopper_{}/battery".format(mqtt_room_topic,sensorID),bytedata[13])

        sleep(public_wait)
        print("RSSI: ", sensor_obj.rssi)
        client.publish("{}/sensor/se_lab_hopper_{}/rssi".format(mqtt_room_topic,sensorID),sensor_obj.rssi)
        sleep(public_wait)
        print("Addr: ", sensor_obj.address)
    
    #Table-Sensor
    if chr(bytedata[3]) == 'T':
        print("Table")
        print("Modus: ",bytedata[2])

        client.publish("{}/sensor/se_lab_table_{}/sensor_mode".format(mqtt_room_topic,sensorID),bytedata[2])
        sleep(public_wait)

        #Ask current working_mode via MQTT
        working_mode = get_current_workingmode(mqtt_server,mqtt_port)

        #If Working_mode is different then current mode of sensor it have to be switched
        if (bytedata[2] != working_mode):
            print("Change working mode form {} to {}".format(bytedata[2],working_mode))
            set_sensor_working_mode(sensor_obj.address,working_mode)
        
        #Used-Flag
        print("Used: ",bytedata[4])
        client.publish("{}/sensor/se_lab_table_{}/usage".format(mqtt_room_topic,sensorID),bytedata[4])
        sleep(public_wait)

        #Triggered?
        print("Trigged: ",bytedata[5])
        client.publish("{}/sensor/se_lab_table_{}/trigger".format(mqtt_room_topic,sensorID),bytedata[5])
        sleep(public_wait)

        #Distance
        print("Distance: ",bytedata[8])
        client.publish("{}/sensor/se_lab_table_{}/distance".format(mqtt_room_topic,sensorID),bytedata[8])
        sleep(public_wait)

        #Battery
        sleep(public_wait)
        print("Battery: {}%".format(bytedata[13]))
        client.publish("{}/sensor/se_lab_table_{}/battery".format(mqtt_room_topic,sensorID),bytedata[13])

        sleep(public_wait)
        print("RSSI: ", sensor_obj.rssi)
        client.publish("{}/sensor/se_lab_table_{}/rssi".format(mqtt_room_topic,sensorID),sensor_obj.rssi)
        sleep(public_wait)
        print("Addr: ", sensor_obj.address)

    #Whiteboard Rack sensor - Whiteboard
    if chr(bytedata[3]) == 'W':
        print("Whiteboard Rack")
        print("Modus: ",bytedata[2])

        client.publish("{}/sensor/se_lab_board_{}/sensor_mode".format(mqtt_room_topic,sensorID),bytedata[2])
        sleep(public_wait)

        #Ask current working_mode via MQTT
        working_mode = get_current_workingmode(mqtt_server,mqtt_port)

        #If Working_mode is different then current mode of sensor it have to be switched
        if (bytedata[2] != working_mode):
            print("Change working mode form {} to {}".format(bytedata[2],working_mode))
            set_sensor_working_mode(sensor_obj.address,working_mode)
        
        #Used-Flag
        print("Used: ",bytedata[4])
        client.publish("{}/sensor/se_lab_board_{}/usage".format(mqtt_room_topic,sensorID),bytedata[4])
        sleep(public_wait)

        #Triggered?
        print("Trigged: ",bytedata[5])
        client.publish("{}/sensor/se_lab_board_{}/trigger".format(mqtt_room_topic,sensorID),bytedata[5])
        sleep(public_wait)

        #Temperature
        print("Temp: {}{} Celsius".format(chr(bytedata[6]),bytedata[7]))
        temp_switch = 1
        if chr(bytedata[6]) == '-':
            temp_switch = -1
        client.publish("{}/sensor/se_lab_board_{}/temperature".format(mqtt_room_topic,sensorID),bytedata[7]*temp_switch)

        #Vibration-detection
        sleep(public_wait)
        vibration_bytes = bytearray()
        vibration_bytes.append(bytedata[8])
        vibration_bytes.append(bytedata[9])
        vibration_detail = int.from_bytes(vibration_bytes,'big')
        print("vibration_detail: {}".format(vibration_detail))
        client.publish("{}/sensor/se_lab_board_{}/vibration_detail".format(mqtt_room_topic,sensorID),vibration_detail)

        #Gyro-Measurements
        sleep(public_wait)
        gyro_x = bytedata[10]
        gyro_y = bytedata[11]
        gyro_z = bytedata[12]
        print("Gyrodata:\t X:{}\tY:{}\tZ:{}".format(gyro_x,gyro_y,gyro_z))
        client.publish("{}/sensor/se_lab_board_{}/diff_gyro_x".format(mqtt_room_topic,sensorID),gyro_x)
        sleep(public_wait)
        client.publish("{}/sensor/se_lab_board_{}/diff_gyro_y".format(mqtt_room_topic,sensorID),gyro_y)
        sleep(public_wait+0.1)
        client.publish("{}/sensor/se_lab_board_{}/diff_gyro_z".format(mqtt_room_topic,sensorID),gyro_z)

        #Battery
        sleep(public_wait)
        print("Battery: {}%".format(bytedata[13]))
        client.publish("{}/sensor/se_lab_board_{}/battery".format(mqtt_room_topic,sensorID),bytedata[13])

        #RSSI
        sleep(public_wait)
        print("RSSI: ", sensor_obj.rssi)
        client.publish("{}/sensor/se_lab_board_{}/rssi".format(mqtt_room_topic,sensorID),sensor_obj.rssi)
        sleep(public_wait)
        print("Addr: ", sensor_obj.address)
    
    print("\n\n")
    pass

def on_message(client,userdata,msg):
    global SENSOR_MODE
    SENSOR_MODE = msg.payload.decode()
    client.disconnect()

def get_current_workingmode(mqtt_server,port=1883,timeout=60,mqtt_room_topic='testroom'):
    global MQTT_CA_FILE
    global MQTT_USER_NAME
    global MQTT_USER_PW
    client = mqtt.Client("MQTT_SERVER")

    if MQTT_CA_FILE != None:
        client.tls_set(MQTT_CA_FILE)
        client.tls_insecure_set(True)
        client.username_pw_set(MQTT_USER_NAME,MQTT_USER_PW)
    
    client.connect(mqtt_server,port,timeout)
    client.subscribe("{}/sensor_mode".format(mqtt_room_topic))
    client.on_message = on_message
    sleep(0.5)
    client.loop_forever()
    return int(SENSOR_MODE)
