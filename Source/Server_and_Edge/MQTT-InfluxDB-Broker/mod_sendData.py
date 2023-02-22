from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from time import sleep, localtime, strftime,time
import paho.mqtt.client as mqtt
#disable SSL-CERT WARNINGS
import requests
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# You can generate an API token from the "API Tokens Tab" in the InfluxDB WebUI
def sendInfluxData(data,timestamp,
                    mqtt_topic=None,
                    influx_server="192.168.178.36",
                    influx_port=8086,
                    influx_bucket="sensor_data",
                    influx_org="sedus",
                    influx_token="cWFmcPImcclW0cnGn9ewKmYQxxXiNSJsPfHDMapNhGFqQfTrN7cIW9HVUOYusl-ujof1jtWSEDx0o9NRl7yHhw==",
                    use_tls = False
                    ):
    
    #set server URL based on encryption
    if (use_tls == True):
        server = "https://{}:{}".format(influx_server,influx_port)
    else:
        server = "http://{}:{}".format(influx_server,influx_port)

    with InfluxDBClient(url=server, token=influx_token, org=influx_org,ssl=True, verify_ssl=False) as client:
        
        #setup InlfuxDB client
        write_api = client.write_api(write_options=SYNCHRONOUS)
        
        #if no MQTT-Topic is given write simply the data
        if mqtt_topic == None:
            
            point = Point("Testroom") \
            .tag("sensor", "sensorxy") \
            .field("data", float(data)) \
            .time(datetime.utcfromtimestamp(timestamp), WritePrecision.NS)
        
        else:
            influx_points=mqtt_topic.split('/')

            #check if the MQTT-Topics are in the wished format
            if (len(influx_points) <4):
                print("invalid mqtt-format!")
                return "err"

            #Set the Datapoints for InfluxDB
            point = Point(influx_points[0]) \
            .tag(influx_points[1], influx_points[2]) \
            .field(influx_points[3], float(data)) \
            .time(datetime.utcfromtimestamp(int(timestamp)), WritePrecision.NS)

        #Write Datapoint to InfluxDB
        write_api.write(influx_bucket, influx_org, point)


#unencrypted MQTT
def sendMQTTData(MQTT_Server,topic,payload,port=1883,timeout=60,mqtt_retain=False):
    client = mqtt.Client()
    client.connect(MQTT_Server,port,timeout)
    client.publish(topic,payload,retain=mqtt_retain)
    client.disconnect()


#encrypted MQTT
def sendMQTTData_secure(MQTT_Server,topic,payload,mqtt_ca_cert,mqtt_secure_user,mqtt_secure_pw,port=8888,timeout=60,mqtt_retain=False):
    
    client = mqtt.Client()
    client.tls_set(mqtt_ca_cert)
    client.tls_insecure_set(True)
    client.username_pw_set(mqtt_secure_user,mqtt_secure_pw)
    client.connect(MQTT_Server,port,timeout)
    client.publish(topic,payload,retain=mqtt_retain)
    client.disconnect()

#Send Seconnects Sensor Data
def send_seconnects_sensor_data(data,sensor_data_endpoint,tenant_url,gw_device_id,mqtt_topic,sensor_type="desk",age=0,battery=101,count=999,rssi=-99,uptime=999):

    data_points=mqtt_topic.split('/')
    #check if the MQTT-Topics are in the wished format
    if (len(data_points) <4):
        print("invalid mqtt-format!")
        return "err"

    if(data_points[3] == 'usage'):
        presense = data
    else:
        presense = 0

    #get the last value which is the Sensor_mac
    sensor_mac = data_points[2].split('_')[-1]

    data={"chairs":[{
            "age":int(age),
            "battery":int(battery),
            "count":int(count),
            "fwvmajor":3,
            "fwvminor":41,
            "mac":sensor_mac,
            "present":presense,
            "rssi":int(rssi),
            "type":str(sensor_type)}],
            "deviceid":str(gw_device_id),
            "timestamp":int(time()),
            "uptime":int(uptime)}
    
    #Seconnects Sensor Gateway
    data_url = sensor_data_endpoint
    #data_url = 'https://sedus-gw-api.iot.kapschcloud.net/api/Data/uploadData'
    resp = requests.post(data_url,verify=False,headers={"Accept":"application/json","Referer":str(tenant_url)},json=data)
    jsondata_default = json.loads(resp.text)
    return jsondata_default
#testing
if __name__ == '__main__':
    #sendInfluxData(15,1637959636,mqtt_topic='testroom/sensor/se_lab_hopper_badeaffebadeafffe/usage')
    pass