# 👁️ Eye Tracking Screen Shader

GPU-accelerated eye-tracking shader with foveated rendering for PC gaming. Uses webcam-based gaze detection to create a motion-sickness-free magnification effect by applying selective blur to peripheral vision, mimicking natural human vision.

## ⚠️ Important: Accuracy Limitations

**This is a proof-of-concept with fundamental accuracy limitations.**

Webcam-based eye tracking has ±5-10° error, which means it's good for **general gaze direction** but not precise point tracking. This is due to:
- No IR illumination (can't see pupil reflections clearly)
- Low webcam resolution limits iris detail
- Ambient lighting variations
- Basic head movement compensation

**For accurate gaming eye tracking, dedicated hardware is required:**
- **Tobii Eye Tracker 5** (~$230) - Gaming-focused, ±0.5° accuracy
- **Gazepoint GP3** (~$500) - Research-grade
- Works with IR cameras and higher sampling rates

This implementation is educational and demonstrates the core concepts, but real applications need specialized hardware.

## 🎮 Features

- **Foveated Rendering**: Sharp center focus with progressively blurred periphery - no geometric distortion
- **Webcam Eye Tracking**: Real-time gaze detection using OpenCV and gaze-tracking library
- **Motion-Sickness Safe**: Uses perceptual rendering instead of warping to prevent vestibular conflicts
- **FPS Optimized**: Variable resolution sampling for smooth gameplay
- **Easy Integration**: Works with ShaderGlass or any shader framework supporting GLSL/Slang
- **Multi-Mode Support**: Includes reference zoom/fisheye shader for comparison

## 🚀 Quick Start

### Download & Run Eye Tracker

```bash
cd Misc/
./eye_tracker.exe
```

The eye tracker will:
- Open your webcam
- Detect your gaze position
- Output real-time coordinates to `eye_gaze.json`
- Display visualization with gaze point (red circle)

### Load Shader in ShaderGlass

1. Open **ShaderGlass** 
2. Select **Import Custom Shader** 
3. Navigate to: `Scripts/slang-shaders/custom/foveated-rendering/`
4. Select `foveated-rendering.slangp`
5. Adjust **CenterX** and **CenterY** sliders to follow your eye position

## 📋 System Requirements

- **OS**: Windows 10/11
- **Hardware**: Any GPU supporting DirectX 11 (or compatible shader framework)
- **Webcam**: USB webcam or integrated camera
- **ShaderGlass**: Optional (required for the featured implementation)

## 📦 Project Structure

```
eye-tracking-screen-shader/
├── Misc/
│   ├── eye_tracker.exe           # Standalone executable (no Python needed)
│   ├── eye_tracker.py            # Python source (if you want to modify)
│   ├── EYE_TRACKING_README.md    # Detailed documentation
│   └── FoveatedRendering.*       # Backup shader files
├── Scripts/slang-shaders/custom/
│   ├── foveated-rendering/       # Main shader (RECOMMENDED)
│   │   ├── foveated-rendering.slang
│   │   └── foveated-rendering.slangp
│   └── zoom-fisheye/             # Reference implementation (causes motion sickness)
├── README.md                      # This file
└── setup-github.ps1              # GitHub repository setup script
```

## ⚙️ Shader Parameters

### Foveated Rendering (Recommended)

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| **CenterX** | 0.5 | 0.0-1.0 | Horizontal gaze position (0=left, 1=right) |
| **CenterY** | 0.5 | 0.0-1.0 | Vertical gaze position (0=top, 1=bottom) |
| **FoveaRadius** | 0.15 | 0.05-0.4 | Size of sharp central area |
| **TransitionRadius** | 0.35 | 0.1-0.8 | Falloff boundary (blur gradient) |
| **PeripheralBlur** | 2.0 | 0.5-4.0 | Maximum blur strength in periphery |
| **Sharpness** | 1.2 | 0.8-2.0 | Center detail enhancement (unsharp mask) |

### FPS Gaming Recommended Settings
```
FoveaRadius: 0.15
TransitionRadius: 0.35
PeripheralBlur: 2.0
Sharpness: 1.2
```

### Performance Priority Settings
```
FoveaRadius: 0.18
TransitionRadius: 0.40
PeripheralBlur: 1.5
Sharpness: 1.1
```

## 🎯 How It Works

1. **Eye Tracking**: `eye_tracker.exe` captures webcam frames and detects gaze position using ML-based eye detection
2. **JSON Output**: Gaze coordinates written to `eye_gaze.json` every frame (~30-60 FPS)
3. **Shader Binding**: ShaderGlass reads JSON and updates `CenterX`/`CenterY` parameters
4. **Foveated Rendering**: GPU shader applies sharp rendering at gaze point, progressively blurs periphery

**Technical Details**: The shader calculates distance from gaze center, converts to eccentricity (0=fovea, 1=edge), and applies proportional blur + sharpening. Unlike fisheye distortion techniques, this preserves image geometry while mimicking natural human visual perception.

## 📖 Full Documentation

See [EYE_TRACKING_README.md](Misc/EYE_TRACKING_README.md) for:
- Detailed setup instructions
- Parameter tuning guide
- Troubleshooting webcam/calibration issues
- Performance optimization tips
- Use cases beyond FPS gaming

## 🔧 Manual Build (Advanced)

If you want to rebuild `eye_tracker.exe` from source:

```bash
# Install dependencies
pip install opencv-python gaze-tracking PyInstaller

# Run build script
cd Misc/
./build_exe.bat
```

Output: `Misc/dist/eye_tracker.exe` (~150MB standalone executable)

## 📚 Alternative: Zoom/Fisheye Shader

A reference zoom-based implementation is included in `Scripts/slang-shaders/custom/zoom-fisheye/`. This uses geometric distortion for magnification but may cause motion sickness due to vestibular conflicts. Foveated rendering is strongly recommended for continuous use.

## 🐛 Troubleshooting

### Webcam Not Detected
- Check Windows Device Manager: Devices > Cameras
- Verify app permissions: Settings > Privacy & Security > Camera
- Try different USB port or webcam

### Gaze Position Jumping
- Increase smoothing in `eye_tracker.py` (line ~140): `smoothing_factor = 0.3`
- Ensure adequate lighting on face
- Rebuild exe after changes: `./build_exe.bat`

### Shader Not Updating
- Confirm `eye_gaze.json` is being written (check file timestamp)
- Verify ShaderGlass has read permissions for the JSON file
- Check parameter names match exactly: `CenterX`, `CenterY`

See [EYE_TRACKING_README.md](Misc/EYE_TRACKING_README.md) for more solutions.

## 📝 License

This project is provided as-is for educational and personal use. 

## 🙏 Credits

- Built with [ShaderGlass](https://github.com/civil-team/ShaderGlass) shader overlay
- Eye detection via [Gaze Tracking](https://github.com/antoinelame/GazeTracking) library
- Shader framework: [Slang](https://slang-shaders.github.io/)

## 🚀 Future Enhancements

- [ ] Automatic gaze calibration (5-point)
- [ ] Multi-monitor support
- [ ] VR headset integration
- [ ] Performance profiling overlay
- [ ] Custom shader editor UI
- [ ] Support for other shader frameworks (ANGLE, UE4)

## 📞 Support

For issues or suggestions:
1. Check [EYE_TRACKING_README.md](Misc/EYE_TRACKING_README.md) troubleshooting section
2. Review shader parameters and adjust gradually
3. Verify webcam and eye_gaze.json functionality independently

---

**Made for FPS gamers who want immersive gaze-contingent rendering without motion sickness.** 👀🎮
