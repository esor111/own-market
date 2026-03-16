import cv2
import mediapipe as mp
import numpy as np
import math
from collections import deque

class HandGestureDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,  # Detect both hands
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.drawing_points = deque(maxlen=512)
        self.particles = []
        self.virtual_buttons = [
            {"pos": (100, 100), "size": 80, "label": "Clear", "color": (0, 0, 255)},
            {"pos": (250, 100), "size": 80, "label": "Particles", "color": (255, 0, 255)},
            {"pos": (400, 100), "size": 80, "label": "Draw", "color": (0, 255, 0)}
        ]
        self.mode = "draw"
        
    def get_finger_distance(self, p1, p2):
        """Calculate distance between two points"""
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)
    
    def detect_pinch(self, hand_landmarks):
        """Detect pinch gesture (thumb and index finger close)"""
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        distance = self.get_finger_distance(thumb_tip, index_tip)
        return distance < 0.05
    
    def detect_fist(self, hand_landmarks):
        """Detect closed fist"""
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        fingertips = [
            hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP],
            hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
            hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP],
            hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        ]
        
        # All fingertips should be close to wrist
        all_closed = all(self.get_finger_distance(tip, wrist) < 0.15 for tip in fingertips)
        return all_closed
    
    def detect_peace_sign(self, hand_landmarks):
        """Detect peace sign (index and middle finger up)"""
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        ring_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP]
        pinky_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        
        index_up = index_tip.y < wrist.y
        middle_up = middle_tip.y < wrist.y
        ring_down = ring_tip.y > wrist.y
        pinky_down = pinky_tip.y > wrist.y
        
        return index_up and middle_up and ring_down and pinky_down
    
    def get_index_finger_pos(self, hand_landmarks, frame_shape):
        """Get index finger tip position in pixel coordinates"""
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        h, w, _ = frame_shape
        return (int(index_tip.x * w), int(index_tip.y * h))
    
    def check_button_press(self, pos, hand_landmarks, frame_shape):
        """Check if finger is pressing a virtual button"""
        finger_pos = self.get_index_finger_pos(hand_landmarks, frame_shape)
        
        for button in self.virtual_buttons:
            bx, by = button["pos"]
            size = button["size"]
            if (bx - size//2 < finger_pos[0] < bx + size//2 and 
                by - size//2 < finger_pos[1] < by + size//2):
                return button["label"]
        return None
    
    def process_frame(self, frame):
        """Process a single frame and detect gestures"""
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        gestures = []
        hand_positions = []
        
        # Draw virtual buttons
        for button in self.virtual_buttons:
            bx, by = button["pos"]
            size = button["size"]
            cv2.circle(frame, (bx, by), size//2, button["color"], -1)
            cv2.circle(frame, (bx, by), size//2, (255, 255, 255), 3)
            cv2.putText(frame, button["label"], (bx - 30, by + 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        if results.multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # Draw hand skeleton with cool colors
                color = (0, 255, 255) if idx == 0 else (255, 0, 255)
                self.mp_draw.draw_landmarks(
                    frame, 
                    hand_landmarks, 
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_draw.DrawingSpec(color=color, thickness=2, circle_radius=4),
                    self.mp_draw.DrawingSpec(color=color, thickness=2)
                )
                
                # Get finger position
                finger_pos = self.get_index_finger_pos(hand_landmarks, frame.shape)
                hand_positions.append(finger_pos)
                
                # Check button press with pinch
                if self.detect_pinch(hand_landmarks):
                    button = self.check_button_press(finger_pos, hand_landmarks, frame.shape)
                    if button == "Clear":
                        self.drawing_points.clear()
                        self.particles.clear()
                        gestures.append("CLEARED!")
                    elif button == "Particles":
                        self.mode = "particles"
                        gestures.append("Particle Mode")
                    elif button == "Draw":
                        self.mode = "draw"
                        gestures.append("Draw Mode")
                    else:
                        gestures.append(f"Hand {idx+1}: PINCH")
                        
                        # Add to drawing or particles
                        if self.mode == "draw":
                            self.drawing_points.append(finger_pos)
                        elif self.mode == "particles":
                            for _ in range(5):
                                self.particles.append({
                                    "pos": list(finger_pos),
                                    "vel": [np.random.randint(-5, 5), np.random.randint(-5, 5)],
                                    "life": 30,
                                    "color": tuple(np.random.randint(0, 255, 3).tolist())
                                })
                
                elif self.detect_fist(hand_landmarks):
                    gestures.append(f"Hand {idx+1}: FIST")
                    self.drawing_points.clear()
                
                elif self.detect_peace_sign(hand_landmarks):
                    gestures.append(f"Hand {idx+1}: PEACE ✌")
                
                else:
                    gestures.append(f"Hand {idx+1}: Open")
                
                # Draw finger pointer
                cv2.circle(frame, finger_pos, 10, (0, 255, 0), -1)
        
        # Draw the trail
        for i in range(1, len(self.drawing_points)):
            if self.drawing_points[i-1] is None or self.drawing_points[i] is None:
                continue
            thickness = int(np.sqrt(len(self.drawing_points) / float(i + 1)) * 4)
            cv2.line(frame, self.drawing_points[i-1], self.drawing_points[i], 
                    (0, 255, 255), thickness)
        
        # Update and draw particles
        particles_to_remove = []
        for particle in self.particles:
            particle["pos"][0] += particle["vel"][0]
            particle["pos"][1] += particle["vel"][1]
            particle["life"] -= 1
            
            if particle["life"] <= 0:
                particles_to_remove.append(particle)
            else:
                cv2.circle(frame, tuple(map(int, particle["pos"])), 
                          5, particle["color"], -1)
        
        for p in particles_to_remove:
            self.particles.remove(p)
        
        # Draw distance between two hands
        if len(hand_positions) == 2:
            cv2.line(frame, hand_positions[0], hand_positions[1], (255, 255, 0), 2)
            distance = math.sqrt((hand_positions[0][0] - hand_positions[1][0])**2 + 
                               (hand_positions[0][1] - hand_positions[1][1])**2)
            mid_point = ((hand_positions[0][0] + hand_positions[1][0])//2,
                        (hand_positions[0][1] + hand_positions[1][1])//2)
            cv2.putText(frame, f"{int(distance)}px", mid_point,
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        gesture_text = " | ".join(gestures) if gestures else "No hands detected"
        return frame, gesture_text
    
    def release(self):
        """Release resources"""
        self.hands.close()
