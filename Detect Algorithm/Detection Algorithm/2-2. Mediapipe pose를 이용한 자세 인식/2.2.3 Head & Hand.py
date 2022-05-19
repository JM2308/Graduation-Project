import cv2
import mediapipe as mp


def headHandCheck(image_width, image_height, points):
    # 15 : left_wrist | 16 : right_wrist | 17 : left_pinky | 18 : right_pinky
    # 19 : left_index | 20 : right_index | 21 : left_thumb | 22 : right_thumb

    try:
        print("TRY")
        LWristX = points.landmark[mp_pose.PoseLandmark(15).value].x * image_width
        LWristY = points.landmark[mp_pose.PoseLandmark(15).value].y * image_height
        LPinkyX = points.landmark[mp_pose.PoseLandmark(17).value].x * image_width
        LPinkyY = points.landmark[mp_pose.PoseLandmark(17).value].y * image_height
        LIndexX = points.landmark[mp_pose.PoseLandmark(19).value].x * image_width
        LIndexY = points.landmark[mp_pose.PoseLandmark(19).value].y * image_height
        LThumbX = points.landmark[mp_pose.PoseLandmark(21).value].x * image_width
        LThumbY = points.landmark[mp_pose.PoseLandmark(21).value].y * image_height

        LShoulderX = points.landmark[mp_pose.PoseLandmark(11).value].x * image_width
        LShoulderY = points.landmark[mp_pose.PoseLandmark(11).value].y * image_height
        RShoulderX = points.landmark[mp_pose.PoseLandmark(12).value].x * image_width
        RShoulderY = points.landmark[mp_pose.PoseLandmark(12).value].y * image_height

        LListX = [LWristX, LPinkyX, LIndexX, LThumbX]
        LListY = [LWristY, LPinkyY, LIndexY, LThumbY]

        print(LWristX, LPinkyX, LIndexX, LThumbX)
        print(LShoulderX, RShoulderX)
        print(LWristY, LPinkyY, LIndexY, LThumbY)
        print(LShoulderY, RShoulderY)

        for x in LListX:
            if LShoulderX > x or RShoulderX < x:
                return False
            else:
                print("ELSE1")

        for y in LListY:
            if LShoulderY > y or RShoulderY > y:
                return False
            else:
                print("ELSE2")

        return True
    except:
        try:
            print("EXCEPT")
            RWristX = points.landmark[mp_pose.PoseLandmark(16).value].x * image_width
            RWristY = points.landmark[mp_pose.PoseLandmark(16).value].y * image_height
            RPinkyX = points.landmark[mp_pose.PoseLandmark(18).value].x * image_width
            RPinkyY = points.landmark[mp_pose.PoseLandmark(18).value].y * image_height
            RIndexX = points.landmark[mp_pose.PoseLandmark(20).value].x * image_width
            RIndexY = points.landmark[mp_pose.PoseLandmark(20).value].y * image_height
            RThumbX = points.landmark[mp_pose.PoseLandmark(22).value].x * image_width
            RThumbY = points.landmark[mp_pose.PoseLandmark(22).value].y * image_height

            LShoulderX = points.landmark[mp_pose.PoseLandmark(11).value].x * image_width
            LShoulderY = points.landmark[mp_pose.PoseLandmark(11).value].y * image_height
            RShoulderX = points.landmark[mp_pose.PoseLandmark(12).value].x * image_width
            RShoulderY = points.landmark[mp_pose.PoseLandmark(12).value].y * image_height

            RListX = [RWristX, RPinkyX, RIndexX, RThumbX]
            RListY = [RWristY, RPinkyY, RIndexY, RThumbY]

            print(LWristX, RWristX, LPinkyX, RPinkyX, LIndexX, RIndexX, LThumbX, RThumbX)
            print(LShoulderX, RShoulderX)
            print(LWristY, RWristY, LPinkyY, RPinkyY, LIndexY, RIndexY, LThumbY, RThumbY)
            print(LShoulderY, RShoulderY)

            for x in RListX:
                if LShoulderX > x or RShoulderX < x:
                    return False
                else:
                    print("ELSE3")

            for y in RListY:
                if LShoulderY > y or RShoulderY > y:
                    return False
                else:
                    print("ELSE4")

            return True
        except:
            print("Some Points is None")
            return False


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

            if headHandCheck(image_width, image_height, results.pose_landmarks):
                print("Head Hand")
            else:
                print("Not Head Hand")

            cv2.imshow('MediaPipe Pose', cv2.flip(image, 1))

            if cv2.waitKey(5) & 0xFF == 27:
                break


mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

# 0 : Nose | 1 : left_eye_inner | 2 : left_eye | 3 : left_eye_outer | 4 : right_eye_inner
# 5 : right_eye | 6 : right_eye_outer | 7 : left_ear | 8 : right_ear | 9 : mouth_left
# 10 : mouth_right | 11 : left_shoulder | 12 : right_shoulder | 13 : left_elbow | 14 : right_elbow
# 15 : left_wrist | 16 : right_wrist | 17 : left_pinky | 18 : right_pinky | 19 : left_index
# 20 : right_index | 21 : left_thumb | 22 : right_thumb | 23 : left_hip | 24 : right_hip
# 25 : left_knee | 26 : right_knee | 27 : left_ankle | 28 : right_ankle | 29 : left_heel
# 30 : right_heel | 31 : left_foot_index | 32.right_foot_index

# Camera
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if cap.isOpened():
    while True:
        mediaPipeCameraPose(cap)
else:
    print("can't open camera")

cap.release()
