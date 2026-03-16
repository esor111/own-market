import cv2
from ui_automation import UIAutomationController
import pyautogui
import time

def main():
    # Get screen size
    screen_w, screen_h = pyautogui.size()
    print(f"Screen resolution: {screen_w}x{screen_h}")
    
    # Initialize webcam with optimized settings
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    # Set optimal camera resolution (lower = faster)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 60)  # Request higher FPS
    
    # Disable auto-exposure if possible (reduces flicker)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
    
    # Initialize UI automation controller
    controller = UIAutomationController(screen_w, screen_h)
    
    print("\n" + "="*70)
    print("🎯 PRECISION HAND GESTURE UI AUTOMATION")
    print("="*70)
    print("\n📋 NEW FEATURES:")
    print("  🎯 PRECISION MODE: Raise index + middle finger")
    print("     • Slower, more stable cursor")
    print("     • Perfect for small buttons")
    print("     • Purple skeleton = precision mode active")
    print("\n  🖱️  CURSOR FREEZE: Pinch freezes cursor position")
    print("     • Hold pinch for 0.15s to click")
    print("     • Cursor won't move while pinching")
    print("     • Red crosshair shows click target")
    print("\n  ✨ ANTI-JITTER:")
    print("     • 3-pixel deadzone eliminates flicker")
    print("     • Adaptive smoothing per mode")
    print("     • Frame stability requirement")
    print("\n📋 Controls:")
    print("  ✋ INDEX FINGER ONLY = Normal cursor movement")
    print("  ✌️  INDEX + MIDDLE UP = Precision mode (slower, stable)")
    print("  👌 PINCH & HOLD 0.15s = Click at frozen position")
    print("  🛑 Move to CORNER = Emergency abort")
    print("  ❌ Press 'q' = Quit")
    print("\n💡 Tips:")
    print("  • Use precision mode for small UI elements")
    print("  • Pinch freezes cursor - no more shaky clicks!")
    print("  • Good lighting = better tracking")
    print("="*70 + "\n")
    
    # Create window
    cv2.namedWindow('Precision Hand Control', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Precision Hand Control', 640, 480)
    
    # FPS tracking
    fps_counter = 0
    fps_display = 0
    start_time = time.time()
    frame_times = []
    
    while True:
        frame_start = time.time()
        
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame")
            break
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Process frame and control UI
        processed_frame, status = controller.process_frame(frame)
        
        # Calculate FPS
        fps_counter += 1
        if time.time() - start_time > 1:
            fps_display = fps_counter
            fps_counter = 0
            start_time = time.time()
        
        # Calculate frame time
        frame_time = (time.time() - frame_start) * 1000
        frame_times.append(frame_time)
        if len(frame_times) > 30:
            frame_times.pop(0)
        avg_frame_time = sum(frame_times) / len(frame_times)
        
        # Create info overlay
        h, w, _ = processed_frame.shape
        overlay = processed_frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 140), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.75, processed_frame, 0.25, 0, processed_frame)
        
        # Display status with mode indicator
        if "PRECISION" in status:
            color = (255, 0, 255)
        elif "CLICKED" in status:
            color = (0, 255, 0)
        else:
            color = (255, 255, 255)
        
        cv2.putText(processed_frame, status, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
        
        # Display performance metrics
        cv2.putText(processed_frame, f"FPS: {fps_display}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.putText(processed_frame, f"Latency: {avg_frame_time:.1f}ms", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Display instructions
        mode_hint = "INDEX+MIDDLE=Precision | PINCH&HOLD=Click | Q=Quit"
        cv2.putText(processed_frame, mode_hint,
                   (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        # Show frame
        cv2.imshow('Precision Hand Control', processed_frame)
        
        # Check for quit
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    # Cleanup
    controller.release()
    cap.release()
    cv2.destroyAllWindows()
    print("\n✅ UI Automation stopped successfully!")
    print(f"📊 Average FPS: {fps_display}")
    print(f"📊 Average Latency: {avg_frame_time:.1f}ms")

if __name__ == "__main__":
    main()
