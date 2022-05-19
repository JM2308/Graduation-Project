import cv2
import numpy as np
import math
import tensorflow as tf
import mediapipe as mp


def get_landmark_model(saved_model='models/pose_model'):
    """
    Get the facial landmark model.
    Original repository: https://github.com/yinguobing/cnn-facial-landmark

    Parameters
    ----------
    saved_model : string, optional
        Path to facial landmarks model. The default is 'models/pose_model'.

    Returns
    -------
    model : Tensorflow model
        Facial landmarks model

    """
    model = tf.saved_model.load(saved_model)
    return model


def get_square_box(box):
    """Get a square box out of the given box, by expanding it."""
    left_x = box[0]
    top_y = box[1]
    right_x = box[2]
    bottom_y = box[3]

    box_width = right_x - left_x
    box_height = bottom_y - top_y

    # Check if box is already a square. If not, make it a square.
    diff = box_height - box_width
    delta = int(abs(diff) / 2)

    if diff == 0:  # Already a square.
        return box
    elif diff > 0:  # Height > width, a slim box.
        left_x -= delta
        right_x += delta
        if diff % 2 == 1:
            right_x += 1
    else:  # Width > height, a short box.
        top_y -= delta
        bottom_y += delta
        if diff % 2 == 1:
            bottom_y += 1

    # Make sure box is always square.
    assert ((right_x - left_x) == (bottom_y - top_y)), 'Box is not square.'

    return [left_x, top_y, right_x, bottom_y]


def move_box(box, offset):
    """Move the box to direction specified by vector offset"""
    left_x = box[0] + offset[0]
    top_y = box[1] + offset[1]
    right_x = box[2] + offset[0]
    bottom_y = box[3] + offset[1]
    return [left_x, top_y, right_x, bottom_y]


def detect_marks(img, model, face):
    """
    Find the facial landmarks in an image from the faces

    Parameters
    ----------
    img : np.uint8
        The image in which landmarks are to be found
    model : Tensorflow model
        Loaded facial landmark model
    face : list
        Face coordinates (x, y, x1, y1) in which the landmarks are to be found

    Returns
    -------
    marks : numpy array
        facial landmark points

    """

    offset_y = int(abs((face[3] - face[1]) * 0.1))
    box_moved = move_box(face, [0, offset_y])
    facebox = get_square_box(box_moved)

    h, w = img.shape[:2]
    if facebox[0] < 0:
        facebox[0] = 0
    if facebox[1] < 0:
        facebox[1] = 0
    if facebox[2] > w:
        facebox[2] = w
    if facebox[3] > h:
        facebox[3] = h

    face_img = img[facebox[1]: facebox[3], facebox[0]: facebox[2]]
    face_img = cv2.resize(face_img, (128, 128))
    face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)

    # # Actual detection.
    predictions = model.signatures["predict"](tf.constant([face_img], dtype=tf.uint8))

    # Convert predictions to landmarks.
    marks = np.array(predictions['output']).flatten()[:136]
    marks = np.reshape(marks, (-1, 2))

    marks *= (facebox[2] - facebox[0])
    marks[:, 0] += facebox[0]
    marks[:, 1] += facebox[1]
    marks = marks.astype(np.uint)

    return marks


def draw_marks(image, marks, color=(0, 255, 0)):
    """
    Draw the facial landmarks on an image

    Parameters
    ----------
    image : np.uint8
        Image on which landmarks are to be drawn.
    marks : list or numpy array
        Facial landmark points
    color : tuple, optional
        Color to which landmarks are to be drawn with. The default is (0, 255, 0).

    Returns
    -------
    None.

    """
    for mark in marks:
        cv2.circle(image, (mark[0], mark[1]), 2, color, -1, cv2.LINE_AA)


def get_face_detector(modelFile=None, configFile=None, quantized=False):
    """
    Get the face detection caffe model of OpenCV's DNN module

    Parameters
    ----------
    modelFile : string, optional
        Path to model file. The default is "models/res10_300x300_ssd_iter_140000.caffemodel" or models/opencv_face_detector_uint8.pb" based on quantization.
    configFile : string, optional
        Path to config file. The default is "models/deploy.prototxt" or "models/opencv_face_detector.pbtxt" based on quantization.
    quantization: bool, optional
        Determines whether to use quantized tf model or unquantized caffe model. The default is False.

    Returns
    -------
    model : dnn_Net

    """
    if quantized:
        if modelFile is None:
            modelFile = "models/opencv_face_detector_uint8.pb"
        if configFile is None:
            configFile = "models/opencv_face_detector.pbtxt"
        model = cv2.dnn.readNetFromTensorflow(modelFile, configFile)

    else:
        if modelFile is None:
            modelFile = "models/res10_300x300_ssd_iter_140000.caffemodel"
        if configFile is None:
            configFile = "models/deploy.prototxt"
        model = cv2.dnn.readNetFromCaffe(configFile, modelFile)
    return model


def find_faces(img, model):
    """
    Find the faces in an image

    Parameters
    ----------
    img : np.uint8
        Image to find faces from
    model : dnn_Net
        Face detection model

    Returns
    -------
    faces : list
        List of coordinates of the faces detected in the image

    """
    h, w = img.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
    model.setInput(blob)
    res = model.forward()
    faces = []

    for i in range(res.shape[2]):
        confidence = res[0, 0, i, 2]
        if confidence > 0.5:
            box = res[0, 0, i, 3:7] * np.array([w, h, w, h])
            (x, y, x1, y1) = box.astype("int")
            faces.append([x, y, x1, y1])
    return faces


def draw_faces(img, faces):
    """
    Draw faces on image

    Parameters
    ----------
    img : np.uint8
        Image to draw faces on
    faces : List of face coordinates
        Coordinates of faces to draw

    Returns
    -------
    None.

    """
    for x, y, x1, y1 in faces:
        cv2.rectangle(img, (x, y), (x1, y1), (0, 0, 255), 3)


def get_2d_points(img, rotation_vector, translation_vector, camera_matrix, val):
    point_3d = []
    dist_coeffs = np.zeros((4, 1))
    rear_size = val[0]
    rear_depth = val[1]
    point_3d.append((-rear_size, -rear_size, rear_depth))
    point_3d.append((-rear_size, rear_size, rear_depth))
    point_3d.append((rear_size, rear_size, rear_depth))
    point_3d.append((rear_size, -rear_size, rear_depth))
    point_3d.append((-rear_size, -rear_size, rear_depth))

    front_size = val[2]
    front_depth = val[3]
    point_3d.append((-front_size, -front_size, front_depth))
    point_3d.append((-front_size, front_size, front_depth))
    point_3d.append((front_size, front_size, front_depth))
    point_3d.append((front_size, -front_size, front_depth))
    point_3d.append((-front_size, -front_size, front_depth))
    point_3d = np.array(point_3d, dtype=np.float).reshape(-1, 3)

    # Map to 2d img points
    (point_2d, _) = cv2.projectPoints(point_3d, rotation_vector, translation_vector, camera_matrix, dist_coeffs)
    point_2d = np.int32(point_2d.reshape(-1, 2))
    return point_2d


def draw_annotation_box(img, rotation_vector, translation_vector, camera_matrix,
                        rear_size=300, rear_depth=0, front_size=500, front_depth=400, color=(255, 255, 0),
                        line_width=2):
    rear_size = 1
    rear_depth = 0
    front_size = img.shape[1]
    front_depth = front_size * 2
    val = [rear_size, rear_depth, front_size, front_depth]
    point_2d = get_2d_points(img, rotation_vector, translation_vector, camera_matrix, val)

    # # Draw all the lines
    cv2.polylines(img, [point_2d], True, color, line_width, cv2.LINE_AA)
    cv2.line(img, tuple(point_2d[1]), tuple(
        point_2d[6]), color, line_width, cv2.LINE_AA)
    cv2.line(img, tuple(point_2d[2]), tuple(
        point_2d[7]), color, line_width, cv2.LINE_AA)
    cv2.line(img, tuple(point_2d[3]), tuple(
        point_2d[8]), color, line_width, cv2.LINE_AA)


def head_pose_points(img, rotation_vector, translation_vector, camera_matrix):
    rear_size = 1
    rear_depth = 0
    front_size = img.shape[1]
    front_depth = front_size * 2
    val = [rear_size, rear_depth, front_size, front_depth]
    point_2d = get_2d_points(img, rotation_vector, translation_vector, camera_matrix, val)
    y = (point_2d[5] + point_2d[8]) // 2
    x = point_2d[2]

    return (x, y)


def head_pose_estimation(cap):
    ret, img = cap.read()
    faces = find_faces(img, face_model)

    for face in faces:
        marks = detect_marks(img, landmark_model, face)
        # mark_detector.draw_marks(img, marks, color=(0, 255, 0))
        image_points = np.array([
            marks[30],  # Nose tip
            marks[8],  # Chin
            marks[36],  # Left eye left corner
            marks[45],  # Right eye right corne
            marks[48],  # Left Mouth corner
            marks[54]  # Right mouth corner
        ], dtype="double")
        dist_coeffs = np.zeros((4, 1))  # Assuming no lens distortion
        (success, rotation_vector, translation_vector) = cv2.solvePnP(model_points, image_points, camera_matrix,
                                                                      dist_coeffs, flags=cv2.SOLVEPNP_UPNP)

        # Project a 3D point (0, 0, 1000.0) onto the image plane.
        # We use this to draw a line sticking out of the nose

        (nose_end_point2D, jacobian) = cv2.projectPoints(np.array([(0.0, 0.0, 1000.0)]), rotation_vector,
                                                         translation_vector, camera_matrix, dist_coeffs)

        for p in image_points:
            cv2.circle(img, (int(p[0]), int(p[1])), 3, (0, 0, 255), -1)

        p1 = (int(image_points[0][0]), int(image_points[0][1]))
        p2 = (int(nose_end_point2D[0][0][0]), int(nose_end_point2D[0][0][1]))
        x1, x2 = head_pose_points(img, rotation_vector, translation_vector, camera_matrix)

        cv2.line(img, p1, p2, (0, 255, 255), 2)
        cv2.line(img, tuple(x1), tuple(x2), (255, 255, 0), 2)

        # for (x, y) in marks:
        #     cv2.circle(img, (x, y), 4, (255, 255, 0), -1)
        # cv2.putText(img, str(p1), p1, font, 1, (0, 255, 255), 1)

        try:
            m = (p2[1] - p1[1]) / (p2[0] - p1[0])
            ang1 = int(math.degrees(math.atan(m)))
        except:
            ang1 = 90

        try:
            m = (x2[1] - x1[1]) / (x2[0] - x1[0])
            ang2 = int(math.degrees(math.atan(-1 / m)))
        except:
            ang2 = 90

        # 코드 분석 및 head_pose_estimation 조건 추가
        """
            # print('div by zero error')
        if ang1 >= 48:
            print('Head down')
            cv2.putText(img, 'Head down', (30, 30), font, 2, (255, 255, 128), 3)
        elif ang1 <= -48:
            print('Head up')
            cv2.putText(img, 'Head up', (30, 30), font, 2, (255, 255, 128), 3)

        if ang2 >= 48:
            print('Head right')
            cv2.putText(img, 'Head right', (90, 30), font, 2, (255, 255, 128), 3)
        elif ang2 <= -48:
            print('Head left')
            cv2.putText(img, 'Head left', (90, 30), font, 2, (255, 255, 128), 3)

        """

        cv2.putText(img, str(ang1), tuple(p1), font, 2, (128, 255, 255), 3)
        cv2.putText(img, str(ang2), tuple(x1), font, 2, (255, 255, 128), 3)

    cv2.imshow('img', img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        return False


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


def checkLandmark(image_width, image_height, points):
    # 0 : Nose | 1 : left_eye_inner | 2 : left_eye | 3 : left_eye_outer | 4 : right_eye_inner
    # 5 : right_eye | 6 : right_eye_outer | 7 : left_ear | 8 : right_ear | 9 : mouth_left
    # 10 : mouth_right | 11 : left_shoulder | 12 : right_shoulder | 13 : left_elbow | 14 : right_elbow
    # 15 : left_wrist | 16 : right_wrist | 17 : left_pinky | 18 : right_pinky | 19 : left_index
    # 20 : right_index | 21 : left_thumb | 22 : right_thumb | 23 : left_hip | 24 : right_hip
    # 25 : left_knee | 26 : right_knee | 27 : left_ankle | 28 : right_ankle | 29 : left_heel
    # 30 : right_heel | 31 : left_foot_index | 32.right_foot_index

    try:
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

        MPLandmark[0] = NoseX
        MPLandmark[1] = NoseY
        MPLandmark[2] = LMouthX
        MPLandmark[3] = LMouthY
        MPLandmark[4] = RMouthX
        MPLandmark[5] = RMouthY
        MPLandmark[6] = LShoulderX
        MPLandmark[7] = LShoulderY
        MPLandmark[8] = RShoulderX
        MPLandmark[9] = RShoulderY

        return True
    except:
        print("Some Landmark is not found")
        return False


def headCheck():
    MMouthX = (MPLandmark[2] + MPLandmark[4]) / 2
    MMouthY = (MPLandmark[3] + MPLandmark[5]) / 2

    lineResult1 = findLineFunction(MPLandmark[0], MPLandmark[1], MMouthX, MMouthY)  # Line1

    if not lineResult1:
        print('AngleResult = 0')
        print('Not Tilted Head')
        return -1

    lineResult2 = findLineFunction(MPLandmark[8], MPLandmark[9], MPLandmark[6], MPLandmark[7])  # Line2

    m1 = lineResult1[0]
    m2 = lineResult2[0]

    angle = round(findAngle(m1, m2))
    print('AngleResult = ' + str(angle))

    global threshold
    if angle <= threshold:
        print('Tilted Head')
        return True
    else:
        print('Not Tilted Head')
        return False


def MPPose(cap):
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
        if checkLandmark(image_width, image_height, results.pose_landmarks) is True:
            return True
        else:
            return False

        # cv2.imshow('MediaPipe Pose', cv2.flip(image, 1))


face_model = get_face_detector()
landmark_model = get_landmark_model()

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

threshold = 80  # MP head check의 기준 각도

cap = cv2.VideoCapture(0)

# 3D model points.
model_points = np.array([
    (0.0, 0.0, 0.0),  # Nose tip
    (0.0, -330.0, -65.0),  # Chin
    (-225.0, 170.0, -135.0),  # Left eye left corner
    (225.0, 170.0, -135.0),  # Right eye right corne
    (-150.0, -150.0, -125.0),  # Left Mouth corner
    (150.0, -150.0, -125.0)  # Right mouth corner
])

MPLandmark = []

if cap.isOpened():
    ret, img = cap.read()
    size = img.shape
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Camera internals
    focal_length = size[1]
    center = (size[1] / 2, size[0] / 2)
    camera_matrix = np.array([[focal_length, 0, center[0]], [0, focal_length, center[1]], [0, 0, 1]], dtype="double")

    while True:
        if MPPose(cap) is True:  # Check Landmark
            if headCheck() is True:  # Mediapipe Pose
                print("Tilted Head1")
            else:
                print("Not Tilted Head1")
        else:
            if head_pose_estimation(cap) is True:  # Mobilenet
                print("Tilted Head2")
            else:
                print("Not Tilted Head2")

        cv2.waitKey(3)

cv2.destroyAllWindows()
cap.release()
