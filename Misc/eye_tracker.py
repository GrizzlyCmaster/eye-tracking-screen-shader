#!/usr/bin/env python3
"""
Gaze Direction Tracker for ShaderGlass
Detects where you are looking on the screen by tracking pupil position
and writes normalized gaze direction coordinates to a file
that ShaderGlass or a helper app can read.

Uses OpenCV cascade classifiers to detect eyes, then tracks iris position
within each eye to estimate gaze direction on screen.

Usage:
  python eye_tracker.py
  
The app writes gaze direction to 'eye_gaze.json' in the same directory.
- Gaze X/Y: 0.5 = center of screen, 0.0 = left/top, 1.0 = right/bottom
"""

import json
import time
import os
import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError:
    print("Missing required packages. Install with:")
    print("  pip install opencv-python numpy")
    sys.exit(1)


class EyeTracker:
    def __init__(self, output_file="eye_gaze.json"):
        self.output_file = output_file
        
        # Load cascade classifiers (built into OpenCV)
        cascade_path = cv2.data.haarcascades
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
        
        # Open webcam
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
        self.face_detected = False
        
        print(f"Gaze Direction Tracker initialized with OpenCV")
        print(f"Camera resolution: {self.width}x{self.height}")
        print(f"Output file: {self.output_file}")
        print(f"")
        print(f"Look at different parts of your screen.")
        print(f"The red circle shows where your gaze is directed.")
        print(f"Press 'q' to quit, 'space' to show/hide visualization")
    
    def find_iris_position(self, eye_region):
        """
        Find iris position relative to eye (0.0-1.0)
        Returns normalized position within the eye region
        0.5 = center, 0.0 = left/top, 1.0 = right/bottom
        """
        gray = cv2.cvtColor(eye_region, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to smooth the image
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # Create a binary image (iris is darker than eye white)
        _, thresh = cv2.threshold(blurred, 100, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours (pupil/iris)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        h, w = eye_region.shape[:2]
        
        if contours:
            # Get the largest contour (the pupil/iris)
            largest_contour = max(contours, key=cv2.contourArea)
            (x, y), radius = cv2.minEnclosingCircle(largest_contour)
            
            # Normalize iris position within eye region (0.0 to 1.0)
            iris_x = x / w
            iris_y = y / h
            
            # Clamp to valid range
            iris_x = max(0.1, min(0.9, iris_x))  # Avoid extreme edges
            iris_y = max(0.1, min(0.9, iris_y))
            
            return iris_x, iris_y
        
        # Fallback: center of eye
        return 0.5, 0.5
    
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
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                h, w = frame.shape[:2]
                
                gaze_x, gaze_y = self.smooth_x, self.smooth_y
                self.face_detected = False
                
                # Detect faces
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                
                if len(faces) > 0:
                    self.face_detected = True
                    # Use the largest face detected
                    face = max(faces, key=lambda f: f[2] * f[3])
                    fx, fy, fw, fh = face
                    
                    # Region of interest for eyes (upper half of face)
                    roi_gray = gray[fy:fy + fh//2, fx:fx + fw]
                    roi_color = frame[fy:fy + fh//2, fx:fx + fw]
                    
                    # Detect eyes
                    eyes = self.eye_cascade.detectMultiScale(roi_gray)
                    
                    if len(eyes) >= 2:
                        # Sort eyes by x coordinate (left to right)
                        eyes = sorted(eyes, key=lambda e: e[0])
                        
                        # Get both eyes
                        left_eye = eyes[0]
                        right_eye = eyes[-1]
                        
                        # Extract eye regions
                        lex, ley, lew, leh = left_eye
                        rex, rey, rew, reh = right_eye
                        
                        left_eye_region = roi_color[ley:ley+leh, lex:lex+lew]
                        right_eye_region = roi_color[rey:rey+reh, rex:rex+rew]
                        
                        # Find iris position within each eye (0.0-1.0)
                        left_iris_x, left_iris_y = self.find_iris_position(left_eye_region)
                        right_iris_x, right_iris_y = self.find_iris_position(right_eye_region)
                        
                        # Average iris position from both eyes
                        avg_iris_x = (left_iris_x + right_iris_x) / 2
                        avg_iris_y = (left_iris_y + right_iris_y) / 2
                        
                        # Convert iris position to gaze direction on screen
                        # Iris at 0.5 = center of screen
                        # Iris at 0.0 = looking left/up
                        # Iris at 1.0 = looking right/down
                        new_gaze_x = avg_iris_x
                        new_gaze_y = avg_iris_y
                        
                        # Apply smoothing to reduce jitter
                        self.smooth_x = self.smooth_x * (1 - self.smoothing_factor) + new_gaze_x * self.smoothing_factor
                        self.smooth_y = self.smooth_y * (1 - self.smoothing_factor) + new_gaze_y * self.smoothing_factor
                        
                        gaze_x = self.smooth_x
                        gaze_y = self.smooth_y
                
                # Write to JSON file
                self._write_gaze_data(gaze_x, gaze_y)
                
                # Visualization
                if show_viz:
                    frame = self._draw_visualization(frame, faces)
                    cv2.imshow("Eye Tracker (Press 'q' to quit, space to hide)", frame)
                else:
                    cv2.imshow("Eye Tracker - Hidden (Press space to show)", frame)
                
                # Handle key input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("Quit requested")
                    break
                elif key == ord(' '):
                    show_viz = not show_viz
        
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
    
    def _draw_visualization(self, frame, faces):
        """Draw gaze direction and crosshair on frame"""
        h, w = frame.shape[:2]
        
        # Draw screen center crosshair (green)
        cv2.line(frame, (w // 2 - 30, h // 2), (w // 2 + 30, h // 2), (0, 255, 0), 2)
        cv2.line(frame, (w // 2, h // 2 - 30), (w // 2, h // 2 + 30), (0, 255, 0), 2)
        
        # Draw gaze direction point (where you're looking on screen)
        gaze_x = int(self.smooth_x * w)
        gaze_y = int(self.smooth_y * h)
        cv2.circle(frame, (gaze_x, gaze_y), 20, (0, 0, 255), -1)    # Red filled circle (large)
        cv2.circle(frame, (gaze_x, gaze_y), 25, (0, 0, 255), 3)     # Red circle outline
        
        # Draw detected faces with rectangles
        for (x, y, fw, fh) in faces:
            cv2.rectangle(frame, (x, y), (x + fw, y + fh), (255, 0, 0), 2)
            cv2.putText(frame, "Face", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        
        # Draw info text
        status = "DETECTED" if self.face_detected else "NOT DETECTED"
        cv2.putText(frame, f"Gaze Direction: {status}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"Looking at: ({self.smooth_x:.2f}, {self.smooth_y:.2f}) on screen", 
                   (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
        cv2.putText(frame, f"Pixel coords: ({gaze_x}, {gaze_y})", 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)
        
        # Instructions
        cv2.putText(frame, "Green cross = screen center | Red circle = your gaze direction", 
                   (10, h - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
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
