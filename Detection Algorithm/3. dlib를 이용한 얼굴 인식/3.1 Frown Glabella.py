import dlib
import cv2 as cv
import numpy as np
import math


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


def calculateLength(LEyebrowX, LEyebrowY, REyebrowX, REyebrowY):
    glabellaLength = round(math.pow(math.pow((LEyebrowX - REyebrowX), 2) + math.pow((LEyebrowY - REyebrowY), 2), 1/2))
    return glabellaLength


def frownGlabellaCheck(list_points):
    LEyebrowX = list_points[21][0]
    LEyebrowY = list_points[21][1]
    REyebrowX = list_points[22][0]
    REyebrowY = list_points[22][1]
    NoseX = list_points[27][0]
    NoseY = list_points[27][1]

    lineResult1 = findLineFunction(NoseX, NoseY, LEyebrowX, LEyebrowY) # Line1
    lineResult2 = findLineFunction(NoseX, NoseY, REyebrowX, REyebrowY) # Line2

    m1 = lineResult1[0]
    m2 = lineResult2[0]

    angle = findAngle(m1, m2)
    print('AngleResult = ' + str(angle))

    glabellaLength = calculateLength(LEyebrowX, LEyebrowY, REyebrowX, REyebrowY)
    print('GlabellaLengthResult = ' + str(glabellaLength))

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


detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('../Setting File/shape_predictor_68_face_landmarks.dat')

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

GLABELLA = list(range(21, 23)) + list(range(27, 28))

index = GLABELLA

initialGlabellaLength = 0
initialAngle = 0

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

        LEyebrow = list_points[21]
        REyebrow = list_points[22]
        Nose = list_points[27]

        for i, pt in enumerate(list_points[index]):
            pt_pos = (pt[0], pt[1])
            cv.circle(img_frame, pt_pos, 2, (0, 255, 0), -1)

        cv.rectangle(img_frame, (face.left(), face.top()), (face.right(), face.bottom()), (0, 0, 255), 3)

        cv.imshow('result', cv.flip(img_frame, 1))

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

        frownGlabellaCheck(list_points)

cap.release()

