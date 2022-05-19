import cv2
import numpy as np
import math
import tensorflow as tf
import dlib
import queue


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


def head_pose_estimation(img):
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

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, str(ang1), tuple(p1), font, 2, (128, 255, 255), 3)
        # cv2.putText(img, str(ang2), tuple(x1), font, 2, (255, 255, 128), 3)

    cv2.imshow('img', img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        return False


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
    print(movingAverage)
    return movingAverage


def headCheck(X1, Y1, X2, Y2):
    global angle

    theta = np.arctan((X2 - X1) / (Y2 - Y1))
    angle = theta * 180 / math.pi
    angle = abs(angle)
    print('AngleResult = ' + str(angle))

    newMovingAverage = queueUpdate(angle)
    # print("Average = ", newMovingAverage)

    global preMovingAverage

    if movingQueue.qsize() == 0:
        preMovingAverage = newMovingAverage

    if angle >= threshold:
        # 계산한 각도가 threshold 보다 클 때
        # print("Tilted Head")
        return True

    if newMovingAverage >= threshold:
        # average 가  threshold 보다 클 때
        if preMovingAverage - (threshold / 10) <= newMovingAverage:
            # 급격하게 고개 각도가 줄어들 때 (고개갸웃 -> 원래대로 돌아올때)를 확인
            # print("Tilted Head")
            return True

    if movingQueue.qsize() == 10:
        if preMovingAverage + (threshold / 10) <= newMovingAverage:
            # 급격하게 고개 각도가 커질 때 (기존 -> 고개 갸웃거릴 때)를 확인
            # print("Tilted Head")
            return True

    preMovingAverage = newMovingAverage

    # return True
    return False ## Check


face_model = get_face_detector()
landmark_model = get_landmark_model()

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

UsingLandmark = list(range(27, 28)) + list(range(30, 31))

index = UsingLandmark

movingQueue = queue.Queue()
preMovingAverage = 0
threshold = 25

# 3D model points.
model_points = np.array([
    (0.0, 0.0, 0.0),  # Nose tip
    (0.0, -330.0, -65.0),  # Chin
    (-225.0, 170.0, -135.0),  # Left eye left corner
    (225.0, 170.0, -135.0),  # Right eye right corne
    (-150.0, -150.0, -125.0),  # Left Mouth corner
    (150.0, -150.0, -125.0)  # Right mouth corner
])

cap = cv2.VideoCapture(0)

if cap.isOpened():
    ret, img = cap.read()
    size = img.shape

    # Camera internals
    focal_length = size[1]
    center = (size[1] / 2, size[0] / 2)
    camera_matrix = np.array([[focal_length, 0, center[0]], [0, focal_length, center[1]], [0, 0, 1]], dtype="double")

    while True:
        ret, img_frame = cap.read()
        img_gray = cv2.cvtColor(img_frame, cv2.COLOR_BGR2GRAY)
        dets = detector(img_gray, 1)
        ######################################
        for face in dets:
            shape = predictor(img_frame, face)
            list_points = []

            for p in shape.parts():
                list_points.append([p.x, p.y])

            list_points = np.array(list_points)

            for i, pt in enumerate(list_points[index]):
                pt_pos = (pt[0], pt[1])
                cv2.circle(img, pt_pos, 2, (0, 255, 0), -1)

            cv2.rectangle(img, (face.left(), face.top()), (face.right(), face.bottom()), (0, 0, 255), 3)

            if headCheck(list_points[27][0], list_points[27][1], list_points[30][0], list_points[30][1]) is True:
                print("Tilted Head")

            head_pose_estimation(img_frame)
        """
        if headCheck(list_points[27][0], list_points[27][1], list_points[30][0],
                     list_points[30][1]) is True or head_pose_estimation(cap) is True
            print("Tilted Head")
        else:
            print("Not Tilted Head")
        """
        ##############################
        # cv2.imshow('result', img_frame)
        cv2.waitKey(3)

cv2.destroyAllWindows()
cap.release()

"""
if cap.isOpened():
    ret, img = cap.read()
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    dets = detector(img_gray, 1)
    size = img.shape
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Camera internals
    focal_length = size[1]
    center = (size[1] / 2, size[0] / 2)
    camera_matrix = np.array([[focal_length, 0, center[0]], [0, focal_length, center[1]], [0, 0, 1]], dtype="double")

    while True:
        for face in dets:
            shape = predictor(img, face)
            list_points = []

            for p in shape.parts():
                list_points.append([p.x, p.y])

            list_points = np.array(list_points)

            for i, pt in enumerate(list_points[index]):
                pt_pos = (pt[0], pt[1])
                cv.circle(img, pt_pos, 2, (0, 255, 0), -1)

            cv.rectangle(img, (face.left(), face.top()), (face.right(), face.bottom()), (0, 0, 255), 3)

        if headCheck(list_points[27][0], list_points[27][1], list_points[30][0], list_points[30][1]) is True or head_pose_estimation(cap) is True:
            print("Tilted Head")
        else:
            print("Not Tilted Head")

        cv.imshow('result', img)
        cv2.waitKey(3)
"""


"""
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

        for i, pt in enumerate(list_points[index]):
            pt_pos = (pt[0], pt[1])
            cv.circle(img_frame, pt_pos, 2, (0, 255, 0), -1)

        cv.rectangle(img_frame, (face.left(), face.top()), (face.right(), face.bottom()), (0, 0, 255), 3)

        headCheck(list_points[27][0], list_points[27][1], list_points[30][0], list_points[30][1])
        cv.imshow('result', img_frame)

        key = cv.waitKey(1)

cap.release()
"""