import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import math
import time

class UIAutomationController:
    def __init__(self, screen_width=1920, screen_height=1080):
        self.mp_hands = mp.solutions.hands
        # Use model_complexity=1 for better accuracy (compromise between 0 and 2)
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=1,  # Better accuracy than 0
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Screen dimensions
        self.screen_w = screen_width
        self.screen_h = screen_height
        
        # Control rectangle padding
        self.control_pad = 120
        
        # Adaptive smoothing
        self.alpha_normal = 0.4  # Normal mode (more responsive)
        self.alpha_precision = 0.15  # Precision mode (more stable)
        self.current_alpha = self.alpha_normal
        self.smooth_x = None
        self.smooth_y = None
        
        # Deadzone to eliminate micro-jitter
        self.deadzone_pixels = 3
        self.last_sent_x = None
        self.last_sent_y = None
        
        # Pinch detection
        self.click_threshold_ratio = 0.30
        self.precision_threshold_ratio = 0.25  # Tighter for precision mode
        self.was_pinched = False
        self.pinch_start_time = 0.0
        self.pinch_hold_time = 0.15  # Hold pinch for this long before click
        self.last_click_time = 0.0
        self.click_cooldown = 0.25
        
        # Precision mode detection (middle finger up = precision mode)
        self.precision_mode = False
        
        # Cursor freeze during click
        self.freeze_cursor = False
        self.frozen_x = None
        self.frozen_y = None
        
        # Frame stability
        self.min_stable_frames = 3
        self.stable_count = 0
        
        # Hand scale
        self.hand_scale = 1.0
        
        # PyAutoGUI settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.0
        
    
    def clamp(self, v, lo, hi):
        """Clamp value between lo and hi"""
        return max(lo, min(hi, v))
    
    def calculate_hand_scale(self, landmarks):
        """Calculate hand scale for normalized thresholds"""
        wrist = landmarks[0]
        index_mcp = landmarks[5]
        scale = math.sqrt(
            (wrist.x - index_mcp.x)**2 + 
            (wrist.y - index_mcp.y)**2 + 
            (wrist.z - index_mcp.z)**2
        )
        return max(0.01, scale)
    
    def get_finger_distance(self, p1, p2):
        """Calculate 3D distance between two landmarks"""
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)
    
    def is_finger_up(self, landmarks, finger_tip_id, finger_pip_id):
        """Check if a finger is extended"""
        return landmarks[finger_tip_id].y < landmarks[finger_pip_id].y
    
    
    def detect_precision_mode(self, hand_landmarks):
        """Detect precision mode: index + middle finger up"""
        landmarks = hand_landmarks.landmark
        index_up = self.is_finger_up(landmarks, 8, 6)
        middle_up = self.is_finger_up(landmarks, 12, 10)
        ring_down = not self.is_finger_up(landmarks, 16, 14)
        
        return index_up and middle_up and ring_down
    
    def detect_pinch(self, hand_landmarks):
        """Detect pinch gesture with adaptive threshold"""
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        
        distance = self.get_finger_distance(thumb_tip, index_tip)
        normalized_distance = distance / self.hand_scale
        
        # Use tighter threshold in precision mode
        threshold = self.precision_threshold_ratio if self.precision_mode else self.click_threshold_ratio
        
        return normalized_distance < threshold
    
    def map_to_screen(self, x_norm, y_norm):
        """Map normalized coordinates to screen with control rectangle and deadzone"""
        # Apply control rectangle padding
        pad_ratio = self.control_pad / 640.0
        
        x_clamped = self.clamp(x_norm, pad_ratio, 1.0 - pad_ratio)
        y_clamped = self.clamp(y_norm, pad_ratio, 1.0 - pad_ratio)
        
        x_remapped = (x_clamped - pad_ratio) / (1.0 - 2 * pad_ratio)
        y_remapped = (y_clamped - pad_ratio) / (1.0 - 2 * pad_ratio)
        
        screen_x = x_remapped * self.screen_w
        screen_y = y_remapped * self.screen_h
        
        # Apply EMA smoothing with adaptive alpha
        if self.smooth_x is None:
            self.smooth_x = screen_x
            self.smooth_y = screen_y
        else:
            self.smooth_x = self.current_alpha * screen_x + (1.0 - self.current_alpha) * self.smooth_x
            self.smooth_y = self.current_alpha * screen_y + (1.0 - self.current_alpha) * self.smooth_y
        
        final_x = int(self.smooth_x)
        final_y = int(self.smooth_y)
        
        # Apply deadzone to eliminate micro-jitter
        if self.last_sent_x is not None:
            dx = abs(final_x - self.last_sent_x)
            dy = abs(final_y - self.last_sent_y)
            
            if dx < self.deadzone_pixels and dy < self.deadzone_pixels:
                # Movement too small, use last position
                return self.last_sent_x, self.last_sent_y
        
        self.last_sent_x = final_x
        self.last_sent_y = final_y
        
        return final_x, final_y
    
    
    def get_index_finger_pos(self, hand_landmarks):
        """Get index finger tip position in normalized coordinates"""
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        return index_tip.x, index_tip.y
    
    def reset_smoothing(self):
        """Reset smoothing when tracking is lost"""
        self.smooth_x = None
        self.smooth_y = None
        self.stable_count = 0
        self.last_sent_x = None
        self.last_sent_y = None
        self.freeze_cursor = False
        self.frozen_x = None
        self.frozen_y = None
    
    def process_frame(self, frame):
        """Process frame with precision mode and cursor freeze"""
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        status = "No hand detected"
        
        if not results.multi_hand_landmarks:
            self.reset_smoothing()
            self.freeze_cursor = False
            return frame, status
        
        self.stable_count = min(self.min_stable_frames, self.stable_count + 1)
        
        if self.stable_count < self.min_stable_frames:
            return frame, "Stabilizing..."
        
        hand_landmarks = results.multi_hand_landmarks[0]
        self.hand_scale = self.calculate_hand_scale(hand_landmarks.landmark)
        
        # Detect precision mode (index + middle up)
        self.precision_mode = self.detect_precision_mode(hand_landmarks)
        
        # Adjust smoothing based on mode
        if self.precision_mode:
            self.current_alpha = self.alpha_precision
            self.control_pad = 140  # Larger pad = more precision
        else:
            self.current_alpha = self.alpha_normal
            self.control_pad = 100
        
        # Draw hand skeleton
        color = (255, 0, 255) if self.precision_mode else (0, 255, 0)
        self.mp_draw.draw_landmarks(
            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
            self.mp_draw.DrawingSpec(color=color, thickness=2, circle_radius=3),
            self.mp_draw.DrawingSpec(color=color, thickness=2)
        )
        
        # Get finger position
        finger_x, finger_y = self.get_index_finger_pos(hand_landmarks)
        
        # Detect pinch
        is_pinched = self.detect_pinch(hand_landmarks)
        current_time = time.time()
        
        # Handle pinch with hold time
        if is_pinched:
            if not self.was_pinched:
                # Start pinch
                self.pinch_start_time = current_time
                self.was_pinched = True
                
                # Freeze cursor at current position
                if not self.freeze_cursor:
                    screen_x, screen_y = self.map_to_screen(finger_x, finger_y)
                    self.frozen_x = screen_x
                    self.frozen_y = screen_y
                    self.freeze_cursor = True
                
                status = "👌 Hold pinch..."
            else:
                # Check if held long enough
                hold_duration = current_time - self.pinch_start_time
                
                if hold_duration >= self.pinch_hold_time:
                    # Check cooldown
                    if (current_time - self.last_click_time) > self.click_cooldown:
                        # Perform click at frozen position
                        pyautogui.click(self.frozen_x, self.frozen_y)
                        status = "🖱️ CLICKED!"
                        self.last_click_time = current_time
                        
                        # Visual feedback
                        finger_px = (int(finger_x * w), int(finger_y * h))
                        cv2.circle(frame, finger_px, 50, (0, 0, 255), 5)
                    else:
                        status = "⏳ Cooldown..."
                else:
                    # Still holding
                    remaining = self.pinch_hold_time - hold_duration
                    status = f"👌 Hold {remaining:.2f}s..."
        else:
            # Released pinch
            self.was_pinched = False
            self.freeze_cursor = False
            self.pinch_start_time = 0.0
            
            # Normal cursor movement
            screen_x, screen_y = self.map_to_screen(finger_x, finger_y)
            pyautogui.moveTo(screen_x, screen_y, duration=0)
            
            mode_text = "PRECISION" if self.precision_mode else "NORMAL"
            status = f"✋ {mode_text} ({screen_x}, {screen_y})"
        
        # If cursor is frozen, keep it at frozen position
        if self.freeze_cursor and self.frozen_x is not None:
            pyautogui.moveTo(self.frozen_x, self.frozen_y, duration=0)
            
            # Draw crosshair at frozen position
            frozen_px = (int(self.frozen_x * w / self.screen_w), 
                        int(self.frozen_y * h / self.screen_h))
            cv2.drawMarker(frame, frozen_px, (0, 0, 255), 
                          cv2.MARKER_CROSS, 40, 3)
        
        # Draw control rectangle
        pad = self.control_pad
        rect_color = (255, 0, 255) if self.precision_mode else (0, 255, 255)
        cv2.rectangle(frame, (pad, pad), (w - pad, h - pad), rect_color, 2)
        
        zone_text = "PRECISION ZONE" if self.precision_mode else "Control Zone"
        cv2.putText(frame, zone_text, (pad + 5, pad + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, rect_color, 2)
        
        # Draw cursor indicator
        finger_px = (int(finger_x * w), int(finger_y * h))
        cursor_color = (255, 0, 255) if self.precision_mode else (0, 255, 0)
        cv2.circle(frame, finger_px, 10, cursor_color, -1)
        cv2.circle(frame, finger_px, 13, (255, 255, 255), 2)
        
        # Draw pinch indicator
        if is_pinched:
            thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
            thumb_px = (int(thumb_tip.x * w), int(thumb_tip.y * h))
            cv2.line(frame, finger_px, thumb_px, (0, 0, 255), 3)
        
        return frame, status
    
    def release(self):
        """Release resources"""
        self.hands.close()
