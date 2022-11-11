from flask import request
from flask import Flask
from werkzeug.utils import secure_filename
import os
import sys
import shutil
import json
import time
from io import BytesIO
from PIL import Image
import base64
import cv2
import numpy
import mod_read_config as read_config

#read config file
config_file = "/etc/people-counter-server/people_counter_server.yaml"
config = read_config.get_server_config(config_file)

#set needed globals out of config-file
UPLOAD_FOLDER = config['flask_config']['upload_folder']
DOCKER_CONTAINER = None
DOCKERMODE = config['openpose_config']['dockermode']
OPENPOSE_PYTHON = None
OPENPOSE_MODEL_FOLDER = None
OPENPOSE_NET_RESOLUTION = config['openpose_config']['op_param_net_resolution']
OPENPOSE_SCALE_NUMBER = config['openpose_config']['op_param_scale_number']
OPENPOSE_SCALE_GAP = config['openpose_config']['op_param_scale_gap']
OPENPOSE_MODEL = config['openpose_config']['op_param_model_pose']
OPENPOSE_LOGGING_LEVEL = config['openpose_config']['op_param_logging_level']



if DOCKERMODE == True:
    DOCKER_CONTAINER = config['openpose_config']['docker_container']
else:
    OPENPOSE_PYTHON = config['openpose_config']['op_param_python_folder']
    OPENPOSE_MODEL_FOLDER = config['openpose_config']['op_param_model_folder']

#create Flask-Object
app = Flask(__name__)
#the Upload-Folder is only needed by the Docker Solution
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


#get current time for logging
def get_current_time():
    t = time.localtime()
    current_time = time.strftime("%Y/%m/%d - %H:%M:%S", t)
    return str(current_time)

#function for peoplecountig inside a docker container
def count_people_docker(folder,jsonfilename):

    print('{}: Start - Imageprocessing {}'.format(get_current_time(),str(folder)))
    try:
        dockerstring = 'docker run --rm -v {}:/data {} -display 0 -image_dir /data -write_images /data -write_json /data -model_pose {} -net_resolution {} -scale_number {} -scale_gap {} >> /dev/null'.format(folder,DOCKER_CONTAINER,OPENPOSE_MODEL,OPENPOSE_NET_RESOLUTION,OPENPOSE_SCALE_NUMBER,OPENPOSE_SCALE_GAP)
        os.system(dockerstring)
        #jsonfile = open('C:\\temp\\images\\'+jsonfilename)
        jsonfile = open(os.path.join(folder,jsonfilename))
        openpose_result = json.load(jsonfile)
        jsonfile.close()
        shutil.rmtree(folder)
        print('{}: Done - Imageprocessing {}'.format(get_current_time(),str(folder)))
        return len(openpose_result['people'])
    except:
        print('{}: Error - Imageprocessing {}'.format(get_current_time(),str(folder)))
        if os.path.exists(folder):
            shutil.rmtree(folder)
        return -1

#function for peoplecounting directly with the OpenPose-API
def count_people_openpose_native(image):
    try:
        sys.path.append(OPENPOSE_PYTHON)
        from openpose import pyopenpose as op
        
        params = dict()
        params["model_folder"] = OPENPOSE_MODEL_FOLDER
        params["face"] = False
        params["hand"] = False
        params["display"] = 0
        params["model_pose"] = OPENPOSE_MODEL
        params["net_resolution"] = OPENPOSE_NET_RESOLUTION
        params["scale_number"] = OPENPOSE_SCALE_NUMBER
        params["scale_gap"] = OPENPOSE_SCALE_GAP
        params["logging_level"] = OPENPOSE_LOGGING_LEVEL
        
        opWrapper = op.WrapperPython()
        opWrapper.configure(params)
        opWrapper.start()
        
        datum = op.Datum()
        datum.cvInputData = image
        
        opWrapper.emplaceAndPop(op.VectorDatum([datum]))
        
        if type(datum.poseKeypoints) != type(None):
            return (len(datum.poseKeypoints))
        else:
            return 0
    except:
        return -1

#route for POST-Requests over /JsonPeopleCounting
@app.route('/JsonPeopleCounting',methods=['POST'])

#gets the picture-date out of a Base64-String inside the JSON-Data
def json2image():
    if request.method == 'POST':
        load = json.loads(request.json)
        imdata = base64.b64decode(load['image'])
        image = Image.open(BytesIO(imdata))
        picture_gray = cv2.cvtColor(numpy.array(image),cv2.COLOR_RGB2BGR)

        #if docker is used create a picture to use it inside docker
        #otherwise only use the data inside the picture_gray numpy_array
        if DOCKERMODE == True:
            filename = secure_filename(load['filename'])
            tempfolderpath =os.path.join(app.config['UPLOAD_FOLDER'],filename.split('.')[0])
            os.mkdir(tempfolderpath)
            cv2.imwrite("{}/{}".format(tempfolderpath,filename),picture_gray)
            jsonfilename = filename.split('.')[0]+'_keypoints.json'
            peoplecount = count_people_docker(tempfolderpath,jsonfilename)
        else:
            peoplecount = count_people_openpose_native(picture_gray)
        return str(peoplecount),200

#route for Post-Request over /FilePeopleCounting
@app.route('/FilePeopleCounting',methods=['POST'])

#function to handle picture-data over Post-Request
def getPicture():

    if request.method == 'POST':
        if 'file' not in request.files:
            print('No file part')
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            tempfolderpath =os.path.join(app.config['UPLOAD_FOLDER'],filename.split('.')[0])
            tempfilepath = os.path.join(tempfolderpath,filename)
            os.mkdir(os.path.join(app.config['UPLOAD_FOLDER'],filename.split('.')[0]))
            file.save(tempfilepath)
            jsonfilename = filename.split('.')[0]+'_keypoints.json'
            peoplecount = count_people_docker(tempfolderpath,jsonfilename)
            return str(peoplecount),200

#start FLASK-Service on port 8443
#create an AdHoc self-signed SSL Certificate for encrypted communication
#Listen on all interfaces "0.0.0.0"
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8443,ssl_context='adhoc')
