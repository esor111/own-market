import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import math
import time
from filters import AdaptiveFilter


class ProfessionalUIController:
    def __init__(self, screen_width=1920, screen_height=1080):
        self.mp_hands = mp.solutions.hands
        # Use model_complexity=1 for best balance
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=1,
            min_detection_confidence=0.85,
            min_tracking_confidence=0.85
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Screen dimensions
        self.screen_w = screen_width
        self.screen_h = screen_height
        
        # Professional adaptive filter
        self.filter = AdaptiveFilter()
        
        # Control settings
        self.control_pad_normal = 80
        self.control_pad_precision = 150
        self.current_pad = self.control_pad_normal
        
        # Click detection
        self.click_threshold = 0.028  # Very tight for precision
        self.pinch_hold_time = 0.12  # Faster response
        self.click_cooldown = 0.2
        
        # State
        self.precision_mode = False
        self.was_pinched = False
        self.pinch_start_time = 0.0
        self.last_click_time = 0.0
        self.freeze_cursor = False
        self.frozen_x = None
        self.frozen_y = None
        
        # Stability
        self.min_stable_frames = 3
        self.stable_count = 0
        self.hand_scale = 1.0
        
        # PyAutoGUI settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.0
    
    def clamp(self, v, lo, hi):
        return max(lo, min(hi, v))
    
    def calculate_hand_scale(self, landmarks):
        """Calculate hand scale for normalization"""
        wrist = landmarks[0]
        middle_mcp = landmarks[9]
        scale = math.sqrt(
            (wrist.x - middle_mcp.x)**2 + 
            (wrist.y - middle_mcp.y)**2 + 
            (wrist.z - middle_mcp.z)**2
        )
        return max(0.01, scale)
    
    def get_finger_distance(self, p1, p2):
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)
    
    def is_finger_up(self, landmarks, tip_id, pip_id):
        return landmarks[tip_id].y < landmarks[pip_id].y
    
    def detect_precision_mode(self, hand_landmarks):
        """Index + middle up = precision mode"""
        landmarks = hand_landmarks.landmark
        index_up = self.is_finger_up(landmarks, 8, 6)
        middle_up = self.is_finger_up(landmarks, 12, 10)
        ring_down = not self.is_finger_up(landmarks, 16, 14)
        return index_up and middle_up and ring_down
    
    def detect_pinch(self, hand_landmarks):
        """Detect pinch with normalized threshold"""
        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]
        distance = self.get_finger_distance(thumb_tip, index_tip)
        normalized = distance / self.hand_scale
        return normalized < self.click_threshold
    
    def map_to_screen(self, x_norm, y_norm):
        """Map with control rectangle"""
        pad_ratio = self.current_pad / 640.0
        
        x_clamped = self.clamp(x_norm, pad_ratio, 1.0 - pad_ratio)
        y_clamped = self.clamp(y_norm, pad_ratio, 1.0 - pad_ratio)
        
        x_remapped = (x_clamped - pad_ratio) / (1.0 - 2 * pad_ratio)
        y_remapped = (y_clamped - pad_ratio) / (1.0 - 2 * pad_ratio)
        
        screen_x = x_remapped * self.screen_w
        screen_y = y_remapped * self.screen_h
        
        # Apply professional adaptive filter
        filtered_x, filtered_y = self.filter.filter(screen_x, screen_y)
        
        return int(filtered_x), int(filtered_y)
    
    def reset_smoothing(self):
        self.filter.reset()
        self.stable_count = 0
        self.freeze_cursor = False
        self.frozen_x = None
        self.frozen_y = None
    
    def process_frame(self, frame):
        """Process with professional filtering"""
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        status = "No hand detected"
        
        if not results.multi_hand_landmarks:
            self.reset_smoothing()
            return frame, status
        
        self.stable_count = min(self.min_stable_frames, self.stable_count + 1)
        
        if self.stable_count < self.min_stable_frames:
            return frame, "Stabilizing..."
        
        hand_landmarks = results.multi_hand_landmarks[0]
        self.hand_scale = self.calculate_hand_scale(hand_landmarks.landmark)
        
        # Detect precision mode
        self.precision_mode = self.detect_precision_mode(hand_landmarks)
        self.current_pad = self.control_pad_precision if self.precision_mode else self.control_pad_normal
        
        # Draw skeleton
        color = (255, 0, 255) if self.precision_mode else (0, 255, 0)
        self.mp_draw.draw_landmarks(
            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
            self.mp_draw.DrawingSpec(color=color, thickness=2, circle_radius=3),
            self.mp_draw.DrawingSpec(color=color, thickness=2)
        )
        
        # Get finger position
        index_tip = hand_landmarks.landmark[8]
        finger_x, finger_y = index_tip.x, index_tip.y
        
        # Detect pinch
        is_pinched = self.detect_pinch(hand_landmarks)
        current_time = time.time()
        
        if is_pinched:
            if not self.was_pinched:
                self.pinch_start_time = current_time
                self.was_pinched = True
                
                # Freeze cursor
                if not self.freeze_cursor:
                    screen_x, screen_y = self.map_to_screen(finger_x, finger_y)
                    self.frozen_x = screen_x
                    self.frozen_y = screen_y
                    self.freeze_cursor = True
                
                status = "👌 Hold..."
            else:
                hold_duration = current_time - self.pinch_start_time
                
                if hold_duration >= self.pinch_hold_time:
                    if (current_time - self.last_click_time) > self.click_cooldown:
                        # Click at frozen position
                        pyautogui.click(self.frozen_x, self.frozen_y)
                        status = "🎯 CLICKED!"
                        self.last_click_time = current_time
                        
                        # Visual feedback
                        finger_px = (int(finger_x * w), int(finger_y * h))
                        cv2.circle(frame, finger_px, 60, (0, 255, 0), 6)
                    else:
                        status = "⏳ Cooldown..."
                else:
                    remaining = self.pinch_hold_time - hold_duration
                    status = f"👌 {remaining:.2f}s"
        else:
            self.was_pinched = False
            self.freeze_cursor = False
            
            # Normal movement with professional filtering
            screen_x, screen_y = self.map_to_screen(finger_x, finger_y)
            pyautogui.moveTo(screen_x, screen_y, duration=0)
            
            mode_text = "🎯 PRECISION" if self.precision_mode else "⚡ NORMAL"
            status = f"{mode_text} ({screen_x}, {screen_y})"
        
        # Keep cursor frozen during pinch
        if self.freeze_cursor and self.frozen_x is not None:
            pyautogui.moveTo(self.frozen_x, self.frozen_y, duration=0)
            
            # Draw precise crosshair
            frozen_px = (int(self.frozen_x * w / self.screen_w), 
                        int(self.frozen_y * h / self.screen_h))
            
            # Large crosshair
            cv2.drawMarker(frame, frozen_px, (0, 255, 0), 
                          cv2.MARKER_CROSS, 50, 4)
            # Small center dot
            cv2.circle(frame, frozen_px, 3, (0, 0, 255), -1)
        
        # Draw control rectangle
        pad = self.current_pad
        rect_color = (255, 0, 255) if self.precision_mode else (0, 255, 255)
        cv2.rectangle(frame, (pad, pad), (w - pad, h - pad), rect_color, 2)
        
        zone_text = "🎯 PRECISION ZONE" if self.precision_mode else "⚡ Control Zone"
        cv2.putText(frame, zone_text, (pad + 5, pad + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, rect_color, 2)
        
        # Draw cursor indicator
        finger_px = (int(finger_x * w), int(finger_y * h))
        cursor_color = (255, 0, 255) if self.precision_mode else (0, 255, 0)
        cv2.circle(frame, finger_px, 8, cursor_color, -1)
        cv2.circle(frame, finger_px, 12, (255, 255, 255), 2)
        
        # Draw pinch line
        if is_pinched:
            thumb_tip = hand_landmarks.landmark[4]
            thumb_px = (int(thumb_tip.x * w), int(thumb_tip.y * h))
            cv2.line(frame, finger_px, thumb_px, (0, 255, 0), 3)
        
        return frame, status
    
    def release(self):
        self.hands.close()
