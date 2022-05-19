import cv2

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if cap.isOpened():
    while True:
        ret, video = cap.read()
        if ret:
            video = cv2.resize(video, dsize=(400, 300), interpolation=cv2.INTER_AREA)
            cv2.imshow('video', video)

            if cv2.waitKey(1) != -1:
                break
        else:
            print("no frame")
            break
else:
    print("can't open camera")

cap.release()
cv2.destroyAllWindows()