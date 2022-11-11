import re
from flask import request
from flask import Flask
from flask import jsonify
from werkzeug.wrappers import response
import mod_sendData as sd

import os
import shutil
import json
import time

#Erstelle Flask-Objekt
app = Flask(__name__)


ALLOWED_INITIATORS =[
                    'camera_sensor',
                    'pir_sensor'
                    ]

#WORKINGMODE (0=OFF,1=ON,2=KEEPALIVE)
working_mode={
                "mode": 1,
                "initiator": "init",
                "timestamp": int(time.time())
            }



#Beispiel (Kann gelöscht werdne)
params={
            "operation":"program", # operation muss gesetzt sein: hier der operator program    
        }

#Route für das Schreiben von Sensordaten ins InfluxDB
@app.route('/writeSensorData',methods=['POST'])

def writeSensorData():

    if not request.json or not 'operation' in request.json:
        return jsonify({"Error":"operation missing"}),400

    #TODO
    sd.sendData()

#Route für das Lesen des Aktiven Working Modes
@app.route('/getWorkingMode',methods=['GET'])

def getWorkingMode():
    return jsonify(working_mode),200

#Route für das Schreiben des Aktiven Working Modes
@app.route('/setWorkingMode',methods=['POST'])

def setWorkingMode():

    if not request.json or not 'operation' in request.json:
        return jsonify({"Error":"operation value missing"}),400

    if not request.json or not 'mode' in request.json:
        return jsonify({"Error":"mode value missing"}),400

    if not request.json or not 'initiator' in request.json:
        return jsonify({"Error":"initiator value missing"}),400
    
    if request.json['initiator'] not in ALLOWED_INITIATORS:
        return jsonify({"Error":"initiator value missing"}),401
    
    if request.json['operation'] == 'modify':
        try:
            working_mode['mode'] = request.json['mode']
            working_mode['initiator'] = request.json['initiator']
            working_mode['timestamp'] = int(time.time())
            return jsonify({"message":"workingmode successfully changed"}),200
        except:
            return jsonify({"Error":"something went wrong"}),400


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8443,ssl_context='adhoc')
    #app.run(host="0.0.0.0", port=8443)
