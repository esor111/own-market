# 🎨 Advanced Hand Gesture Control System

An interactive two-handed gesture control system using Python, OpenCV, and MediaPipe with cool visual effects!

## Features

### 🖐️ Two-Hand Detection
- Detects and tracks both hands simultaneously
- Shows distance between hands in real-time
- Different colors for each hand

### 🎯 Gesture Recognition
- **Pinch** (👌): Draw or create particles
- **Fist** (✊): Clear all drawings
- **Peace Sign** (✌️): Recognition demo
- **Open Hand** (🖐️): Idle state

### 🎨 Interactive Modes
1. **Draw Mode**: Create colorful trails by pinching
2. **Particle Mode**: Generate particle explosions with physics

### 🔘 Virtual Buttons
- Press buttons by pinching near them
- Clear, Particles, and Draw mode buttons
- Visual feedback on interaction

### ✨ Visual Effects
- Smooth drawing trails with thickness variation
- Particle system with random colors and physics
- Real-time FPS counter
- Hand skeleton overlay with custom colors

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Controls

- **Pinch gesture**: Draw/create particles (bring thumb and index finger together)
- **Fist gesture**: Clear the canvas
- **Press 'q'**: Quit the application

## How to Use

1. Show both hands to the camera
2. Make a pinch gesture to start drawing
3. Use virtual buttons at the top to switch modes
4. Make a fist to clear everything
5. Have fun experimenting!

## Next Steps for React Integration

1. **REST API**: Create a Flask/FastAPI server to expose gesture data
2. **WebSocket**: Real-time gesture streaming to React frontend
3. **Electron**: Package as desktop app with React UI
4. **WebRTC**: Stream video and gestures directly to browser
