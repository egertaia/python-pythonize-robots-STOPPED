import cv2
import numpy as np
import signal
import sys
from flask import Flask, render_template, Response, request
from collections import deque
from datetime import datetime
from time import time, sleep
from threading import Thread

try:
    from PyMata.pymata import PyMata
 
    class Motors(Thread):
        MOTOR_1_PWM = 2
        MOTOR_1_A   = 3
        MOTOR_1_B   = 4
        MOTOR_2_PWM = 5
        MOTOR_2_A   = 6
        MOTOR_2_B   = 7
        MOTOR_3_PWM = 8
        MOTOR_3_A   = 9
        MOTOR_3_B   = 10
     
        def __init__(self):
            Thread.__init__(self)
            self.daemon = True
            self.board = PyMata()
            def signal_handler(sig, frame):
                self.stop_motors()
                self.board.reset()
                sys.exit(0)
            signal.signal(signal.SIGINT, signal_handler)
            self.board.set_pin_mode(self.MOTOR_1_PWM, self.board.PWM,    self.board.DIGITAL)
            self.board.set_pin_mode(self.MOTOR_1_A,   self.board.OUTPUT, self.board.DIGITAL)
            self.board.set_pin_mode(self.MOTOR_1_B,   self.board.OUTPUT, self.board.DIGITAL)
            self.board.set_pin_mode(self.MOTOR_2_PWM, self.board.PWM,    self.board.DIGITAL)
            self.board.set_pin_mode(self.MOTOR_2_A,   self.board.OUTPUT, self.board.DIGITAL)
            self.board.set_pin_mode(self.MOTOR_2_B,   self.board.OUTPUT, self.board.DIGITAL)
            self.board.set_pin_mode(self.MOTOR_3_PWM, self.board.PWM,    self.board.DIGITAL)
            self.board.set_pin_mode(self.MOTOR_3_A,   self.board.OUTPUT, self.board.DIGITAL)
            self.board.set_pin_mode(self.MOTOR_3_B,   self.board.OUTPUT, self.board.DIGITAL)
            self.dx, self.dy = 0, 0
     
        def stop_motors(self):
            self.board.digital_write(self.MOTOR_1_B, 0)
            self.board.digital_write(self.MOTOR_1_A, 0)
            self.board.digital_write(self.MOTOR_2_B, 0)
            self.board.digital_write(self.MOTOR_2_A, 0)
            self.board.digital_write(self.MOTOR_3_B, 0)
            self.board.digital_write(self.MOTOR_3_A, 0)
     
        def run(self):
            while True:
                # Reset all direction pins to avoid damaging H-bridges  
                # TODO: USE dx,dy now in (-1,1)+(None,None) range
                self.stop_motors()
     
                dist = abs(self.dx)
                if dist > 0.2: #was 2
                    if self.dx > 0:
                        print("Turning left")
                        self.board.digital_write(self.MOTOR_1_B, 1)
                        self.board.digital_write(self.MOTOR_2_B, 1)
                        self.board.digital_write(self.MOTOR_3_B, 1)
                    else:
                        print("Turning right")
                        self.board.digital_write(self.MOTOR_1_A, 1)
                        self.board.digital_write(self.MOTOR_2_A, 1)
                        self.board.digital_write(self.MOTOR_3_A, 1)
                    self.board.analog_write(self.MOTOR_1_PWM, int(dist ** 0.7 + 25))
                    self.board.analog_write(self.MOTOR_2_PWM, int(dist ** 0.7 + 25))
                    self.board.analog_write(self.MOTOR_3_PWM, int(dist ** 0.7 + 25))
                # elif self.dy > 30:
                else:
                    print("Going forward")
                    self.board.digital_write(self.MOTOR_1_B, 1)
                    self.board.digital_write(self.MOTOR_3_A, 1)
                    self.board.analog_write(self.MOTOR_1_PWM, int(self.dy ** 0.5 )+30)
                    self.board.analog_write(self.MOTOR_2_PWM, 0)
                    self.board.analog_write(self.MOTOR_3_PWM, int(self.dy ** 0.5 )+30)
                sleep(0.03)
except:
    class Motors:
        def __init__(self):            
            self.dx, self.dy = 0, 0
        def start(self):
            print("Wrooom wroom!!!! (no motors found) ")

class FrameGrabber(Thread):
    def __init__(self, width=320, height=240):
        Thread.__init__(self)
        self.daemon = True
        self.video = cv2.VideoCapture(0)
        self.width,self.height = width,height
        self.video.set(3, width)
        self.video.set(4, height)
        self.timestamp = time()
        self.frames = 0
        self.fps = 50
        self.current_frame = self.video.read()[1]
        self.ballLower = (5, 140, 140)
        self.ballUpper = (30, 255, 255)
    
    def getFrameSize(self, frame=None):
        if frame==None:
            return self.width,self.height
        width   = np.size(frame, 1)
        height  = np.size(frame, 0)
        return width, height

    def getBallDelta(self,x,y):
        w,h     = self.width,self.height
        dx,dy   = x/w, y/h
        dx,dy   = (dx-0.5)*2,(dy-0.5)*2
        return dx,dy

    def run(self):
        while True:

            self.frames += 1
            timestamp_begin = time()
            if self.frames > 10:
                self.fps = self.frames / (timestamp_begin - self.timestamp)
                self.frames = 0
                self.timestamp = timestamp_begin

            _, frame    = self.video.read()
            frame       = cv2.flip(frame, 1)
            original    = frame
            blurred     = cv2.blur(frame, (4,4))
            hsv         = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
            mask        = cv2.inRange(hsv, self.ballLower, self.ballUpper)
            mask        = cv2.dilate(mask, None, iterations=2)
            cutout      = cv2.bitwise_and(frame,frame, mask= mask)
            cnts        = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

            if cnts:
                c = max(cnts, key=cv2.contourArea)
                (x, y), radius = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                if radius > 5:
                    cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                    cv2.circle(frame, center, 5, (0, 0, 255), -1)
                    radius = round( (1/radius)*1135, 2)
                    cv2.putText(original,str(radius),(int(x),int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.7,(255,255,255),1,cv2.LINE_AA)
                    cv2.putText(original,str(radius),(int(x+3),int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.59,(0,0,0),1,cv2.LINE_AA)

                    motors.dx, motors.dy = self.getBallDelta(x,y)

            cv2.putText(frame,"%.01f fps" % self.fps, (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.3,(255,255,255),1,cv2.LINE_AA)
            width, height = self.getFrameSize(frame=frame)
            cv2.putText(frame,str([round(motors.dx,2), round(motors.dy,2)]), (int(width*0.007),int(height*0.97)), cv2.FONT_HERSHEY_SIMPLEX, 0.3,(255,255,255),1,cv2.LINE_AA)

            self.current_frame = np.hstack([original, cutout])
 
motors  = Motors()
grabber = FrameGrabber()
motors.start()
grabber.start()
 
app = Flask(__name__)
 
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/nouislider.css')
def nouisliderCSS():
    return render_template('nouislider.css')
@app.route('/nouislider.js')
def nouisliderJS():
    return render_template('nouislider.js')
@app.route('/sliders')
def sliders():
    return render_template('sliders.html')
 
@app.route('/video_feed')
def video_feed():
    def generator():
        while True:
            if grabber.current_frame != None:
                ret, jpeg = cv2.imencode('.jpg', grabber.current_frame, (cv2.IMWRITE_JPEG_QUALITY, 10))
                yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n'
            sleep(0.002)
    return Response(generator(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/camera/config', methods=['get', 'post'])
def config():
    global grabber
    blH = int(request.form.get('blH')) #int cant be none
    blS = int(request.form.get('blS'))
    blV = int(request.form.get('blV'))
    bhH = int(request.form.get('bhH'))
    bhS = int(request.form.get('bhS'))
    bhV = int(request.form.get('bhV'))
    print ("lower range is now: " , grabber.ballLower , (blH, blS, blV))
    grabber.ballLower = (blH, blS, blV)
    print("Higher range is now: " ,grabber.ballUpper, (bhH, bhS, bhV))
    grabber.ballUpper = (bhH, bhS, bhV)
    return "OK" 
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True,use_reloader=False,threaded=True)