import cv2
import mediapipe as mp
import math
import dlib
import numpy as np
import time
import pyscreenshot as ImageGrab
from tkinter import *
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db


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


def calculateLength(X1, Y1, X2, Y2):
    length = round(math.pow(math.pow((X1 - X2), 2) + math.pow((Y1 - Y2), 2), 1 / 2))
    return length


def tiltedHeadCheck(image_width, image_height, points):
    NoseX = points.landmark[mp_pose.PoseLandmark(0).value].x * image_width
    NoseY = points.landmark[mp_pose.PoseLandmark(0).value].y * image_height
    LMouthX = points.landmark[mp_pose.PoseLandmark(9).value].x * image_width
    LMouthY = points.landmark[mp_pose.PoseLandmark(9).value].y * image_height
    RMouthX = points.landmark[mp_pose.PoseLandmark(10).value].x * image_width
    RMouthY = points.landmark[mp_pose.PoseLandmark(10).value].y * image_height
    LShoulderX = points.landmark[mp_pose.PoseLandmark(11).value].x * image_width
    LShoulderY = points.landmark[mp_pose.PoseLandmark(11).value].y * image_height
    RShoulderX = points.landmark[mp_pose.PoseLandmark(12).value].x * image_width
    RShoulderY = points.landmark[mp_pose.PoseLandmark(12).value].y * image_height

    MMouthX = (LMouthX + RMouthX) / 2
    MMouthY = (LMouthY + RMouthY) / 2

    lineResult1 = findLineFunction(NoseX, NoseY, MMouthX, MMouthY)  # Line1

    if not lineResult1:
        print('Not Tilted Head')
        return 0

    lineResult2 = findLineFunction(RShoulderX, RShoulderY, LShoulderX, LShoulderY)  # Line2

    m1 = lineResult1[0]
    m2 = lineResult2[0]

    angle = round(findAngle(m1, m2))

    if angle <= 80:
        print('Tilted Head')
        return 1
    else:
        print('Not Tilted Head')
        return 0


def faceCloserCheck(image_width, image_height, points):
    LEarX = points.landmark[mp_pose.PoseLandmark(7).value].x * image_width
    LEarY = points.landmark[mp_pose.PoseLandmark(7).value].y * image_height
    REarX = points.landmark[mp_pose.PoseLandmark(8).value].x * image_width
    REarY = points.landmark[mp_pose.PoseLandmark(8).value].y * image_height

    faceLength = calculateLength(LEarX, LEarY, REarX, REarY)

    global preFaceLength

    if preFaceLength != 0:
        if faceLength > (preFaceLength + 3):
            preFaceLength = faceLength
            return True
        else:
            preFaceLength = faceLength
            return False
    else:
        preFaceLength = faceLength
        return False


def frownGlabellaCheck(list_points):
    # 좌표 계산
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

    angle = findAngle(m1, m2)

    glabellaLength = calculateLength(LEyebrowX, LEyebrowY, REyebrowX, REyebrowY)

    global initialAngle
    global initialGlabellaLength

    if initialAngle == 0 and initialGlabellaLength == 0:
        initialAngle = angle
        initialGlabellaLength = glabellaLength
    else:
        if glabellaLength < initialGlabellaLength and angle < initialAngle:
            ####################################################
            # 미간을 찌푸릴 때
            print('Frown Glabella')
            return -1
            ####################################################
        else:
            ####################################################
            # 미간을 찌푸리지 않을 때
            print('Not Frown Glabella')
            return 0
            ####################################################


# Camera
def mediaPipeCameraPose(image, pose):
    image.flags.writeable = False
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(image)

    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                              landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

    image_height, image_width, _ = image.shape

    return results.pose_landmarks


def dlibCheck(image, gray):
    ret = detector(gray, 1)

    for face in ret:
        shape = predictor(image, face)
        list_points = []

        for p in shape.parts():
            list_points.append([p.x, p.y])

        list_points = np.array(list_points)

        global index

        for i, pt in enumerate(list_points[index]):
            pt_pos = (pt[0], pt[1])
            cv2.circle(image, pt_pos, 2, (0, 255, 0), -1)

        cv2.rectangle(image, (face.left(), face.top()), (face.right(), face.bottom()), (0, 0, 255), 3)

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

        return list_points


def algorithmCheck():
    dir=db.reference('minsu')

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while True:
            print('------------------------------------------')
            time.sleep(3)
            im = ImageGrab.grab(bbox=(45, 320, 610, 740))
            im.save('part.png')
            imageName = "part.png"
            img = cv2.imread(imageName)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            results = cascade.detectMultiScale(gray,  # 입력 이미지
                                               scaleFactor=1.1,  # 이미지 피라미드 스케일 factor
                                               minNeighbors=5,  # 인접 객체 최소 거리 픽셀
                                               minSize=(20, 20)  # 탐지 객체 최소 크기
                                               )

            image_height, image_width, _ = img.shape

            if len(results) == 0:
                ####################################################
                # 자리에 없을 때
                print('The student isn\'t sitting in his/her seat.')
                dir.update({'in_seat': 0})
                ####################################################
            elif len(results) >= 1:
                ####################################################
                # 자리에 있을 때
                print('The student is sitting in his/her seat.')
                dir.update({'in_seat': 1})
                ####################################################
                pose_landmark = mediaPipeCameraPose(img, pose)
                # list_point = dlibCheck(img, gray)

                # 고개 갸웃거리는 부분 체크
                if(tiltedHeadCheck(image_width, image_height, pose_landmark)==0):
                    # 고개를 갸웃거리지 않음
                    dir.update({'tilted':0})
                else:
                    # 고개를 갸웃거림
                    dir.update({'tilted':1})

                # 얼굴 가까이하는 부분 체크
                if faceCloserCheck(image_width, image_height, pose_landmark):
                ####################################################
                    # 얼굴 가까이 했을 때
                    print("Face Closer")
                    dir.update({'face_closer':1})
                ####################################################
                else:
                ####################################################
                    # 얼굴 가까이하지 않았을 때
                    print("Face isn't Closer")
                    dir.update({'face_closer':0})
                ####################################################

                # 미간 찌푸리는 부분 체크
                # frownGlabellaCheck(list_point)
                print('--------------------------------------------')


# firebase
cred = credentials.Certificate('C:/Users/leeminsu/Desktop/uume-58fe8-firebase-adminsdk-ed1pa-c645bc55b1.json')
firebase_admin.initialize_app(cred,{
    'databaseURL':'https://uume-58fe8-default-rtdb.firebaseio.com/'
})
# -----------------------algorithm----------------------------
cascade_filename = 'Setting File/haarcascade_frontalface_alt.xml'
cascade = cv2.CascadeClassifier(cascade_filename)

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('Setting File/shape_predictor_68_face_landmarks.dat')

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

# Initial Setting
preFaceLength = 0
imageNum = 0

time.sleep(5)
algorithmCheck()
