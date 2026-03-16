import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import math
import time

class UIAutomationController:
    def __init__(self, screen_width=1920, screen_height=1080):
        self.mp_hands = mp.solutions.hands
        # Use model_complexity=0 for maximum speed (3x faster)
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=0,  # Fastest model
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Screen dimensions
        self.screen_w = screen_width
        self.screen_h = screen_height
        
        # Control rectangle padding (smaller = more sensitive)
        self.control_pad = 100
        
        # EMA smoothing (lower = smoother but more lag)
        self.alpha = 0.25
        self.smooth_x = None
        self.smooth_y = None
        
        # Pinch detection with normalized thresholds
        self.click_threshold_ratio = 0.35  # Ratio of hand scale
        self.was_pinched = False
        self.last_click_time = 0.0
        self.click_cooldown = 0.3  # seconds
        
        # Frame stability
        self.min_stable_frames = 2
        self.stable_count = 0
        
        # Hand scale for normalization
        self.hand_scale = 1.0
        
        # PyAutoGUI settings
        pyautogui.FAILSAFE = True  # Move to corner to abort
        pyautogui.PAUSE = 0.0  # No delay between commands
        
    
    def clamp(self, v, lo, hi):
        """Clamp value between lo and hi"""
        return max(lo, min(hi, v))
    
    def calculate_hand_scale(self, landmarks):
        """Calculate hand scale for normalized thresholds"""
        wrist = landmarks[0]
        index_mcp = landmarks[5]
        # Distance from wrist to index MCP as scale reference
        scale = math.sqrt(
            (wrist.x - index_mcp.x)**2 + 
            (wrist.y - index_mcp.y)**2 + 
            (wrist.z - index_mcp.z)**2
        )
        return max(0.01, scale)  # Avoid division by zero
    
    def get_finger_distance(self, p1, p2):
        """Calculate 3D distance between two landmarks"""
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)
    
    
    def detect_pinch(self, hand_landmarks):
        """Detect pinch gesture with normalized threshold"""
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        
        # Calculate distance
        distance = self.get_finger_distance(thumb_tip, index_tip)
        
        # Normalize by hand scale
        normalized_distance = distance / self.hand_scale
        
        return normalized_distance < self.click_threshold_ratio
    
    def map_to_screen(self, x_norm, y_norm):
        """Map normalized coordinates to screen with control rectangle"""
        # x_norm, y_norm are in [0, 1] range
        
        # Apply control rectangle padding
        # This creates a smaller active area for better precision
        pad_ratio = self.control_pad / 640.0  # Assuming 640px width
        
        # Clamp to control region
        x_clamped = self.clamp(x_norm, pad_ratio, 1.0 - pad_ratio)
        y_clamped = self.clamp(y_norm, pad_ratio, 1.0 - pad_ratio)
        
        # Remap to [0, 1]
        x_remapped = (x_clamped - pad_ratio) / (1.0 - 2 * pad_ratio)
        y_remapped = (y_clamped - pad_ratio) / (1.0 - 2 * pad_ratio)
        
        # Map to screen
        screen_x = x_remapped * self.screen_w
        screen_y = y_remapped * self.screen_h
        
        # Apply EMA smoothing
        if self.smooth_x is None:
            self.smooth_x = screen_x
            self.smooth_y = screen_y
        else:
            self.smooth_x = self.alpha * screen_x + (1.0 - self.alpha) * self.smooth_x
            self.smooth_y = self.alpha * screen_y + (1.0 - self.alpha) * self.smooth_y
        
        return int(self.smooth_x), int(self.smooth_y)
    
    
    def get_index_finger_pos(self, hand_landmarks):
        """Get index finger tip position in normalized coordinates"""
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        return index_tip.x, index_tip.y
    
    def reset_smoothing(self):
        """Reset smoothing when tracking is lost"""
        self.smooth_x = None
        self.smooth_y = None
        self.stable_count = 0
    
    def process_frame(self, frame):
        """Process frame and control UI with optimized precision"""
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        status = "No hand detected"
        
        # Check if hand is detected
        if not results.multi_hand_landmarks:
            self.reset_smoothing()
            return frame, status
        
        # Increment stability counter
        self.stable_count = min(self.min_stable_frames, self.stable_count + 1)
        
        # Only process if stable
        if self.stable_count < self.min_stable_frames:
            return frame, "Stabilizing..."
        
        hand_landmarks = results.multi_hand_landmarks[0]
        
        # Calculate hand scale for normalized thresholds
        self.hand_scale = self.calculate_hand_scale(hand_landmarks.landmark)
        
        # Draw hand skeleton with high-contrast color
        self.mp_draw.draw_landmarks(
            frame, 
            hand_landmarks, 
            self.mp_hands.HAND_CONNECTIONS,
            self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
            self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2)
        )
        
        # Get index finger position (normalized)
        finger_x, finger_y = self.get_index_finger_pos(hand_landmarks)
        
        # Map to screen coordinates with control rectangle
        screen_x, screen_y = self.map_to_screen(finger_x, finger_y)
        
        # Move cursor
        pyautogui.moveTo(screen_x, screen_y, duration=0)
        
        # Detect pinch for clicking
        is_pinched = self.detect_pinch(hand_landmarks)
        current_time = time.time()
        
        # Handle click with cooldown
        if is_pinched and not self.was_pinched:
            if (current_time - self.last_click_time) > self.click_cooldown:
                pyautogui.click()
                status = "🖱️ CLICKED!"
                self.last_click_time = current_time
                
                # Visual feedback
                finger_px = (int(finger_x * w), int(finger_y * h))
                cv2.circle(frame, finger_px, 40, (0, 0, 255), 4)
            else:
                status = "⏳ Cooldown..."
        elif is_pinched:
            status = "👌 Pinching..."
        else:
            status = f"✋ Moving ({screen_x}, {screen_y})"
        
        self.was_pinched = is_pinched
        
        # Draw control rectangle
        pad = self.control_pad
        cv2.rectangle(frame, (pad, pad), (w - pad, h - pad), (0, 255, 255), 2)
        cv2.putText(frame, "Control Zone", (pad + 5, pad + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # Draw cursor indicator
        finger_px = (int(finger_x * w), int(finger_y * h))
        cv2.circle(frame, finger_px, 12, (0, 255, 0), -1)
        cv2.circle(frame, finger_px, 15, (255, 255, 255), 2)
        
        # Draw pinch distance indicator
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        thumb_px = (int(thumb_tip.x * w), int(thumb_tip.y * h))
        if is_pinched:
            cv2.line(frame, finger_px, thumb_px, (0, 0, 255), 2)
        
        return frame, status
    
    def release(self):
        """Release resources"""
        self.hands.close()
