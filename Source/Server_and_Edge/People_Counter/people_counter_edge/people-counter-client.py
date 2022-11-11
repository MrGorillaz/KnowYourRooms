import json
import cv2
import requests
import time
from time import sleep
from time import strftime
from datetime import datetime
import os
import mod_sendData
import base64
from sys import platform
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import mod_read_config as read_config

print("START SERVICE")

#get configuration
config_file = "/etc/people-counter-client/people_counter_config.yaml"
config = read_config.get_server_config(config_file)

#set globals out of configurationfile
WORK_START_HOUR = config['general_config']['start_hour']
WORK_END_HOUR = config['general_config']['end_hour']
#WORK_MODE = config['general_config']['standalone_mode']
KAMERA_ID = config['general_config']['use_camera_id']
SEND_MODE = config['general_config']['send_mode']
WAIT_SHORT = config['general_config']['wait_seconds_short']
WAIT_LONG = config['general_config']['wait_seconds_long']
SLEEP_TIME = config['general_config']['sleep_seconds']
SW_PICTURE = config['general_config']['sw_picture']
OPENPOSE_SERVER = "{}://{}:{}".format(config['openpose_config']['protocol'],config['openpose_config']['server'],config['openpose_config']['port'])

#OPENPSOE_WORKING_MODES: 
# ->>> "FILE" : takes a picture and transfer it to openPose Endpoint
# ->>> "JSON" : takes a picture, encode it to Base64 and send a jsonstring to openPose Endpoint
OPENPOSE_WORKING_MODE = config['openpose_config']['working_mode']

if OPENPOSE_WORKING_MODE == "FILE":
    OPENPOSE_SERVER = "{}/FilePeopleCounting".format(OPENPOSE_SERVER)
elif OPENPOSE_WORKING_MODE == "JSON":
    OPENPOSE_SERVER = "{}/JsonPeopleCounting".format(OPENPOSE_SERVER)
else:
    print("NO WORKING MODE GIVEN!")
    exit(-1)

#Send Modes
if SEND_MODE == "MQTT":
    MQTT_SERVER = config['mqtt_config']['mqtt_server']
    MQTT_PORT = config['mqtt_config']['mqtt_port']
    MQTT_TIMEOUT = config['mqtt_config']['mqtt_timeout']
    MQTT_COUNT_TOPIC = config['mqtt_config']['mqtt_count_topic']
    MQTT_USAGE_TOPIC = config['mqtt_config']['mqtt_usage_topic']
    MQTT_SECURE = False #standard is false
    
    #get MQTT-Secure settings
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

elif SEND_MODE == "INFLUX":
    INFLUXDB_SERVER = config['influxdb_config']['influxdb_server']
    INFLUXDB_PORT = config['influxdb_config']['influxdb_port']
    INFLUXDB_API_TOKEN = config['influxdb_config']['influxdb_api_token']
    INFLUXDB_BUCKET = config['influxdb_config']['influx_bucket']
    INFLUXDB_ORG = config['influxdb_config']['influx_org']
    INLFUXDB_COUNT_TOPIC = config['influxdb_config']['influx_count_topic']
    INLFUXDB_USAGE_TOPIC = config['influxdb_config']['influx_usage_topic']
    INFLUXDB_SECURE = False

    try:
        INFLUXDB_SECURE = config['influxdb_config']['influxdb_tls_enable']
    except:
        pass

else:
    print("ERROR - UNKOWN SEND MODE")
    exit(-1)


SENSOR_MODE = {"SLEEP":0,"AWAKE":1,"WORKING":2}

#take a picture and save it in a OpenCV-Numpy-array
#encode Image to Base64
def image2json(img,filename):

    ret , image = cv2.imencode('.PNG',img)
    jsonPic = json.dumps({"image": base64.b64encode(image).decode('ascii'),
                           "filename": filename })
    return jsonPic


#take a picture
def take_picture(cam,picture_name,mode="FILE"):

    #get OS-Settings for optimal camera-usage
    print("{} | TAKE PICTURE".format(get_log_time()))
    
    #windows
    if 'win32' in platform:
        camera = cv2.VideoCapture(cam,cv2.CAP_DSHOW)
        time.sleep(1.0)
    #linux
    else:
        camera = cv2.VideoCapture(cam,cv2.CAP_V4L2)
        time.sleep(1.0)

    #get frames of taken picutes
    ret, picture = camera.read()
    #release camera-object
    camera.release()


    if not ret:
        print("{} | NO PICTURE TAKEN!".format(get_log_time()))
        return False
    else:
        if (SW_PICTURE):
        #Convert picture to gray to save memory (optional)
            picture_gray = cv2.cvtColor(picture,cv2.COLOR_BGR2GRAY)
        else:
            picture_gray = picture

        #FILE-MODUS
        if mode == "FILE":
            try:
                #try to save picture as a file
                cv2.imwrite(picture_name,picture_gray)
                return True
            except:
                return False

        #JSON-MODUS
        if mode == "JSON":
            try:
                jsonPicture = image2json(picture_gray,filename)
                return jsonPicture
            except:
                return False

#function for peoplecounting over a taken picturefile
#this interface handles peoplecounting over files
def get_people_file(url,filename):
    files = {'file': open(filename, 'rb')}
    try:
        responce = requests.post(url,json={'picturename': filename}, files=files, verify=False)
        return responce.text
    except:
        return 0

#function to handle peoplecountig over json-files
#picture has to be Base64 encoded with the key "image" inside the json
def get_people_json(url,jsondata):
    try:
        response = requests.post(url,json=jsondata,verify=False)
        return response.text
    except:
        return 0


#function to get log-time
def get_log_time():
    log_time = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    return log_time

#Do forever
while(True):

    #get current hour
    current_hour = int(time.strftime("%H",time.localtime()))
    #Only take Pictures in the timeslot between WORK_START_HOUR and WORK_END_HOUR
    if (current_hour >= WORK_START_HOUR) and (current_hour <= WORK_END_HOUR):
        try:
            #get current unix-timestamp
            timestamp = int(time.time())

            #set a filename for the temporary picture
            filename = "PeopleCount_"+str(timestamp)+".png"

            #Take Picture base on openPose Working Mode
            if OPENPOSE_WORKING_MODE.upper() == "FILE":

                pic = take_picture(KAMERA_ID,filename,mode="FILE")
                #send to openPose-Endpoint for counting
                print("{} | WAITING FOR RESULT...".format(get_log_time()))
                result = get_people_file(OPENPOSE_SERVER,filename)
                #delete old Image after counting
                os.remove(filename)


            if OPENPOSE_WORKING_MODE.upper() == "JSON":
                
                pic = take_picture(KAMERA_ID,filename,mode="JSON")
                print("{} | WAITING FOR RESULT...".format(get_log_time()))
                if pic != False:
                    result = get_people_json(OPENPOSE_SERVER,pic)
                else:
                    result = -1
            print("{} | COUNTED PEOPLE: {}".format(get_log_time(),result))


            #Behavior of Send Modes
            #Send Results via MQTT
            if SEND_MODE.upper() == "MQTT":
                mqtt_count_payload = "{}:{}".format(timestamp,result)
                
                if (int(result)>0):
                    mqtt_usage_payload = "{}:{}".format(timestamp,1)
                else:
                    mqtt_usage_payload = "{}:{}".format(timestamp,0)
                
                if MQTT_SECURE == False:

                    mod_sendData.sendMQTTData(MQTT_SERVER,topic=MQTT_COUNT_TOPIC,payload=mqtt_count_payload,port=MQTT_PORT,timeout=MQTT_TIMEOUT)
                    time.sleep(0.2)
                    mod_sendData.sendMQTTData(MQTT_SERVER,topic=MQTT_USAGE_TOPIC,payload=mqtt_usage_payload,port=MQTT_PORT,timeout=MQTT_TIMEOUT)
                    time.sleep(0.2)
                else:
                    mod_sendData.sendMQTTData_secure(MQTT_SERVER,
                                                        topic=MQTT_COUNT_TOPIC,
                                                        payload=mqtt_count_payload,
                                                        mqtt_ca_cert=MQTT_CA_FILE,
                                                        mqtt_secure_user=MQTT_SECURE_USER,
                                                        mqtt_secure_pw=MQTT_SECURE_PW,
                                                        port=MQTT_SECURE_PORT,
                                                        timeout=MQTT_TIMEOUT)
                    time.sleep(0.2)
                    mod_sendData.sendMQTTData_secure(MQTT_SERVER,
                                                        topic=MQTT_USAGE_TOPIC,
                                                        payload=mqtt_usage_payload,
                                                        mqtt_ca_cert=MQTT_CA_FILE,
                                                        mqtt_secure_user=MQTT_SECURE_USER,
                                                        mqtt_secure_pw=MQTT_SECURE_PW,
                                                        port=MQTT_SECURE_PORT,
                                                        timeout=MQTT_TIMEOUT)
                    time.sleep(0.2)
            #Send Results directly to INFLUXDB
            elif SEND_MODE.upper() == "INFLUX":
                mod_sendData.sendInfluxData(result,
                                            timestamp,
                                            mqtt_topic=INLFUXDB_COUNT_TOPIC,
                                            influx_server=INFLUXDB_SERVER,
                                            influx_port=INFLUXDB_PORT,
                                            influx_bucket=INFLUXDB_BUCKET,
                                            influx_org=INFLUXDB_ORG,
                                            influx_token=INFLUXDB_API_TOKEN,
                                            use_tls=INFLUXDB_SECURE)
                time.sleep(0.2)

                if (int(result)>0):
                    influx_usage_data = 1
                else:
                    influx_usage_data = 0

                mod_sendData.sendInfluxData(influx_usage_data,
                                            timestamp,
                                            mqtt_topic=INLFUXDB_USAGE_TOPIC,
                                            influx_server=INFLUXDB_SERVER,
                                            influx_port=INFLUXDB_PORT,
                                            influx_bucket=INFLUXDB_BUCKET,
                                            influx_org=INFLUXDB_ORG,
                                            influx_token=INFLUXDB_API_TOKEN,
                                            use_tls=INFLUXDB_SECURE)

            
            #sleep for a given time based on result
            if(int(result)>0):
                #sleep short
                print("{} | SLEEPING FOR {}".format(get_log_time(),WAIT_SHORT))
                time.sleep(float(WAIT_SHORT))
                
            else:
                #sleep long
                print("{} | SLEEPING FOR {}".format(get_log_time(),WAIT_LONG))
                time.sleep(float(WAIT_LONG))
                
        except:
            #try to delete picture if something goes wrong
            try:
                if (os.path.exists(filename)):
                    os.remove(filename)
            
            #close programm with CTRL+C (in console-mode)
            except KeyboardInterrupt:
                exit()
            except:
                pass
    else:
        #Sleep for an hour (no use for night)
        if MQTT_SECURE == False:
            mod_sendData.sendMQTTData(MQTT_SERVER,MQTT_USAGE_TOPIC,SENSOR_MODE["SLEEP"],mqtt_retain=True)
        else:
             mod_sendData.sendMQTTData_secure(MQTT_SERVER,
                                                        topic=MQTT_USAGE_TOPIC,
                                                        payload=SEND_MODE['SLEEP'],
                                                        mqtt_ca_cert=MQTT_CA_FILE,
                                                        mqtt_secure_user=MQTT_SECURE_USER,
                                                        mqtt_secure_pw=MQTT_SECURE_PW,
                                                        port=MQTT_SECURE_PORT,
                                                        timeout=MQTT_TIMEOUT)
        print("{} | I guess nobody is here, GOOD NIGHT!".format(get_log_time()))
        time.sleep(float(SLEEP_TIME))
