import cv2
from ui_automation_pro import ProfessionalUIController
import pyautogui
import time

def main():
    screen_w, screen_h = pyautogui.size()
    print(f"Screen resolution: {screen_w}x{screen_h}")
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    # Optimal settings
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 60)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
    
    controller = ProfessionalUIController(screen_w, screen_h)
    
    print("\n" + "="*75)
    print("🎯 PROFESSIONAL HAND GESTURE UI CONTROL")
    print("="*75)
    print("\n✨ ADVANCED FILTERING:")
    print("  • One Euro Filter: Velocity-adaptive smoothing")
    print("  • Kalman Filter: Predictive tracking with motion model")
    print("  • Multi-frame Averaging: Outlier rejection (drops 2 min/max)")
    print("  • Triple-stage pipeline: Average → Kalman → One Euro")
    print("\n🎯 PRECISION MODE:")
    print("  • Raise INDEX + MIDDLE finger together")
    print("  • Purple skeleton = precision active")
    print("  • Larger control zone (150px pad)")
    print("  • Perfect for small UI elements")
    print("\n🖱️  CLICK SYSTEM:")
    print("  • Pinch thumb + index finger")
    print("  • Cursor FREEZES at exact position")
    print("  • Hold 0.12s to click")
    print("  • Green crosshair shows target")
    print("  • 0.2s cooldown prevents double-clicks")
    print("\n📊 TECHNICAL SPECS:")
    print("  • Model Complexity: 1 (balanced)")
    print("  • Detection Confidence: 0.85")
    print("  • Tracking Confidence: 0.85")
    print("  • Click Threshold: 0.028 (very tight)")
    print("  • Frame Stability: 3 frames")
    print("\n⌨️  CONTROLS:")
    print("  ✋ INDEX ONLY = Normal mode")
    print("  ✌️  INDEX + MIDDLE = Precision mode")
    print("  👌 PINCH & HOLD = Click")
    print("  🛑 CORNER = Emergency abort")
    print("  ❌ Q = Quit")
    print("\n💡 PRO TIPS:")
    print("  • Good lighting is critical")
    print("  • Keep hand at consistent distance")
    print("  • Use precision mode for all small buttons")
    print("  • Pinch freezes cursor - no shake!")
    print("="*75 + "\n")
    
    cv2.namedWindow('Professional Hand Control', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Professional Hand Control', 640, 480)
    
    fps_counter = 0
    fps_display = 0
    start_time = time.time()
    frame_times = []
    
    while True:
        frame_start = time.time()
        
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        processed_frame, status = controller.process_frame(frame)
        
        # FPS calculation
        fps_counter += 1
        if time.time() - start_time > 1:
            fps_display = fps_counter
            fps_counter = 0
            start_time = time.time()
        
        # Frame time
        frame_time = (time.time() - frame_start) * 1000
        frame_times.append(frame_time)
        if len(frame_times) > 30:
            frame_times.pop(0)
        avg_frame_time = sum(frame_times) / len(frame_times)
        
        # Info overlay
        h, w, _ = processed_frame.shape
        overlay = processed_frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.8, processed_frame, 0.2, 0, processed_frame)
        
        # Status with color coding
        if "PRECISION" in status:
            color = (255, 0, 255)
        elif "CLICKED" in status:
            color = (0, 255, 0)
        elif "Hold" in status:
            color = (0, 255, 255)
        else:
            color = (255, 255, 255)
        
        cv2.putText(processed_frame, status, (10, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Performance metrics
        cv2.putText(processed_frame, f"FPS: {fps_display} | Latency: {avg_frame_time:.1f}ms", 
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
        
        # Filter info
        filter_text = "Filters: OneEuro + Kalman + Averaging"
        cv2.putText(processed_frame, filter_text, (10, 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 200, 255), 1)
        
        # Instructions
        cv2.putText(processed_frame, "INDEX+MIDDLE=Precision | PINCH=Click | Q=Quit",
                   (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        cv2.imshow('Professional Hand Control', processed_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    controller.release()
    cap.release()
    cv2.destroyAllWindows()
    
    print("\n✅ Professional UI Control stopped")
    print(f"📊 Final Stats:")
    print(f"   Average FPS: {fps_display}")
    print(f"   Average Latency: {avg_frame_time:.1f}ms")

if __name__ == "__main__":
    main()
