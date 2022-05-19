import cv2
from gaze_tracking import GazeTracking

gaze = GazeTracking()
webcam = cv2.VideoCapture(0)
# webcam = cv2.VideoCapture("../Test Image/sample2.mp4")
eyeFlag = 0


while True:
    _, frame = webcam.read()
    gaze.refresh(frame)

    new_frame = gaze.annotated_frame()
    text = ""

    global eyeFlag

    if gaze.is_center():
        text = "Looking center"
        eyeFlag = 0
    elif gaze.is_left():
        text = "Looking left"
        eyeFlag = -1
    elif gaze.is_right():
        text = "Looking right"
        eyeFlag = 1

    cv2.putText(new_frame, text, (60, 60), cv2.FONT_HERSHEY_DUPLEX, 2, (255, 0, 0), 2)
    cv2.imshow("Demo", new_frame)

    if cv2.waitKey(1) == 27:
        break
