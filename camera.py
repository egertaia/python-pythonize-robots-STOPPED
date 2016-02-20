
import cv2
import numpy as np
from collections import deque
from math import sin
from time import time
class VideoCamera(object):

    BUFFER_SIZE = 64
    ballLower = (5, 160, 160)
    ballUpper = (20, 255, 255)
    pts = deque(maxlen=BUFFER_SIZE)

    def __init__(self):
        self.video = cv2.VideoCapture(0)
        self.cache = None

    def __del__(self):
        self.video.release()

    def get_frame(self):
        image = self.editFrame()

        # image = VideoCamera.resize(image,512)
        ret, jpeg = cv2.imencode('.jpg', image)

        self.cache = jpeg.tobytes()
        return jpeg.tobytes()

    @staticmethod
    def resize(frame,newWidth):
        width   = np.size(frame, 1)
        height  = np.size(frame, 0)

        ratio   = newWidth/width

        frame = cv2.resize(frame, (int(newWidth),int(height*ratio)) )
        return frame

    def editFrame(self):
        success, frame = self.video.read()
        original = frame
        frame = cv2.flip(frame, 1)
        original = cv2.flip(original, 1)

        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv, self.ballLower, self.ballUpper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
        center = None
        if len(cnts) > 0:

            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            if radius > 5:

                cv2.circle(frame, (int(x), int(y)), int(radius),
                    (0, 255, 255), 2)
                cv2.circle(frame, center, 5, (0, 0, 255), -1)
                radius = 1/radius
                radius = round(radius*100*11.35, 2)
                cv2.putText(frame,str(radius),(int(x),int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.7,(255,255,255),1,cv2.LINE_AA)
                cv2.putText(frame,str(radius),(int(x+3),int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.59,(0,0,0),1,cv2.LINE_AA)


        #self.pts.appendleft(center)


        # for i in range(1, len(self.pts)):
        #
        #     if self.pts[i - 1] is None or self.pts[i] is None:
        #         continue
        #
        #     thickness = int(np.sqrt(self.BUFFER_SIZE / float(i + 1)) * 2.5)
        #     cv2.line(frame, self.pts[i - 1], self.pts[i], (0, 0, 255), thickness)

        # frame,mask =  VideoCamera.resize(frame,512), VideoCamera.resize(mask,512)
        # mask = cv2.cvtColor(mask, cv2.COLOR_HSV2GRAY)
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # frame,mask = cv2.resize(frame, (512,512) ), cv2.resize(mask, (512,512) )
        cutout = cv2.bitwise_and(original,original, mask= mask)

        # frame = cv2.add(frame, mask)

        frame = np.hstack([frame, cutout])
        return frame
