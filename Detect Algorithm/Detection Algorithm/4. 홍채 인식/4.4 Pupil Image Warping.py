import cv2
import imutils
import numpy as np


def videoDetector(cam, cascade):
    while True:
        ret, img = cam.read()
        angleTotal = 0

        while angleTotal < 360:
            img = cv2.resize(img, dsize=(400, 300), interpolation=cv2.INTER_AREA)

            if angleTotal == 90:
                img = imutils.rotate(img, 180)
                angleTotal += 180
            elif angleTotal <= 90 or angleTotal >= 270:
                img = imutils.rotate(img, 10)
                angleTotal += 10

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            results = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(20, 20))

            cv2.imshow('img', gray)
            cv2.waitKey(1)

            if len(results) == 0:
                print('The student isn\'t sitting in his/her seat.')
                continue
            elif len(results) >= 1:
                print('The student is sitting in his/her seat.')
                for box in results:
                    x, y, w, h = box
                    pts1 = np.float32([[x, y], [x, y + h], [x + w, y], [x + w, y + h]])
                    pts2 = np.float32([[0, 0], [0, 150], [150, 0], [150, 150]])
                    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), thickness=2)

                    # ---② 변환 전 좌표를 원본 이미지에 표시
                    cv2.circle(img, (x, y), 10, (255, 0, 0), -1)
                    cv2.circle(img, (x, y + h), 10, (0, 255, 0), -1)
                    cv2.circle(img, (x + w, y), 10, (0, 0, 255), -1)
                    cv2.circle(img, (x + w, y + h), 10, (0, 255, 255), -1)

                    # ---③ 원근 변환 행렬 계산
                    mtrx = cv2.getPerspectiveTransform(pts1, pts2)
                    # ---④ 원근 변환 적용
                    dst = cv2.warpPerspective(img, mtrx, (w, h))

                    cv2.imshow("origin", img)
                    cv2.imshow('perspective', dst)
                    cv2.waitKey(0)

                print(angleTotal)

                cv2.imshow('CheckSeat', img)
                print(angleTotal)
                cv2.waitKey(0)
                break

        if cv2.waitKey(1) > 0:
            break


cascade_filename = '../Setting File/haarcascade_frontalface_alt.xml'
cascade = cv2.CascadeClassifier(cascade_filename)

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
videoDetector(cam, cascade)
