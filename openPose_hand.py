# To use Inference Engine backend, specify location of plugins:
# source /opt/intel/computer_vision_sdk/bin/setupvars.sh
import cv2 as cv
import numpy as np
import argparse
# protoFile = "C:/openpose/models/hand/pose_deploy.prototxt"
# weightsFile = "c:/openpose/models/hand/pose_iter_102000.caffemodel"

net = cv.dnn.readNet(cv.samples.findFile(args.proto), cv.samples.findFile(args.model))

cap = cv.VideoCapture(args.input if args.input else 0)

while cv.waitKey(1) < 0:
    hasFrame, frame = cap.read()
    if not hasFrame:
        cv.waitKey()
        break

    frameWidth = frame.shape[1]
    frameHeight = frame.shape[0]
    inp = cv.dnn.blobFromImage(frame, inScale, (inWidth, inHeight),
                              (0, 0, 0), swapRB=False, crop=False)
    net.setInput(inp)
    out = net.forward()

    assert(len(BODY_PARTS) <= out.shape[1])

    points = []
    for i in range(len(BODY_PARTS)):
        # Slice heatmap of corresponding body's part.
        heatMap = out[0, i, :, :]

        # Originally, we try to find all the local maximums. To simplify a sample
        # we just find a global one. However only a single pose at the same time
        # could be detected this way.
        _, conf, _, point = cv.minMaxLoc(heatMap)
        x = (frameWidth * point[0]) / out.shape[3]
        y = (frameHeight * point[1]) / out.shape[2]

        # Add a point if it's confidence is higher than threshold.
        points.append((int(x), int(y)) if conf > args.thr else None)

    for pair in POSE_PAIRS:
        partFrom = pair[0]
        partTo = pair[1]
        assert(partFrom in BODY_PARTS)
        assert(partTo in BODY_PARTS)

        idFrom = BODY_PARTS[partFrom]
        idTo = BODY_PARTS[partTo]

        if points[idFrom] and points[idTo]:
            cv.line(frame, points[idFrom], points[idTo], (0, 255, 0), 3)
            cv.ellipse(frame, points[idFrom], (3, 3), 0, 0, 360, (0, 0, 255), cv.FILLED)
            cv.ellipse(frame, points[idTo], (3, 3), 0, 0, 360, (0, 0, 255), cv.FILLED)

    t, _ = net.getPerfProfile()
    freq = cv.getTickFrequency() / 1000
    cv.putText(frame, '%.2fms' % (t / freq), (10, 20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0))

    cv.imshow('OpenPose using OpenCV', frame)
# import cv2 as cv
#
# BODY_PARTS = {
#     "손목": 0,
#     "엄지0": 1, "엄지1": 2, "엄지2": 3, "엄지3": 4,
#     "검지0": 5, "검지1": 6, "검지2": 7, "검지3": 8,
#     "중지0": 9, "중지1": 10, "중지2": 11, "중지3": 12,
#     "약지0": 13, "약지1": 14, "약지2": 15, "약지3": 16,
#     "소지0": 17, "소지1": 18, "소지2": 19, "소지3": 20,
# }
#
# POSE_PAIRS = [["손목", "엄지0"], ["엄지0", "엄지1"],
#               ["엄지1", "엄지2"], ["엄지2", "엄지3"],
#               ["손목", "검지0"], ["검지0", "검지1"],
#               ["검지1", "검지2"], ["검지2", "검지3"],
#               ["손목", "중지0"], ["중지0", "중지1"],
#               ["중지1", "중지2"], ["중지2", "중지3"],
#               ["손목", "약지0"], ["약지0", "약지1"],
#               ["약지1", "약지2"], ["약지2", "약지3"],
#               ["손목", "소지0"], ["소지0", "소지1"],
#               ["소지1", "소지2"], ["소지2", "소지3"]]
#
# # BODY_PARTS = {
# #                 "Wrist": 0,
# #                 "ThumbMetacarpal": 1, "ThumbProximal": 2, "ThumbMiddle": 3, "ThumbDistal": 4,
# #                 "IndexFingerMetacarpal": 5, "IndexFingerProximal": 6, "IndexFingerMiddle": 7, "IndexFingerDistal": 8,
# #                 "MiddleFingerMetacarpal": 9, "MiddleFingerProximal": 10, "MiddleFingerMiddle": 11, "MiddleFingerDistal": 12,
# #                 "RingFingerMetacarpal": 13, "RingFingerProximal": 14, "RingFingerMiddle": 15, "RingFingerDistal": 16,
# #                 "LittleFingerMetacarpal": 17, "LittleFingerProximal": 18, "LittleFingerMiddle": 19, "LittleFingerDistal": 20,
# #             }
#
# # POSE_PAIRS = [["Wrist", "ThumbMetacarpal"], ["ThumbMetacarpal", "ThumbProximal"],
# #                ["ThumbProximal", "ThumbMiddle"], ["ThumbMiddle", "ThumbDistal"],
# #                ["Wrist", "IndexFingerMetacarpal"], ["IndexFingerMetacarpal", "IndexFingerProximal"],
# #                ["IndexFingerProximal", "IndexFingerMiddle"], ["IndexFingerMiddle", "IndexFingerDistal"],
# #                ["Wrist", "MiddleFingerMetacarpal"], ["MiddleFingerMetacarpal", "MiddleFingerProximal"],
# #                ["MiddleFingerProximal", "MiddleFingerMiddle"], ["MiddleFingerMiddle", "MiddleFingerDistal"],
# #                ["Wrist", "RingFingerMetacarpal"], ["RingFingerMetacarpal", "RingFingerProximal"],
# #                ["RingFingerProximal", "RingFingerMiddle"], ["RingFingerMiddle", "RingFingerDistal"],
# #                ["Wrist", "LittleFingerMetacarpal"], ["LittleFingerMetacarpal", "LittleFingerProximal"],
# #                ["LittleFingerProximal", "LittleFingerMiddle"], ["LittleFingerMiddle", "LittleFingerDistal"]]
#
#
# threshold = 0.1
#
# protoFile = "C:/openpose/models/hand/pose_deploy.prototxt"
# weightsFile = "c:/openpose/models/hand/pose_iter_102000.caffemodel"
#
# net = cv.dnn.readNetFromCaffe(protoFile, weightsFile)
# net.setPreferableBackend(cv.dnn.DNN_BACKEND_CUDA)
# net.setPreferableTarget(cv.dnn.DNN_TARGET_CUDA)
#
# cap = cv.VideoCapture(0)
#
# inputHeight = 368
# inputWidth = 368
# inputScale = 1.0 / 255
#
# while cv.waitKey(1) < 0:
#     hasFrame, frame = cap.read()
#     # frame = cv.resize(frame, dsize=(320, 240), interpolation=cv.INTER_AREA)
#
#     if not hasFrame:
#         cv.waitKey()
#         break
#
#     frameWidth = frame.shape[1]
#     frameHeight = frame.shape[0]
#     inp = cv.dnn.blobFromImage(frame, inputScale, (inputWidth, inputHeight), (0, 0, 0), swapRB=False, crop=False)
#
#     net.setInput(inp)
#     out = net.forward()
#
#     points = []
#     for i in range(len(BODY_PARTS)):
#         heatMap = out[0, i, :, :]
#
#         _, conf, _, point = cv.minMaxLoc(heatMap)
#         x = int((frameWidth * point[0]) / out.shape[3])
#         y = int((frameHeight * point[1]) / out.shape[2])
#
#         if conf > threshold:
#             cv.circle(frame, (x, y), 3, (0, 255, 255), thickness=-1, lineType=cv.FILLED)
#             cv.putText(frame, "{}".format(i), (x, y), cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1, lineType=cv.LINE_AA)
#             points.append((x, y))
#         else:
#             points.append(None)
#
#     for pair in POSE_PAIRS:
#         partFrom = pair[0]
#         partTo = pair[1]
#
#         idFrom = BODY_PARTS[partFrom]
#         idTo = BODY_PARTS[partTo]
#
#         if points[idFrom] and points[idTo]:
#             cv.line(frame, points[idFrom], points[idTo], (0, 255, 0), 1)
#
#     t, _ = net.getPerfProfile()
#     freq = cv.getTickFrequency() / 1000
#     cv.putText(frame, '%.2fms' % (t / freq), (10, 20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0))
#
#     cv.imshow('OpenPose using OpenCV', frame)