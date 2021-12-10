import numpy as np
import cv2
from matplotlib import pyplot as plt

face_cascade = cv2.CascadeClassifier('../Setting File/haarcascade_frontalface_default.xml')

image = cv2.imread('../Test Image/face2.png')

grayImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# plt.figure(figsize=(12, 8))
# plt.imshow(grayImage, cmap='gray')
# plt.xticks([]), plt.yticks([])

faces = face_cascade.detectMultiScale(grayImage, 1.03, 5)

numberOfFace = str(faces.shape[0])

# print(faces.shape)
# print("Number of faces detected: " + str(numberOfFace))

if numberOfFace == "1":
    print("The student is sitting in his/her seat.")

for (x, y, w, h) in faces:
    cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)

cv2.rectangle(image, ((0, image.shape[0] - 25)), (270, image.shape[0]), (255, 255, 255), -1);
# cv2.putText(image, "Test", (0, image.shape[0] - 10), cv2.FONT_HERSHEY_TRIPLEX, 0.5,  (0, 0, 0), 1);

plt.figure(figsize=(12, 12))
plt.imshow(image, cmap='gray')
plt.xticks([]), plt.yticks([])
plt.show()