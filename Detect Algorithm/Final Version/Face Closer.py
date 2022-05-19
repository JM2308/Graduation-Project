import dlib
import cv2
import numpy as np
import math
import queue


def calculateLength(LEyeEdgeX, LEyeEdgeY, REyeEdgeX, REyeEdgeY):
    eyeEdgeLength = round(math.pow(math.pow((LEyeEdgeX - REyeEdgeX), 2) + math.pow((LEyeEdgeY - REyeEdgeY), 2), 1/2))
    return eyeEdgeLength


def queueUpdate(faceLength):
    global movingQueue

    if movingQueue.qsize() == 10:
        movingQueue.get()
        movingQueue.put(faceLength)
    elif movingQueue.qsize() < 10:
        movingQueue.put(faceLength)

    sum = 0

    for index in range(0, movingQueue.qsize()):
        data = movingQueue.get()
        sum += data
        # print("data = ", data)
        # print("sum = ", sum)
        movingQueue.put(data)

    movingAverage = sum / movingQueue.qsize()
    return movingAverage


def faceCloserCheck(list_points):
    LEyeEdgeX = list_points[36][0]
    LEyeEdgeY = list_points[36][1]
    REyeEdgeX = list_points[45][0]
    REyeEdgeY = list_points[45][1]

    faceLength = calculateLength(LEyeEdgeX, LEyeEdgeY, REyeEdgeX, REyeEdgeY)
    # print("faceLength = ", faceLength)

    newMovingAverage = queueUpdate(faceLength)
    # print("Average = ", newMovingAverage)

    global preMovingAverage
    global threshold

    if preMovingAverage == 0:
        preMovingAverage = newMovingAverage
    elif preMovingAverage + threshold <= newMovingAverage:
        print("Face Closer")

    return True


detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('../Setting File/shape_predictor_68_face_landmarks.dat')

cap = cv2.VideoCapture(0)

ALL = list(range(0, 68))
RIGHT_EYEBROW = list(range(17, 22))
LEFT_EYEBROW = list(range(22, 27))
RIGHT_EYE = list(range(36, 42))
LEFT_EYE = list(range(42, 48))
NOSE = list(range(27, 36))
MOUTH_OUTLINE = list(range(48, 61))
MOUTH_INNER = list(range(61, 68))
JAWLINE = list(range(0, 17))

EYE = list(range(36, 37)) + list(range(45, 46))

index = EYE

movingQueue = queue.Queue()
preMovingAverage = 0
threshold = 20

while True:
    ret, img_frame = cap.read()
    img_gray = cv2.cvtColor(img_frame, cv2.COLOR_BGR2GRAY)
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
            cv2.circle(img_frame, pt_pos, 2, (0, 255, 0), -1)

        cv2.rectangle(img_frame, (face.left(), face.top()), (face.right(), face.bottom()), (0, 0, 255), 3)

        faceCloserCheck(list_points)
        cv2.imshow('result', img_frame)

        key = cv2.waitKey(1)

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
