# Graduation-Project

<h3> 1. Check Seat : 학생이 자리에 있는지 없는지 확인 </h3>
 - 과정 01 : 학생이 고개를 갸웃거리고 있을 때 인식이 잘 안되는 부분을 보완하기 위해 캡쳐한 프레임을 왼쪽으로 90도, 오른쪽으로 90도까지 10도씩 사진을 회전시켜 얼굴을 인식 <br>
 - 과정 02 : 얼굴 인식이 될 경우 학생이 자리에 앉아있는 것으로 판단하여 다음 알고리즘으로 넘어간다. <br>
 - 과정 03 : 얼굴 인식이 안될 경우 학생이 자리에 앉아있지 않은 것으로 판단 <br>

<h3> 2-1. Tilted Head (Old) : 고개를 갸웃거리는지 확인 </h3>
 - 과정 01 : Mediapipe Pose과 MobileNet 방식을 결합 <br>
 - 과정 02 : Mediapiep Pose의 경우 코와 입 중점, 어깨 왼쪽과 오른쪽을 이은 두 직선의 사이각을 계산하여 일정 각도 이하로 나타나면 고개를 갸웃거리는 것으로 판단 <br>
 - 과정 03 : MobileNet의 경우, 얼굴의 XYZ축 각도를 계산하여 특정 조건을 만족할 경우 고개를 갸웃거리는 것으로 판단 <br>
 - 과정 04 : Mediapipe Pose 방식을 이용하기 위해서는 Shoulder Landmark가 필요 <br>
 - 과정 05 : 만약 Shoulder Landmark가 인식될 경우, Mediapipe Pose 방식을 이용해 알고리즘 결과 측정 <br>
 - 과정 06 : 만약 Shoulder Landmark가 인식되지 않을 경우, Mediapipe Pose 방식을 이용해 알고리즘 결과 측정 <br>

<table>
    <tr>
        <td> Shoulder Landmark Check Result </td>
        <td> Mediapipe Pose Result </td>
        <td> MobileNet Result </td>
        <td> Tilted Head Result </td>
    </tr>
    <tr>
        <td rowspan="4"> O </td>
        <td rowspan="2"> O </td>
        <td> - </td>
        <td rowspan="2"> O </td>
    </tr>
    <tr>
        <td> - </td>
    </tr>
    <tr>
        <td rowspan="2"> X </td>
        <td> - </td>
        <td rowspan="2"> X </td>
    </tr>
    <tr>
        <td> - </td>
    </tr>
    <tr>
        <td rowspan="2"> X </td>
        <td> - </td>
        <td> O </td>
        <td> O</td>
    </tr>
    <tr>
        <td> - </td>
        <td> X </td>
        <td> X </td>
    </tr>
</table>

<h3> 2-2. Tilted Head (New) : 고개를 갸웃거리는지 확인 </h3>
 New Version <br>
 - 과정 01 : dlib의 눈 사이 중점 (27번)과 코 (30번)의 랜드마크 추출 <br>
 - 과정 02 : 추출한 랜드마크를 토대로 탄젠트 삼각비 함수인 arctan를 이용하여 각도 계산 <br>
 - 과정 03 : 가장 최근 10개 frame의 계산 결과를 평균내어 조건 확인 <br>
 - 조건 01 : angle ≥ threshold <br>
 - 조건 02-1 : newMovingAverage ≥ threshold <br>
 - 조건 02-2 : 각도가 급격하게 낮아지는 경우 (고개 갸웃 → 원래대로)를 예외 조건으로 추가 <br>
              ( → preMovingAverage - (threshold / 10) ≤ newMovingAverage ) <br>
 - 조건 03-1 : QueueSize = 10 <br>
 - 조건 03-2 : 각도가 급격하게 커지는 경우 (기존 → 고개 갸웃)을 예외 조건으로 추가 <br>
              ( → preMovingAverage + (threshold / 10) ≤ newMovingAverage ) <br>
 

<h3> 3. Frown Grabella : 미간을 찌푸리고 있는지 확인 </h3>
 - 방식 :  <br>
 - 결과 :  <br>

<h3> 4. Face Closer : 얼굴을 가까이했는지 확인 </h3>
 - 과정 01 : 정해진 초마다 한번씩 프레임을 캡쳐 <br>
 - 과정 02 : 캡쳐한 프레임에 나타나는 왼쪽 귀와 오른쪽 귀 사이의 거리를 계산 <br>
 - 과정 03 : 최근 프레임 10개를 기준으로 귀 사이 거리 평균을 구하고 이를 이용하여 귀 사이 거리 변화값이 기준값보다 크다면 얼굴을 가까이한 것으로 판단 <br>

<h3> 5. Eye Tracking : 홍채의 움직임을 인식 </h3>
 - 과정 01 : 3초마다 1초씩 동공의 움직임 측정 <br>
 - 과정 02 : 1초 동안 저장한 데이터를 통해 가장 많이 측정된 방향 추출 <br>
 - 과정 03 : 추출한 결과를 DB에 저장 <br>
 - 과정 04 : 이후 모든 학생의 데이터 평균을 이용해 결과 확인 <br>

# < 알고리즘 작동 순서 >
1. Check Seat <br>
2.  <br>
3.  <br>
4.  <br>
5.  <br>
 + 동시에 Eye Tracking 진행 <br>