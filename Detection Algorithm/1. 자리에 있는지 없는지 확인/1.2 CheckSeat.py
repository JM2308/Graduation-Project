import cv2


def videoDetector(cam, cascade):
    while True:
        ret, img = cam.read()
        img = cv2.resize(img, dsize=None, fx=1.0, fy=1.0)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        results = cascade.detectMultiScale(gray, caleFactor=1.1, minNeighbors=5, minSize=(20, 20))

        if len(results) == 0:
            print('The student isn\'t sitting in his/her seat.')
        elif len(results) >= 1:
            print('The student is sitting in his/her seat.')

        for box in results:
            x, y, w, h = box
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), thickness=2)

        cv2.imshow('CheckSeat', cv2.flip(img, 1))

        if cv2.waitKey(1) > 0:
            break


cascade_filename = '../Setting File/haarcascade_frontalface_alt.xml'
cascade = cv2.CascadeClassifier(cascade_filename)

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
videoDetector(cam, cascade)

