#!/usr/bin/env python3
"""
Eye Tracking Application for ShaderGlass
Detects eye gaze position from webcam and writes normalized coordinates to a file
that ShaderGlass or a helper app can read.

Installation:
  pip install opencv-python gaze-tracking

Usage:
  python eye_tracker.py
  
The app writes gaze coordinates to 'eye_gaze.json' in the same directory.
"""

import json
import time
import os
import sys
from pathlib import Path

try:
    import cv2
    from gaze_tracking import GazeTracking
except ImportError:
    print("Missing required packages. Install with:")
    print("  pip install opencv-python gaze-tracking")
    sys.exit(1)


class EyeTracker:
    def __init__(self, output_file="eye_gaze.json"):
        self.output_file = output_file
        self.gaze = GazeTracking()
        self.webcam = cv2.VideoCapture(0)
        
        if not self.webcam.isOpened():
            print("Error: Could not open webcam. Check camera is available.")
            sys.exit(1)
        
        # Get frame dimensions
        self.width = int(self.webcam.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.webcam.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Smoothing for gaze coordinates (reduces jitter)
        self.smooth_x = 0.5
        self.smooth_y = 0.5
        self.smoothing_factor = 0.15
        
        print(f"Eye Tracker initialized")
        print(f"Camera resolution: {self.width}x{self.height}")
        print(f"Output file: {self.output_file}")
        print(f"Press 'q' to quit, 'c' to calibrate, space to show/hide visualization")
    
    def run(self):
        """Main tracking loop"""
        show_viz = True
        
        try:
            while True:
                ret, frame = self.webcam.read()
                if not ret:
                    print("Failed to capture frame from webcam")
                    break
                
                # Flip frame horizontally for natural viewing
                frame = cv2.flip(frame, 1)
                
                # Process frame
                self.gaze.refresh(frame)
                
                # Get gaze coordinates (0.0 to 1.0)
                gaze_x = self.gaze.horizontal_ratio
                gaze_y = self.gaze.vertical_ratio
                
                # Validate coordinates
                if gaze_x is not None and gaze_y is not None:
                    # Apply smoothing to reduce jitter
                    self.smooth_x = self.smooth_x * (1 - self.smoothing_factor) + gaze_x * self.smoothing_factor
                    self.smooth_y = self.smooth_y * (1 - self.smoothing_factor) + gaze_y * self.smoothing_factor
                    
                    # Clamp to valid range
                    self.smooth_x = max(0.0, min(1.0, self.smooth_x))
                    self.smooth_y = max(0.0, min(1.0, self.smooth_y))
                    
                    # Write to JSON file
                    self._write_gaze_data(self.smooth_x, self.smooth_y)
                
                # Visualization
                if show_viz:
                    frame = self._draw_visualization(frame)
                    cv2.imshow("Eye Tracker (Press 'q' to quit, 'c' to calibrate, space to hide)", frame)
                else:
                    cv2.imshow("Eye Tracker - Hidden (Press space to show)", frame)
                
                # Handle key input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("Quit requested")
                    break
                elif key == ord(' '):
                    show_viz = not show_viz
                elif key == ord('c'):
                    print("Calibration not implemented yet - adjust ZoomStrength/Radius manually")
        
        finally:
            self.cleanup()
    
    def _write_gaze_data(self, gaze_x, gaze_y):
        """Write gaze coordinates to JSON file"""
        data = {
            "timestamp": time.time(),
            "gaze_x": gaze_x,
            "gaze_y": gaze_y,
            "center_x": gaze_x,  # For ShaderGlass CenterX parameter
            "center_y": gaze_y   # For ShaderGlass CenterY parameter
        }
        
        try:
            with open(self.output_file, 'w') as f:
                json.dump(data, f)
        except IOError as e:
            print(f"Warning: Could not write to {self.output_file}: {e}")
    
    def _draw_visualization(self, frame):
        """Draw gaze point and crosshair on frame"""
        h, w = frame.shape[:2]
        
        # Draw center crosshair
        cv2.line(frame, (w // 2 - 20, h // 2), (w // 2 + 20, h // 2), (0, 255, 0), 1)
        cv2.line(frame, (w // 2, h // 2 - 20), (w // 2, h // 2 + 20), (0, 255, 0), 1)
        
        # Draw gaze point if available
        if self.gaze.horizontal_ratio is not None and self.gaze.vertical_ratio is not None:
            gaze_x = int(self.smooth_x * w)
            gaze_y = int(self.smooth_y * h)
            cv2.circle(frame, (gaze_x, gaze_y), 10, (0, 0, 255), -1)  # Red filled circle
            cv2.circle(frame, (gaze_x, gaze_y), 15, (0, 0, 255), 2)   # Red circle outline
        
        # Draw face rectangle if detected
        if self.gaze.face_detected:
            for face in self.gaze.faces:
                x, y, w_face, h_face = face
                cv2.rectangle(frame, (x, y), (x + w_face, y + h_face), (255, 0, 0), 2)
        
        # Draw info text
        cv2.putText(frame, f"X: {self.smooth_x:.2f}  Y: {self.smooth_y:.2f}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Space: hide/show | Q: quit", 
                   (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        return frame
    
    def cleanup(self):
        """Clean up resources"""
        self.webcam.release()
        cv2.destroyAllWindows()
        print(f"Eye tracker stopped. Data was written to: {os.path.abspath(self.output_file)}")


if __name__ == "__main__":
    tracker = EyeTracker()
    tracker.run()
