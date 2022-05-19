import cv2
import imutils


cascade_filename = '../Setting File/haarcascade_frontalface_alt.xml'
cascade = cv2.CascadeClassifier(cascade_filename)

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)

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

        if len(results) == 0:
            print('The student isn\'t sitting in his/her seat.')
            continue
        elif len(results) >= 1:
            print('The student is sitting in his/her seat.')
            # for box in results:
                # x, y, w, h = box
                # cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), thickness=2)
            break

    if cv2.waitKey(1) > 0:
        break
