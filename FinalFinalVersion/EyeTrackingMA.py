"""
DB에 저장된 학생의 ID 이용해 식별
"""
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db


def resetUnderstandResult(studentArray):
    global baseRef

    for name in studentArray:
        checkRef = baseRef + '/' + name
        dir = db.reference(checkRef)

        understandArray = str(ref.child(name).child('understand').get())
        # print("understandArray = " + str(understandArray))

        understandArray = []

        if understandArray != "None":
            dir.update({'understand': understandArray})

        # print("understandArray = " + str(understandArray))
        dir.update({'understand': understandArray})


def movingAverage(studentArray):
    global ref

    # 전체 eyeTracking 측정 횟수 확인
    totalCheckNum = len(ref.child(studentArray[0]).child('gaze').get())
    print(totalCheckNum)

    totalCheckNum = int(totalCheckNum)
    for i in range(0, totalCheckNum):
        totalGazeResult = [0, 0, 0, 0]
        studentEyePerSec = []

        for name in studentArray:
            gaze = ref.child(name).child('gaze').get()
            eyeTrackingResult = gaze[i]
            # print("name = " + name + " gaze = " + eyeTrackingResult)

            eachStudentList = [name, eyeTrackingResult]
            studentEyePerSec.append(eachStudentList)

            if eyeTrackingResult == "0":
                totalGazeResult[0] += 1
            elif eyeTrackingResult == "1":
                totalGazeResult[1] += 1
            elif eyeTrackingResult == "2":
                totalGazeResult[2] += 1
            elif eyeTrackingResult == "3":
                totalGazeResult[3] += 1

        understandGaze = str(totalGazeResult.index(max(totalGazeResult)))
        compareStudentEye(understandGaze, studentEyePerSec)


def compareStudentEye(understandGaze, studentEyePerSec):
    for name, gazeResult in studentEyePerSec:
        if understandGaze == gazeResult:
            saveUnderstandResult("1", name)
        else:
            saveUnderstandResult("0", name)


def saveUnderstandResult(understand, name):
    global ref
    global baseRef

    saveRef = baseRef + '/' + name
    dir = db.reference(saveRef)

    understandArray = str(ref.child(name).child('understand').get())

    if understandArray == "None":
        understandArray = understand
    else:
        understandArray = str(ref.child(name).child('understand').get()) + understand

    print("name = " + name + " | understandArray = " + understandArray)
    dir.update({'understand': understandArray})


# firebase
cred = credentials.Certificate('Setting File/uume.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://uume-58fe8-default-rtdb.firebaseio.com/'
})

# TeacherID-SubjectName 입력받기
# room_name = input(str('Enter room name(teacherID-class name): '))
# teacherID = room_name.split("-")[0]
# className = room_name.split("-")[1]

# date = input(str('Enter the Date(yyyymmdd): '))

# DB 구조 : class_v2 -> teacher ID -> Date -> ClassName -> StudentID
# 동적 입력 할당
# ref = db.reference().child('class_v2').child(teacherID).child(date).child(className)
# baseRef = 'class_v2/' + teacherID + '/' + date + '/' + className

# 수동
ref = db.reference().child('class_v2').child('seojin915').child('20220519').child('scienceA')
baseRef = 'class_v2/seojin915/20220519/scienceA'

studentArray = ref.child('students').get().split(".")
studentArray.remove('')

# resetUnderstandResult(studentArray)

# movingAverage(studentArray)
