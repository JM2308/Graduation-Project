import dlib
import cv2 as cv
import numpy as np
import queue
from gaze_tracking import GazeTracking
import time
import math
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime


def queueUpdate(queueName, angle):
    movingQueue = queueName

    if movingQueue.qsize() == 10:
        movingQueue.get()
        movingQueue.put(angle)
    elif movingQueue.qsize() < 10:
        movingQueue.put(angle)

    sum = 0

    for index in range(0, movingQueue.qsize()):
        data = movingQueue.get()
        sum += data

        movingQueue.put(data)

    movingAverage = sum / movingQueue.qsize()

    if queueName == "TH_movingQueue":
        global TH_movingQueue
        TH_movingQueue = movingQueue
    elif queueName == "FC_movingQueue":
        global FC_movingQueue
        FC_movingQueue = movingQueue

    return movingAverage


def headCheck(X1, Y1, X2, Y2):
    global angle

    theta = np.arctan((X2 - X1) / (Y2 - Y1))
    angle = theta * 180 / math.pi
    angle = abs(angle)

    result = '0'

    newMovingAverage = queueUpdate(TH_movingQueue, angle)

    global TH_preMovingAverage

    if TH_movingQueue.qsize() == 0:
        TH_preMovingAverage = newMovingAverage

    if angle >= TH_threshold:
        # 계산한 각도가 threshold 보다 클 때
        print("Tilted Head")
        result = '1'

    if newMovingAverage >= TH_threshold:
        # average 가  threshold 보다 클 때
        if TH_preMovingAverage - (TH_threshold / 10) <= newMovingAverage:
            # 급격하게 고개 각도가 줄어들 때 (고개갸웃 -> 원래대로 돌아올때)를 확인
            print("Tilted Head")
            result = '1'

    if TH_movingQueue.qsize() == 10:
        if TH_preMovingAverage + (TH_threshold / 10) <= newMovingAverage:
            # 급격하게 고개 각도가 커질 때 (기존 -> 고개 갸웃거릴 때)를 확인
            print("Tilted Head")
            result = '1'

    TH_preMovingAverage = newMovingAverage

    return result


def calculateLength(LEyeEdgeX, LEyeEdgeY, REyeEdgeX, REyeEdgeY):
    eyeEdgeLength = round(math.pow(math.pow((LEyeEdgeX - REyeEdgeX), 2) + math.pow((LEyeEdgeY - REyeEdgeY), 2), 1 / 2))
    return eyeEdgeLength


def faceCloserCheck(list_points):
    LEyeEdgeX = list_points[36][0]
    LEyeEdgeY = list_points[36][1]
    REyeEdgeX = list_points[45][0]
    REyeEdgeY = list_points[45][1]

    result = '0'

    faceLength = calculateLength(LEyeEdgeX, LEyeEdgeY, REyeEdgeX, REyeEdgeY)
    # print("faceLength = ", faceLength)

    newMovingAverage = queueUpdate(FC_movingQueue, faceLength)
    # print("Average = ", newMovingAverage)

    global FC_preMovingAverage
    global FC_threshold

    if FC_preMovingAverage == 0:
        FC_preMovingAverage = newMovingAverage
    elif FC_preMovingAverage + FC_threshold <= newMovingAverage:
        print("Face Closer")
        result = '1'

    return result


def eyetrackingCheck(img_frame):
    global gazeResult
    global preSec

    result = 3

    # 3초 간격으로 저장 (3초가 한순간에 딱 측정되는 것이 X! 그 순간 1초 동안 계속 측정)
    # So, 1초 동안 가장 많이 측정된 경우를 파악하고 이 데이터를 저장!
    # gaze = [centerNum, leftNum, rightNum, blinkingNum]의 형태
    nowSec = math.trunc(int(time.time() - start)) + 1
    if nowSec % 3 == 0:
        if gaze.is_center():
            gazeResult[0] += 1
            # text = "Looking center"
        elif gaze.is_left():
            gazeResult[1] += 1
            # text = "Looking left"
            # Looking left = 1
        elif gaze.is_right():
            gazeResult[2] += 1
            # text = "Looking right"
            # Looking right = 2
        elif gaze.is_blinking():
            gazeResult[3] += 1
            # text = "Blinking"
            # Looking Blinking = 3
        # cv.putText(img_frame, text, (90, 60), cv.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)
    elif preSec != nowSec and (nowSec - 1) % 3 == 0 and nowSec != 1:
        # 3초 간격이 아니면 gazeResult를 다시 초기화
        # print("check gazeResult = [", gazeResult[0], ", ", gazeResult[1], ", ", gazeResult[2], ", ", gazeResult[3], "]")
        # 값이 가장 큰 값이 있는 index 저장
        # index = 0 -> center | index = 1 -> left | index = 2 -> right | index = 3 -> blinking
        result = gazeResult.index(max(gazeResult))
        if result == 0:
            print("center")
            print("gazeResult = [", gazeResult[0], ", ", gazeResult[1], ", ", gazeResult[2], ", ", gazeResult[3], "]\n")
        elif result == 1:
            print("left")
            print("gazeResult = [", gazeResult[0], ", ", gazeResult[1], ", ", gazeResult[2], ", ", gazeResult[3], "]\n")
        elif result == 2:
            print("right")
            print("gazeResult = [", gazeResult[0], ", ", gazeResult[1], ", ", gazeResult[2], ", ", gazeResult[3], "]\n")
        elif result == 3:
            print("blinking")
            print("gazeResult = [", gazeResult[0], ", ", gazeResult[1], ", ", gazeResult[2], ", ", gazeResult[3], "]\n")
        # print(result)
        # 이 result를 DB에 저장!!
        gazeResult = [0, 0, 0, 0]

    preSec = nowSec

    # left_pupil = gaze.pupil_left_coords()
    # right_pupil = gaze.pupil_right_coords()
    # cv.putText(img_frame, "Left pupil:  " + str(left_pupil), (90, 130), cv.FONT_HERSHEY_DUPLEX, 0.9, (147, 58, 31), 1)
    # cv.putText(img_frame, "Right pupil: " + str(right_pupil), (90, 165), cv.FONT_HERSHEY_DUPLEX, 0.9, (147, 58, 31), 1)

    return result


# firebase
cred = credentials.Certificate('Setting File/uume.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://uume-58fe8-default-rtdb.firebaseio.com/'
})

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('Setting File/shape_predictor_68_face_landmarks.dat')

# cap = cv.VideoCapture(0)

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

gaze = GazeTracking()

start = time.time()
gazeResult = [0, 0, 0, 0]
preSec = 0

TH_movingQueue = queue.Queue()
FC_movingQueue = queue.Queue()

TH_preMovingAverage = 0
FC_preMovingAverage = 0

TH_threshold = 25
FC_threshold = 20

# database 정보 입력
# room_name seojin915-scienceA 이런식으로 입력 A는 시간임
#           선생님id-과목+시간
room_name = input(str('Enter room name(teacherID-class name): '))
user_id = input(str('Enter user id: '))
teacher_id = room_name.split('-')[0]
class_name = room_name.split('-')[1]

y = str(datetime.today().year)
m = str(datetime.today().month)
d = str(datetime.today().day)
date = y + m + d
ref = 'class_v2/' + teacher_id + '/' + date + '/' + class_name + '/' + user_id
ref2 = 'class_v2/' + teacher_id + '/' + date + '/' + class_name
dir = db.reference(ref)
dir2 = db.reference(ref2)

student_data = dir.get()
# print(student_data)
student_list = dir2.get()

global in_seat_array
global tilted_array
global face_closer_array
global gaze_array
global students_array

if student_list is None:
    students_array = ''
else:
    students_array = str(student_list['students'])
dir2.update({'students': students_array + user_id + '.'})

if student_data is None:
    in_seat_array = ''
    tilted_array = ''
    face_closer_array = ''
    gaze_array = ''
    gaze_score_array = ' '
else:
    in_seat_array = str(student_data['in_seat'])
    tilted_array = str(student_data['tilted'])
    face_closer_array = str(student_data['face_closer'])
    gaze_array = str(student_data['gaze'])
    gaze_score_array = str(student_data['gaze_score'])

# 학생들 id 리스트 가져오기
student_list = dir2.get()
students_array = str(student_list['students'])
student_id_list = students_array.split('.')[0:-1]
print(student_id_list)

count = 0
while True:
    time.sleep(3)
    img = 'C:/Users/jimin/Downloads/'
    if count == 0:
        img += 'test.png'
    else:
        img_name = 'test (' + str(count) + ').png'
        img += img_name
    print(count)
    print(img)
    img_frame = cv.imread(img)
    img_gray = cv.cvtColor(img_frame, cv.COLOR_BGR2GRAY)
    dets = detector(img_gray, 1)

    # We send this frame to GazeTracking to analyze it
    gaze.refresh(img_frame)

    img_frame = gaze.annotated_frame()
    text = ""

    # eyetrackingCheck(img_frame)
    gaze_result = eyetrackingCheck(img_frame)
    gaze_array += str(gaze_result)

    in_seat_check = False
    for face in dets:
        in_seat_check = True
        shape = predictor(img_frame, face)
        list_points = []

        for p in shape.parts():
            list_points.append([p.x, p.y])

        list_points = np.array(list_points)

        LEyeEdge = list_points[36]
        REyeEdge = list_points[45]

        for i, pt in enumerate(list_points[index]):
            pt_pos = (pt[0], pt[1])
            cv.circle(img_frame, pt_pos, 2, (0, 255, 0), -1)

        cv.rectangle(img_frame, (face.left(), face.top()), (face.right(), face.bottom()), (0, 0, 255), 3)

        tilted_result = headCheck(list_points[27][0], list_points[27][1], list_points[30][0], list_points[30][1])
        tilted_array += tilted_result
        face_closer_result = faceCloserCheck(list_points)
        face_closer_array += face_closer_result
        # cv.imshow('result', img_frame)

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

    if in_seat_check:
        in_seat_array += '1'
    else:
        in_seat_array += '0'
        tilted_array += '0'
        face_closer_array += '0'

    # 파이어베이스에 저장
    dir.update({'in_seat': in_seat_array,
                'tilted': tilted_array,
                'face_closer': face_closer_array,
                'gaze': gaze_array})

    # gaze 최빈값 구하기
    gaze_list = []
    for i in student_id_list:
        temp_ref = 'class_v2/' + teacher_id + '/' + date + '/' + class_name + '/' + i
        dir3 = db.reference(temp_ref)
        gaze_data = dir3.get()
        gaze_value = str(gaze_data['gaze'])[count]
        gaze_list.append(gaze_value)
    gaze_target = max(gaze_list)

    # 최빈값과 비교하기
    dir = db.reference(ref)
    gaze_data = dir.get()
    gaze_value = str(gaze_data['gaze'])[count]
    if gaze_value == gaze_target:
        gaze_score = '1'
    else:
        gaze_score = '0'
    gaze_score_array += gaze_score

    # 비교 결과 데이터베이스에 저장
    dir.update({'gaze_score': gaze_score_array
                })

    count += 1
# cap.release()
