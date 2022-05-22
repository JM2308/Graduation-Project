"""
Demonstration of the GazeTracking library.
Check the README.md for complete documentation.
"""

import cv2
from gaze_tracking import GazeTracking
import time
import math

gaze = GazeTracking()
cap = cv2.VideoCapture(0)

start = time.time()
gazeResult = [0, 0, 0, 0]
preSec = 0

while True:
    # We get a new frame from the webcam
    _, frame = cap.read()

    # We send this frame to GazeTracking to analyze it
    gaze.refresh(frame)

    frame = gaze.annotated_frame()
    text = ""

    # 3초 간격으로 저장 (3초가 한순간에 딱 측정되는 것이 X! 그 순간 1초 동안 계속 측정)
    # So, 1초 동안 가장 많이 측정된 경우를 파악하고 이 데이터를 저장!
    # gaze = [blinkingNum, rightNum, leftNum, centerNum]의 형태
    nowSec = math.trunc(int(time.time() - start)) + 1
    if nowSec % 3 == 0:
        # print(nowSec)
        if gaze.is_blinking():
            text = "Blinking"
            gazeResult[0] += 1
            # Blinking = 0
            # 글자말고 숫자로 데이터 전송 및 저장
            # 데이터 전송할 때 학생들의 이름처럼 primary key 이용해서 넘겨야될듯
            # 그리고 나중에 합쳐서 평균 구하는 방식으로
        elif gaze.is_right():
            text = "Looking right"
            gazeResult[1] += 1
            # Looking Right = 1
        elif gaze.is_left():
            text = "Looking left"
            gazeResult[2] += 1
            # Looking Left = 2
        elif gaze.is_center():
            text = "Looking center"
            gazeResult[3] += 1
            # Looking Center = 3
        cv2.putText(frame, text, (90, 60), cv2.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)
    elif preSec != nowSec and (nowSec - 1) % 3 == 0 and nowSec != 1:
        # 3초 간격이 아니면 gazeResult를 다시 초기화
        # print("check gazeResult = [", gazeResult[0], ", ", gazeResult[1], ", ", gazeResult[2], ", ", gazeResult[3], "]")
        # 값이 가장 큰 값이 있는 index 저장
        # index = 0 -> blinking | index = 1 -> right | index = 2 -> left | index = 3 -> center
        result = gazeResult.index(max(gazeResult))
        if result == 0:
            print("blinking")
            print("gazeResult = [", gazeResult[0], ", ", gazeResult[1], ", ", gazeResult[2], ", ", gazeResult[3], "]\n")
        elif result == 1:
            print("right")
            print("gazeResult = [", gazeResult[0], ", ", gazeResult[1], ", ", gazeResult[2], ", ", gazeResult[3], "]\n")
        elif result == 2:
            print("left")
            print("gazeResult = [", gazeResult[0], ", ", gazeResult[1], ", ", gazeResult[2], ", ", gazeResult[3], "]\n")
        elif result == 3:
            print("center")
            print("gazeResult = [", gazeResult[0], ", ", gazeResult[1], ", ", gazeResult[2], ", ", gazeResult[3], "]\n")
        # print(result)
        # 이 result를 DB에 저장!!
        gazeResult = [0, 0, 0, 0]

    preSec = nowSec

    left_pupil = gaze.pupil_left_coords()
    right_pupil = gaze.pupil_right_coords()
    cv2.putText(frame, "Left pupil:  " + str(left_pupil), (90, 130), cv2.FONT_HERSHEY_DUPLEX, 0.9, (147, 58, 31), 1)
    cv2.putText(frame, "Right pupil: " + str(right_pupil), (90, 165), cv2.FONT_HERSHEY_DUPLEX, 0.9, (147, 58, 31), 1)

    cv2.imshow("Demo", frame)

    if cv2.waitKey(1) == 27:
        break
   
cap.release()
cv2.destroyAllWindows()