"""
DB에 저장된 학생의 ID 이용해 식별
"""


def movingAverage():
    global studentNum
    for i in range(1, studentNum + 1):
        global eyeTrackingResult
        # eyeTrackingResult = 가져온 값 저장
        # 값 가져올 때는 학생의 ID 이용
        if eyeTrackingResult == 0:
            gazeResult[0] += 1
        elif eyeTrackingResult == 1:
            gazeResult[1] += 1
        elif eyeTrackingResult == 2:
            gazeResult[2] += 1
        elif eyeTrackingResult == 3:
            gazeResult[3] += 1

    return gazeResult.index(max(gazeResult))


def checkStudentEye(eyeResult):
    global studentNum
    for i in range(1, studentNum):
        # 동공인식 MovingAverage 결과와 각 학생 결과 비교
        # 전체 정보 한꺼번에 저장할 것인지
        # 각 학생별로 저장할 것인지
        # 아니면 둘다?
        
        eachStudentResult = 10 # 값 가져오기
        # 전체 moving average 결과와 학생의 eye tracking 결과가
        # 같으면 집중 O
        # 다르면 집중 X
        if eyeResult == eachStudentResult:
            print("집중 O")
        else :
            print("집중 X")


studentNum = 10  # 이 자리에 학생 수 가져오기
eyeTrackingResult = -1
gazeResult = [0, 0, 0, 0]
movingAverageResult = -1

eyeResult = movingAverage()
checkStudentEye(eyeResult)
