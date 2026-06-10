import cv2
import mediapipe as mp
import math

class ImprovedGestureDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.gesture_history = []
        
    def get_hand_openness(self, landmarks):
        palm_center = landmarks[9]
        total_distance = sum(
            math.sqrt((landmarks[tip][0] - palm_center[0])**2 + (landmarks[tip][1] - palm_center[1])**2)
            for tip in [4, 8, 12, 16, 20]
        )
        return min(total_distance, 0.8)
    
    def detect_pinch(self, landmarks):
        """Detect pinch gesture between thumb and index finger"""
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        distance = math.sqrt((thumb_tip[0] - index_tip[0])**2 + (thumb_tip[1] - index_tip[1])**2)
        return distance < 0.05  # Threshold for pinch detection
    
    def detect_gesture(self, frame):
        results = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        gesture = {'hand_x': 0.5, 'hand_y': 0.5, 'hand_state': 'none', 'detected': False, 'pinch': False}
        
        if results.multi_hand_landmarks:
            landmarks = [[lm.x, lm.y] for lm in results.multi_hand_landmarks[0].landmark]
            gesture['hand_x'] = landmarks[9][0]  # Palm center X
            gesture['hand_y'] = landmarks[9][1]  # Palm center Y
            openness = self.get_hand_openness(landmarks)
            
            # Count fingers
            fingers_up = 0
            if abs(landmarks[4][0] - landmarks[3][0]) > 0.03: fingers_up += 1  # Thumb
            for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
                if landmarks[tip][1] < landmarks[pip][1]: fingers_up += 1
            
            # Detect pinch FIRST and more strictly
            pinch_detected = self.detect_pinch(landmarks)
            
            # Determine gesture with improved logic
            if pinch_detected and fingers_up >= 2 and openness > 0.25:
                # Only pinch if hand is somewhat open and has multiple fingers
                gesture['hand_state'] = 'open'  # Treat as open for paddle movement
                gesture['pinch'] = True
            elif openness < 0.35 and fingers_up <= 2 and not pinch_detected:
                # More lenient fist detection: slightly higher openness and finger count
                # But still exclude pinch to avoid confusion
                gesture['hand_state'] = 'fist'
                gesture['pinch'] = False
            elif fingers_up == 2 and landmarks[8][1] < landmarks[6][1] and landmarks[12][1] < landmarks[10][1] and not pinch_detected:
                # Peace sign only if not pinching
                gesture['hand_state'] = 'peace'
                gesture['pinch'] = False
            elif openness > 0.45:
                gesture['hand_state'] = 'open'
                gesture['pinch'] = False
            else:
                gesture['hand_state'] = 'partial'
                gesture['pinch'] = False
            
            gesture['detected'] = True
            self.gesture_history.append(gesture['hand_state'])
            if len(self.gesture_history) > 5:  # Increased history for better stability
                self.gesture_history.pop(0)
            if len(self.gesture_history) >= 3:
                # Use majority voting for more stable gesture recognition
                gesture['hand_state'] = max(set(self.gesture_history), key=self.gesture_history.count)
            
            self.mp_draw.draw_landmarks(frame, results.multi_hand_landmarks[0], self.mp_hands.HAND_CONNECTIONS)
        
        return gesture, frame