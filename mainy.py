from flask import Flask, render_template, Response
from time import sleep
from camera import *

import threading

class Data:
    def __init__(self):
        self.data = None


def updater(data,camera):
    print("TERE")
    while True:
        frame = camera.get_frame()

        temp = (b'--frame\r\n'
                    b'Content-'
                    b'Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        with lock:
            data.data = temp
            #print("update")
        sleep(0.005)

# camera = cv2.VideoCapture(0)
camera = VideoCamera()

sleep(3)
lock = threading.Lock()

data = Data()
t = threading.Thread(target=updater, args=[data,camera])
t.start()

sleep(0.33)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def gen(data):
    while True:
       # with lock:
            yield data.data

@app.route('/video_feed')
def video_feed():
    global data
    return Response(gen(data),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True,use_reloader=False,threaded=True)