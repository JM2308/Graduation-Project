import cv2
from gaze_tracking import GazeTracking

gaze = GazeTracking()
webcam = cv2.VideoCapture(0)
# webcam = cv2.VideoCapture("../Test Image/sample2.mp4")


while True:
    _, frame = webcam.read()
    gaze.refresh(frame)

    new_frame = gaze.annotated_frame()
    text = ""

    if gaze.is_right():
        text = "Looking right"
    elif gaze.is_left():
        text = "Looking left"
    elif gaze.is_center():
        text = "Looking center"

    cv2.putText(new_frame, text, (60, 60), cv2.FONT_HERSHEY_DUPLEX, 2, (255, 0, 0), 2)
    cv2.imshow("Demo", new_frame)

    if cv2.waitKey(1) == 27:
        break


"""
   * 알고리즘 구성 *
____________________
1-1) 왼쪽
    1-2) 왼쪽 & 센터
        1-3) 왼쪽
    1-2) 오른쪽
        1-3) X
____________________
2-1) 센터
    2-2) 왼쪽
        2-3) 왼쪽
    2-2) 센터
        2-3) 센터
    2-2) 오른쪽
        2-3) 오른쪽
____________________
3-1) 오른쪽
    3-2) 왼쪽
        3-3) X
    3-2) 센터 & 오른쪽
        3-3) 오른쪽
____________________

3초 간격으로 Frame 측정
 (1) Moving Left
 (2) Moving Center
 (3) Moving Right
  + Keep
"""