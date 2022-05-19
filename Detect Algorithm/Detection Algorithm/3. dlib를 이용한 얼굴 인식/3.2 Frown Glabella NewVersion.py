import dlib
import cv2
import numpy as np
import math
import queue


def findLineFunction(x1, y1, x2, y2):
    if x2 != x1:
        m = (y2 - y1) / (x2 - x1)  # 기울기 m 계산
        n = y1 - (m * x1)  # y 절편 계산

        if n > 0:
            result = [m, abs(n)]
        elif n < 0:
            result = [m, -abs(n)]
        else:  # n == 0이면
            result = [m, 0]

        return result
    else:  # x 값이 변하지 않는 경우 (x = a 형태의 그래프)
        return False


def findAngle(m1, m2):
    tanX = abs((m1 - m2) / (1 + m1 * m2))
    Angle = math.atan(tanX) * 180 / math.pi
    return Angle


def queueUpdate(angle):
    global movingQueue

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
    return movingAverage


def frownGlabellaCheck(list_points):
    LEyebrowX = list_points[21][0]
    LEyebrowY = list_points[21][1]
    REyebrowX = list_points[22][0]
    REyebrowY = list_points[22][1]
    NoseX = list_points[27][0]
    NoseY = list_points[27][1]

    lineResult1 = findLineFunction(NoseX, NoseY, LEyebrowX, LEyebrowY)  # Line1
    lineResult2 = findLineFunction(NoseX, NoseY, REyebrowX, REyebrowY)  # Line2

    m1 = lineResult1[0]
    m2 = lineResult2[0]

    angle = findAngle(m1, m2) * 5
    angle = round(angle)
    print('angle = ' + str(angle))
    # print('AngleResult = ' + str(angle))
    # print("angle = " + angle)
    newAngleMovingAverage = queueUpdate(angle)
    newAngleMovingAverage = round(newAngleMovingAverage)
    print("newAngleMA = " + str(newAngleMovingAverage))
    # print("newAngleMA = ", + round(newAngleMovingAverage))

    global preAngleMovingAverage
    global threshold
    global frownFlag

    if preAngleMovingAverage == 0:
        preAngleMovingAverage = newAngleMovingAverage
    else:
        if frownFlag == 0:
            if angle + threshold <= preAngleMovingAverage:
                frownFlag = 1
                print('Frown Glabella1')
                print(frownFlag)
                return True
        else:
            if preAngleMovingAverage + (threshold / 5) <= angle:
                frownFlag = 0
                print(frownFlag)
            # else:
                # print('Frown Glabella2')
            return True

    """
    elif preAngleMovingAverage + angleThreshold <= newAngleMovingAverage:
        print("Frown Glabella")
    elif preLengthMovingAverage + lengthThreshold <= newLengthMovingAverage
        print("Frown Glabella")

    return True
    """

    """
    global initialAngle
    global initialGlabellaLength

    if initialAngle == 0 and initialGlabellaLength == 0:
        initialAngle = angle
        initialGlabellaLength = glabellaLength
    else:
        if glabellaLength < initialGlabellaLength and angle < initialAngle:
            print('Frown Glabella')
            return -1
        else:
            print('Not Frown Glabella')
            return 0
    """


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

GLABELLA = list(range(21, 23)) + list(range(27, 28))

index = GLABELLA

initialGlabellaLength = 0
initialAngle = 0

movingQueue = queue.Queue()
preAngleMovingAverage = 0
threshold = 5

frownFlag = 0

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

        LEyebrow = list_points[21]
        REyebrow = list_points[22]
        Nose = list_points[27]

        for i, pt in enumerate(list_points[index]):
            pt_pos = (pt[0], pt[1])
            cv2.circle(img_frame, pt_pos, 2, (0, 255, 0), -1)

        cv2.rectangle(img_frame, (face.left(), face.top()), (face.right(), face.bottom()), (0, 0, 255), 3)

        frownGlabellaCheck(list_points)
        cv2.imshow('result', cv2.flip(img_frame, 1))

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
