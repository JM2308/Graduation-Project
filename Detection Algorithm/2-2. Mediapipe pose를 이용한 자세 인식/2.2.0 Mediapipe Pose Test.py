import cv2
import mediapipe as mp
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


def headCheck(image_width, image_height, points):
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

    if lineResult1 == False:
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


# Camera
def mediaPipeCameraPose(cap):
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:

        while True:
            success, image = cap.read()

            if not success:
              print("Ignoring empty camera frame.")
              continue

            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = pose.process(image)

            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

            image_height, image_width, _ = image.shape
            headCheck(image_width, image_height, results.pose_landmarks)

            cv2.imshow('MediaPipe Pose', cv2.flip(image, 1))

            if cv2.waitKey(5) & 0xFF == 27:
              break


# Image
def mediaPipeImagePose():
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        image = cv2.imread('../Test Image/face2.png')
        image = cv2.resize(image, dsize=(400, 300), interpolation=cv2.INTER_AREA)

        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                  landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())


        image_height, image_width, _ = image.shape

        headCheck(image_width, image_height, results.pose_landmarks)

        # cv2.imshow('MediaPipe Pose', image)
        # cv2.waitKey(0)


mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

# Camera
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if cap.isOpened():
    while True:
        mediaPipeCameraPose(cap)
else:
    print("can't open camera")

cap.release()

# Image
# mediaPipeImagePose()
