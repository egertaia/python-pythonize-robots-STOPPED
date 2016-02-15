import cv2
import numpy as np

cap = cv2.VideoCapture(0)

while(1):

    # Take each frame
    _, frame = cap.read()

    #Blur the image
    blur = cv2.medianBlur(frame,23)

    # Convert BGR to HSV
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

    # define ball color in HSV
    ORANGE_MIN = np.array([6, 50, 50],np.uint8)
    ORANGE_MAX = np.array([12, 255, 255],np.uint8)

    frame_threshed = cv2.inRange(hsv, ORANGE_MIN, ORANGE_MAX)
    cv2.imshow('output2.jpg', frame_threshed)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()