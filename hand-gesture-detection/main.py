import cv2
from hand_gesture_detector import HandGestureDetector

def main():
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    # Set higher resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Initialize gesture detector
    detector = HandGestureDetector()
    
    print("🎨 Advanced Hand Gesture Control Started!")
    print("=" * 50)
    print("Gestures:")
    print("  👌 PINCH - Draw or create particles")
    print("  ✊ FIST - Clear drawing")
    print("  ✌️  PEACE - Just for fun!")
    print("  🖐️  OPEN - Idle state")
    print("\nButtons:")
    print("  🔴 Clear - Clear all drawings")
    print("  🟣 Particles - Switch to particle mode")
    print("  🟢 Draw - Switch to drawing mode")
    print("\nPress 'q' to quit")
    print("=" * 50)
    
    fps_counter = 0
    fps_display = 0
    import time
    start_time = time.time()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame")
            break
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Process frame and detect gestures
        processed_frame, gesture = detector.process_frame(frame)
        
        # Calculate FPS
        fps_counter += 1
        if time.time() - start_time > 1:
            fps_display = fps_counter
            fps_counter = 0
            start_time = time.time()
        
        # Create info panel
        h, w, _ = processed_frame.shape
        cv2.rectangle(processed_frame, (0, 0), (w, 150), (0, 0, 0), -1)
        cv2.rectangle(processed_frame, (0, 0), (w, 150), (255, 255, 255), 2)
        
        # Display gesture text
        cv2.putText(
            processed_frame, 
            gesture, 
            (10, 40), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7, 
            (0, 255, 255), 
            2
        )
        
        # Display mode
        mode_text = f"Mode: {detector.mode.upper()}"
        cv2.putText(
            processed_frame,
            mode_text,
            (10, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )
        
        # Display FPS
        cv2.putText(
            processed_frame,
            f"FPS: {fps_display}",
            (w - 120, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )
        
        # Display instructions
        cv2.putText(
            processed_frame,
            "Press 'q' to quit | Use PINCH to interact",
            (10, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1
        )
        
        # Show frame
        cv2.imshow('🎨 Advanced Hand Gesture Control', processed_frame)
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    detector.release()
    cap.release()
    cv2.destroyAllWindows()
    print("\n✅ Application closed successfully!")

if __name__ == "__main__":
    main()
