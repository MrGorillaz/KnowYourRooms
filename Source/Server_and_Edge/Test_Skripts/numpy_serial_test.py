import json
from json import JSONEncoder
import cv2
import base64
import requests
import time
import numpy
from io import BytesIO
from PIL import Image

#Clientside
def image2json(img):

    ret , image = cv2.imencode('.JPG',img)
    jsonPic = json.dumps({"image": base64.b64encode(image).decode('ascii')})
    return jsonPic

#Serverside
def json2image(jsonfile):
    load = json.loads(jsonfile)
    imdata = base64.b64decode(load['image'])
    im = Image.open(BytesIO(imdata))
    return im
    pass


camera = cv2.VideoCapture(0,cv2.CAP_DSHOW)
time.sleep(1.0)
#Lese einen Frame der aktuellen Kamera
ret, picture = camera.read()
#print(ret)
#print(picture)
camera.release()

picture = cv2.cvtColor(picture,cv2.COLOR_BGR2GRAY)
jsonPicture = image2json(picture)
picture2 = json2image(jsonPicture)

picture_gray = cv2.cvtColor(numpy.array(picture2),cv2.COLOR_RGB2BGR)
cv2.imwrite("test.png",picture_gray)

print("halt")