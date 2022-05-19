import dlib
import cv2 as cv
import numpy as np
import math
import queue


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

    if queueName == "TH_movingQueue":
        global TH_movingQueue
        TH_movingQueue = movingQueue
    elif queueName == "FC_movingQueue":
        global FC_movingQueue
        FC_movingQueue = movingQueue

    return movingAverage


def headCheck(X1, Y1, X2, Y2):
    global angle

    theta = np.arctan((X2 - X1) / (Y2 - Y1))
    angle = theta * 180 / math.pi
    angle = abs(angle)
    print('AngleResult = ' + str(angle))

    newMovingAverage = queueUpdate(TH_movingQueue, angle)
    # print("Average = ", newMovingAverage)

    global TH_preMovingAverage

    if TH_movingQueue.qsize() == 0:
        TH_preMovingAverage = newMovingAverage

    if angle >= TH_threshold:
        # 계산한 각도가 threshold 보다 클 때
        print("Tilted Head")

    if newMovingAverage >= TH_threshold:
        # average 가  threshold 보다 클 때
        if TH_preMovingAverage - (TH_threshold / 10) <= newMovingAverage:
            # 급격하게 고개 각도가 줄어들 때 (고개갸웃 -> 원래대로 돌아올때)를 확인
            print("Tilted Head")

    if TH_movingQueue.qsize() == 10:
        if TH_preMovingAverage + (TH_threshold / 10) <= newMovingAverage:
            # 급격하게 고개 각도가 커질 때 (기존 -> 고개 갸웃거릴 때)를 확인
            print("Tilted Head")

    TH_preMovingAverage = newMovingAverage

    return True


def calculateLength(LEyeEdgeX, LEyeEdgeY, REyeEdgeX, REyeEdgeY):
    eyeEdgeLength = round(math.pow(math.pow((LEyeEdgeX - REyeEdgeX), 2) + math.pow((LEyeEdgeY - REyeEdgeY), 2), 1/2))
    return eyeEdgeLength


def faceCloserCheck(list_points):
    LEyeEdgeX = list_points[36][0]
    LEyeEdgeY = list_points[36][1]
    REyeEdgeX = list_points[45][0]
    REyeEdgeY = list_points[45][1]

    faceLength = calculateLength(LEyeEdgeX, LEyeEdgeY, REyeEdgeX, REyeEdgeY)
    # print("faceLength = ", faceLength)

    newMovingAverage = queueUpdate(FC_movingQueue, faceLength)
    # print("Average = ", newMovingAverage)

    global FC_preMovingAverage
    global FC_threshold

    if FC_preMovingAverage == 0:
        FC_preMovingAverage = newMovingAverage
    elif FC_preMovingAverage + FC_threshold <= newMovingAverage:
        print("Face Closer")

    return True


detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('Setting File/shape_predictor_68_face_landmarks.dat')

cap = cv.VideoCapture(0)

ALL = list(range(0, 68))
RIGHT_EYEBROW = list(range(17, 22))
LEFT_EYEBROW = list(range(22, 27))
RIGHT_EYE = list(range(36, 42))
LEFT_EYE = list(range(42, 48))
NOSE = list(range(27, 36))
MOUTH_OUTLINE = list(range(48, 61))
MOUTH_INNER = list(range(61, 68))
JAWLINE = list(range(0, 17))

UsingLandmark = list(range(27, 28)) + list(range(30, 31))

index = UsingLandmark

TH_movingQueue = queue.Queue()
FC_movingQueue = queue.Queue()

TH_preMovingAverage = 0
FC_preMovingAverage = 0

TH_threshold = 25
FC_threshold = 20

while True:
    ret, img_frame = cap.read()
    img_gray = cv.cvtColor(img_frame, cv.COLOR_BGR2GRAY)
    dets = detector(img_gray, 1)

    for face in dets:
        shape = predictor(img_frame, face)
        list_points = []

        for p in shape.parts():
            list_points.append([p.x, p.y])

        list_points = np.array(list_points)

        LEyeEdge = list_points[36]
        REyeEdge = list_points[45]

        for i, pt in enumerate(list_points[index]):
            pt_pos = (pt[0], pt[1])
            cv.circle(img_frame, pt_pos, 2, (0, 255, 0), -1)

        cv.rectangle(img_frame, (face.left(), face.top()), (face.right(), face.bottom()), (0, 0, 255), 3)

        headCheck(list_points[27][0], list_points[27][1], list_points[30][0], list_points[30][1])
        faceCloserCheck(list_points)
        cv.imshow('result', img_frame)

        key = cv.waitKey(1)

        if key == 27:
            break
        elif key == ord('1'):
            index = ALL
        elif key == ord('2'):
            index = LEFT_EYEBROW + RIGHT_EYEBROW
        elif key == ord('3'):
            index = LEFT_EYE + RIGHT_EYE
        elif key == ord('4'):
            index = NOSE
        elif key == ord('5'):
            index = MOUTH_OUTLINE + MOUTH_INNER
        elif key == ord('6'):
            index = JAWLINE

cap.release()
