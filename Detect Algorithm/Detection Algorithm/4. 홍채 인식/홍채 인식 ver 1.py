import cv2
from gaze_tracking import GazeTracking
import queue

"""
def queueUpdate(queueName, angle):
    movingQueue = queueName

    if movingQueue.qsize() == 10:
        movingQueue.get()
        movingQueue.put(angle)
    elif movingQueue.qsize() < 10:
        movingQueue.put(angle)

    sum = 0

    for index in range(0, movingQueue.qsize()):
        data = movingQueue.get()
        sum += data
        # print("data = ", data)
        # print("sum = ", sum)

        movingQueue.put(data)

    movingAverage = sum / movingQueue.qsize()
    print(movingAverage)

    if queueName == "EYE_movingQueue":
        global EYE_movingQueue
        EYE_movingQueue = movingQueue

    return movingAverage
"""

gaze = GazeTracking()
webcam = cv2.VideoCapture(0)
# webcam = cv2.VideoCapture("../Test Image/sample2.mp4")
eyeFlag = 0
# EYE_movingQueue = queue.Queue()
# EYE_movingAverage = 0

while True:
    _, frame = webcam.read()
    gaze.refresh(frame)

    new_frame = gaze.annotated_frame()
    text = ""

    if gaze.is_center():
        text = "Looking center"
        eyeFlag = 0
    elif gaze.is_left():
        text = "Looking left"
        eyeFlag = -1
    elif gaze.is_right():
        text = "Looking right"
        eyeFlag = 1

    print("EyeFlag = ", eyeFlag)

    # DB에 flag 정보 저장 (일정 시간을 간격으로 주기)

    cv2.putText(new_frame, text, (60, 60), cv2.FONT_HERSHEY_DUPLEX, 2, (255, 0, 0), 2)
    cv2.imshow("Demo", new_frame)

    if cv2.waitKey(1) == 27:
        break
