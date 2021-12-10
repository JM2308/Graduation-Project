import cv2
import mediapipe as mp
import math
import dlib
import numpy as np


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
    # 0 : Nose | 1 : left_eye_inner | 2 : left_eye | 3 : left_eye_outer | 4 : right_eye_inner
    # 5 : right_eye | 6 : right_eye_outer | 7 : left_ear | 8 : right_ear | 9 : mouth_left
    # 10 : mouth_right | 11 : left_shoulder | 12 : right_shoulder | 13 : left_elbow | 14 : right_elbow
    # 15 : left_wrist | 16 : right_wrist | 17 : left_pinky | 18 : right_pinky | 19 : left_index
    # 20 : right_index | 21 : left_thumb | 22 : right_thumb | 23 : left_hip | 24 : right_hip
    # 25 : left_knee | 26 : right_knee | 27 : left_ankle | 28 : right_ankle | 29 : left_heel
    # 30 : right_heel | 31 : left_foot_index | 32.right_foot_index

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
        print('AngleResult = 0')
        print('Not Tilted Head')
        return -1

    lineResult2 = findLineFunction(RShoulderX, RShoulderY, LShoulderX, LShoulderY)  # Line2

    m1 = lineResult1[0]
    m2 = lineResult2[0]

    angle = round(findAngle(m1, m2))
    print('AngleResult = ' + str(angle))

    if angle <= 80:
        print('Tilted Head')
        return -1
    else:
        print('Not Tilted Head')
        return 0


def faceCloserCheck(image_width, image_height, points):
    LEarX = points.landmark[mp_pose.PoseLandmark(9).value].x * image_width
    LEarY = points.landmark[mp_pose.PoseLandmark(9).value].y * image_height
    REarX = points.landmark[mp_pose.PoseLandmark(10).value].x * image_width
    REarY = points.landmark[mp_pose.PoseLandmark(10).value].y * image_height

    faceLength = calculateLength(LEarX, LEarY, REarX, REarY)
    print(faceLength)

    global preFaceLength

    if faceLength != 0:
        if faceLength > (preFaceLength + 3):  # 조건 넣어주기
            # print(faceLength)
            # 길이 길어졌다가 다시 짧아졌을 때도 구분해줘야 함
            # 이해 O -> 이해 X -> 이해 O
            preFaceLength = faceLength
            return True
        else:
            preFaceLength = faceLength
            return False
    else:
        preFaceLength = faceLength
        # print(faceLength)
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


# Camera
def mediaPipeCameraPose(image, pose):
    # with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                  landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

        image_height, image_width, _ = image.shape

        cv2.imshow('Result', cv2.flip(image, 1))

        return results.pose_landmarks


def dlibCheck(image, gray):
    ret = detector(gray, 1)
    print("2")

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


def videoDetector(cam):
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:

        while True:
            ret, img = cam.read()

            img = cv2.resize(img, dsize=None, fx=1.0, fy=1.0)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            results = cascade.detectMultiScale(gray,  # 입력 이미지
                                               scaleFactor=1.1,  # 이미지 피라미드 스케일 factor
                                               minNeighbors=5,  # 인접 객체 최소 거리 픽셀
                                               minSize=(20, 20)  # 탐지 객체 최소 크기
                                               )

            image_height, image_width, _ = img.shape

            if len(results) == 0:
                print('The student isn\'t sitting in his/her seat.')
            elif len(results) >= 1:
                print('The student is sitting in his/her seat.')
                pose_landmark = mediaPipeCameraPose(img, pose)
                list_point = dlibCheck(img, gray)

                tiltedHeadCheck(image_width, image_height, pose_landmark)

                if faceCloserCheck(image_width, image_height, pose_landmark):
                    print("Face Closer")
                else:
                    print("Face isn't Closer")

                frownGlabellaCheck(list_point)

            if cv2.waitKey(1) > 0:
                break


cascade_filename = '../Setting File/haarcascade_frontalface_alt.xml'
cascade = cv2.CascadeClassifier(cascade_filename)

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('../Setting File/shape_predictor_68_face_landmarks.dat')

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

# Camera
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if cap.isOpened():
    while True:
        videoDetector(cap)
else:
    print("can't open camera")
