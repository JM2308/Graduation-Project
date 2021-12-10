import cv2
import math


def output_keypoints(frame, proto_file, weights_file, threshold, model_name, BODY_PARTS):
    global points

    net = cv2.dnn.readNetFromCaffe(proto_file, weights_file)

    image_height = 300
    image_width = 300

    input_blob = cv2.dnn.blobFromImage(frame, 1.0 / 255, (image_width, image_height), (0, 0, 0),
                                       swapRB=False, crop=False)

    net.setInput(input_blob)

    out = net.forward()
    out_height = out.shape[2]
    out_width = out.shape[3]

    frame_height, frame_width = frame.shape[:2]

    points = []

    for i in range(len(BODY_PARTS)):
        prob_map = out[0, i, :, :]
        min_val, prob, min_loc, point = cv2.minMaxLoc(prob_map)

        x = (frame_width * point[0]) / out_width
        x = int(x)
        y = (frame_height * point[1]) / out_height
        y = int(y)

        if prob > threshold:  # [pointed]
            cv2.circle(frame, (x, y), 5, (0, 255, 255), thickness=-1, lineType=cv2.FILLED)
            cv2.putText(frame, str(i), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1, lineType=cv2.LINE_AA)
            points.append((x, y))

        else:  # [not pointed]
            cv2.circle(frame, (x, y), 5, (0, 255, 255), thickness=-1, lineType=cv2.FILLED)
            cv2.putText(frame, str(i), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 1, lineType=cv2.LINE_AA)
            points.append(None)

    cv2.imshow("Output_Keypoints", frame)
    return frame


def output_keypoints_with_lines(frame, POSE_PAIRS):
    for pair in POSE_PAIRS:
        part_a = pair[0]  # 0 (Head)
        part_b = pair[1]  # 1 (Neck)
        if points[part_a] and points[part_b]:
            cv2.line(frame, points[part_a], points[part_b], (0, 255, 0), 3)

    cv2.imshow("output_keypoints_with_lines", frame)


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


def headCheck():
    NoseX = points[0][0]
    NoseY = points[0][1]
    NeckX = points[1][0]
    NeckY = points[1][1]
    RShoulderX = points[2][0]
    RShoulderY = points[2][1]
    LShoulderX = points[5][0]
    LShoulderY = points[5][1]

    lineResult1 = findLineFunction(NoseX, NoseY, NeckX, NeckY)  # Line1
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


BODY_PARTS_BODY_25 = {0: "Nose", 1: "Neck", 2: "RShoulder", 3: "RElbow", 4: "RWrist", 5: "LShoulder",
                      6: "LElbow", 7: "LWrist", 8: "REye", 9: "LEye", 10: "REar", 11: "LEar", 12: "Background"}

POSE_PAIRS_BODY_25 = [[0, 1], [0, 8], [0, 9], [1, 2], [1, 5], [2, 3], [3, 4], [5, 6], [6, 7], [8, 10], [9, 11]]

protoFile_body_25 = "../Setting File/pose_deploy.prototxt"
weightsFile_body_25 = "../Setting File/pose_iter_584000.caffemodel"

frame_body_25 = cv2.imread('../Test Image/face3.png').copy()
frame_BODY_25 = output_keypoints(frame=frame_body_25, proto_file=protoFile_body_25, weights_file=weightsFile_body_25, threshold=0.2, model_name="BODY_25", BODY_PARTS=BODY_PARTS_BODY_25)
output_keypoints_with_lines(frame=frame_BODY_25, POSE_PAIRS=POSE_PAIRS_BODY_25)

headCheck()

cv2.waitKey(0)