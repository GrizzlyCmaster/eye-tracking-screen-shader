# Eye Tracking Integration for ShaderGlass

This is a complete eye-tracking system for ShaderGlass that automatically positions a zoom/magnification effect based on where your eyes are looking.

## Components

1. **zoom-fisheye.slang / .slangp** - Shader with dynamic center position parameters
2. **eye_tracker.py** - Python application that detects eye gaze from your webcam
3. **EyeTrackingBridge.cs** - C# helper app to bridge eye tracking data to ShaderGlass

## Quick Setup

### 1. Install Python Dependencies

```bash
pip install opencv-python gaze-tracking
```

If you don't have Python installed, [download it here](https://www.python.org/downloads/) (Python 3.8+).

### 2. Prepare the Shader

Copy or import the shader in ShaderGlass:
- **Option A (Recommended)**: In ShaderGlass, use "Import custom..." and navigate to:
  - `ShaderGlass/Scripts/slang-shaders/custom/zoom-fisheye/zoom-fisheye.slangp`
- **Option B**: Copy files from `Misc/ZoomFisheye.slang` and `Misc/ZoomFisheye.slangp` to your custom shaders folder

### 3. Run the Eye Tracker

```bash
cd Misc
python eye_tracker.py
```

You should see:
- A window showing your webcam feed
- A **red circle** showing where the system thinks you're looking
- A **green crosshair** at center for reference
- Coordinates displayed (X: 0-1, Y: 0-1)

**Controls:**
- Press `Space` to show/hide the visualization (useful if it's distracting)
- Press `Q` to quit
- The app continuously writes gaze position to `eye_gaze.json`

### 4. Load the Shader in ShaderGlass

1. In ShaderGlass, import the zoom-fisheye preset
2. You should see parameter sliders for:
   - **ZoomStrength** - magnification intensity
   - **ZoomRadius** - how large the zoom area is
   - **ZoomFalloff** - smooth transition to edges
   - **CenterX** - horizontal zoom center (0.0 = left, 1.0 = right)
   - **CenterY** - vertical zoom center (0.0 = top, 1.0 = bottom)

### 5. (Optional) Use the Bridge App

For automatic parameter updates based on eye position:

1. Compile `EyeTrackingBridge.cs` into an executable (or run with `csc EyeTrackingBridge.cs`)
2. Place the executable in `Misc/` alongside `eye_tracker.py`
3. Run it - it will show a control window
4. Click "Launch Eye Tracker" to start webcam detection
5. Enable checkboxes to automatically link eye position to shader parameters

## How It Works

### Eye Tracking Flow
```
Webcam Feed
    ↓
eye_tracker.py (Python)
    ↓ (detects pupil/iris)
eye_gaze.json (normalized 0-1 coordinates)
    ↓
(Optional) EyeTrackingBridge.exe
    ↓ (simulates keyboard input)
ShaderGlass Parameter Sliders
    ↓
Shader receives CenterX, CenterY
    ↓
Zoom effect follows your eye gaze
```

### Shader Logic

The shader:
1. Takes your eye position as `CenterX` and `CenterY` parameters
2. Draws magnification zone around that center point
3. Uses `ZoomStrength` to control how much to zoom
4. Uses `ZoomRadius` to control area of effect
5. Uses `ZoomFalloff` for smooth edge blending

## Parameter Tuning

### For FPS Gaming
- **ZoomStrength**: 0.25-0.35 (moderate magnification)
- **ZoomRadius**: 0.3-0.4 (relatively focused zone)
- **ZoomFalloff**: 2.0-2.5 (smooth blend)

### For Reading/Detail Work
- **ZoomStrength**: 0.4-0.5 (strong magnification)
- **ZoomRadius**: 0.25-0.35 (tighter focus)
- **ZoomFalloff**: 1.5-2.0 (faster falloff)

### For Peripheral Awareness
- **ZoomStrength**: 0.15-0.25 (subtle zoom)
- **ZoomRadius**: 0.4-0.5 (large area)
- **ZoomFalloff**: 3.0-4.0 (very gradual blend)

## Troubleshooting

### Eye Tracker won't start
- Check your webcam is connected and functional
- Try in a well-lit environment (better face/eye detection)
- Run: `python -c "import cv2; print(cv2.__version__)"`  to verify OpenCV is installed

### Gaze isn't accurate
- Make sure lighting is good (not backlit)
- Face should be roughly centered in frame and 30-60cm away
- Look straight at the red circle in the visualization
- Calibration: wear glasses/contacts you normally use for the computer

### ShaderGlass parameters not updating automatically
- Make sure EyeTrackingBridge.exe is running
- Ensure ShaderGlass window is focused when the bridge sends inputs
- Check `eye_gaze.json` exists and is being updated by eye_tracker.py

### Performance issues
- Try reducing the video resolution on your computer
- Close other applications using the camera
- The eye tracker app is CPU-intensive, consider a dedicated GPU if available

## Advanced Usage

### Manual Parameter Adjustment

You don't need the bridge app - you can manually adjust the sliders:
1. Watch the eye_gaze.json values update
2. Manually adjust CenterX and CenterY sliders to test
3. Once tuned, use the Eye Tracking Bridge to automate

### Using with Different Shaders

You can adapt any shader to eye tracking by adding:
```glsl
#pragma parameter CenterX "Center X" 0.5 0.0 1.0 0.01
#pragma parameter CenterY "Center Y" 0.5 0.0 1.0 0.01
```

Then use `params.CenterX` and `params.CenterY` in your shader logic.

## Files

- `eye_tracker.py` - Main eye detection app (Python)
- `EyeTrackingBridge.cs` - Parameter bridge (C# / .NET)
- `zoom-fisheye.slang` - Shader source
- `zoom-fisheye.slangp` - Shader preset/profile
- `eye_gaze.json` - Output file (created by eye_tracker.py)

## Tips for Best Results

1. **Lighting**: Good ambient light or a desk lamp reduces errors
2. **Camera position**: Mount camera below eye level (like on monitor bezel)
3. **Distance**: 40-60cm from face is optimal
4. **Stability**: Keep head position relatively steady while focusing
5. **Calibration**: Blink occasionally - system adapts to your eyes slightly
6. **Multiple users**: Each person's eyes are different; adjust parameters per user

## Future Improvements

Possible enhancements:
- Calibration wizard for personalized accuracy
- Multiple zoom zones (for split-screen)
- Head tracking integration (combines eye & head position)
- Export/import preset profiles
- Network streaming for remote eye tracking

## Resources

- [GazeTracking Library](https://github.com/antoinelame/GazeTracking)
- [OpenCV Documentation](https://docs.opencv.org/)
- [MediaPipe Facial Landmarks](https://google.github.io/mediapipe/solutions/face_detection)
- [ShaderGlass GitHub](https://github.com/mausimus/ShaderGlass)

## License

These eye-tracking components are provided as extensions to ShaderGlass (GNU GPL v3.0).

---

**Enjoy eye-tracking enhanced visuals!** 👀
