import numpy as np
import mediapipe as mp
import dlib
import cv2


# haarcascade
cascade_filename = '../Setting File/haarcascade_frontalface_alt.xml'
cascade = cv2.CascadeClassifier(cascade_filename)

# dlib
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

index = ALL

# Mediapipe Pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

# Video Setting
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)


def main():
    if cap.isOpened():
        while True:
            faceDetector(cap, cascade)
    else:
        print("can't open camera")

    cap.release()
    cv2.destroyAllWindows()


def faceDetector(cam, cascade):
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while True:
            ret, img = cam.read()

            if ret:
                img = cv2.resize(img, dsize=(400, 300), interpolation=cv2.INTER_AREA)

                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                results = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(20, 20))

                if len(results) == 0:
                    print('The student isn\'t sitting in his/her seat.')
                elif len(results) >= 1:
                    print('The student is sitting in his/her seat.')
                    dlibCheck(img, gray)
                    poseCheck(pose, img)

                for box in results:
                    x, y, w, h = box
                    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), thickness=2)

                if cv2.waitKey(1) > 0:
                    break

            else:
                print("no frame")
                break


def dlibCheck(img, gray):
    dets = detector(gray, 1)

    for face in dets:
        shape = predictor(img, face)
        list_points = []

        for p in shape.parts():
            list_points.append([p.x, p.y])

        list_points = np.array(list_points)

        global index

        for i, pt in enumerate(list_points[index]):
            pt_pos = (pt[0], pt[1])
            cv2.circle(img, pt_pos, 2, (0, 255, 0), -1)

        cv2.rectangle(img, (face.left(), face.top()), (face.right(), face.bottom()), (0, 0, 255), 3)

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

    return 0


def poseCheck(pose, img):
    img.flags.writeable = False
    image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = pose.process(image)

    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                              landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

    cv2.imshow('Result', cv2.flip(image, 1))


if __name__ == "__main__":
    main()

