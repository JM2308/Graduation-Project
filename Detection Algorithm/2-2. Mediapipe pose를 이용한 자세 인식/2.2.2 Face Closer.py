import cv2
import mediapipe as mp
import math


def calculateLength(LEarX, LEarY, REarX, REarY):
    faceLength = round(math.pow(math.pow((LEarX - REarX), 2) + math.pow((LEarY - REarY), 2), 1/2))
    return faceLength


def faceCloserCheck(image_width, image_height, points):
    LEarX = points.landmark[mp_pose.PoseLandmark(7).value].x * image_width
    LEarY = points.landmark[mp_pose.PoseLandmark(7).value].y * image_height
    REarX = points.landmark[mp_pose.PoseLandmark(8).value].x * image_width
    REarY = points.landmark[mp_pose.PoseLandmark(8).value].y * image_height

    faceLength = calculateLength(LEarX, LEarY, REarX, REarY)

    global preFaceLength

    if preFaceLength != 0:
        if faceLength > (preFaceLength + 3):  # 조건 넣어주기
            preFaceLength = faceLength
            return True
        else:
            preFaceLength = faceLength
            return False
    else:
        preFaceLength = faceLength
        return False


def mediaPipeCameraPose(cap):
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        success, image = cap.read()

        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                  landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

        image_height, image_width, _ = image.shape

        if faceCloserCheck(image_width, image_height, results.pose_landmarks):
            print("Face Closer")
        else:
            print("Face isn't Closer")

        cv2.imshow('MediaPipe Pose', cv2.flip(image, 1))

        if cv2.waitKey(5) & 0xFF == 27:
            return False


# 0 : Nose | 1 : left_eye_inner | 2 : left_eye | 3 : left_eye_outer | 4 : right_eye_inner
# 5 : right_eye | 6 : right_eye_outer | 7 : left_ear | 8 : right_ear | 9 : mouth_left
# 10 : mouth_right | 11 : left_shoulder | 12 : right_shoulder | 13 : left_elbow | 14 : right_elbow
# 15 : left_wrist | 16 : right_wrist | 17 : left_pinky | 18 : right_pinky | 19 : left_index
# 20 : right_index | 21 : left_thumb | 22 : right_thumb | 23 : left_hip | 24 : right_hip
# 25 : left_knee | 26 : right_knee | 27 : left_ankle | 28 : right_ankle | 29 : left_heel
# 30 : right_heel | 31 : left_foot_index | 32.right_foot_index

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

preFaceLength = 0

if cap.isOpened():
    while True:
        if not mediaPipeCameraPose(cap):
            break
else:
    print("can't open camera")

cap.release()
