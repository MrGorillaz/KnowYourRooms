from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
#disable SSL-CERT WARNINGS
import requests
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
        
        #if now MQTT-Topic is given write simply the data
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

#testing
if __name__ == '__main__':
    sendInfluxData(15,1637959636,mqtt_topic='testroom/sensor/se_lab_hopper_badeaffebadeafffe/usage')