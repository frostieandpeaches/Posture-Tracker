import cv2
import os

def upscale_if_needed(path):
    cap = cv2.VideoCapture(path)
    ret, frame = cap.read()
    if not ret:
        cap.release()
        return path

    h, w = frame.shape[:2]
    cap.release()

    if w >= 720:
        return path

    new_path = path.replace(".mp4", "_upscaled.mp4")
    cap = cv2.VideoCapture(path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(new_path, fourcc, 30.0, (1280, 720))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (1280, 720))
        out.write(frame)

    cap.release()
    out.release()
    return new_path
