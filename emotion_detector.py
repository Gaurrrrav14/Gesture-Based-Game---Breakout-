# emotion_detector.py

from fer import FER
import cv2

class EmotionDetector:
    def __init__(self):
        self.detector = FER(mtcnn=False)

    def detect_emotion(self, frame):
        # Convert frame to RGB for FER
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.detector.top_emotion(rgb_frame)
        return result  # either None or (emotion, score)
