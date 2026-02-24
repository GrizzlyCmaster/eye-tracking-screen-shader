#!/usr/bin/env python3
"""
Enhanced Gaze Direction Tracker for ShaderGlass
Advanced eye tracking with Kalman filtering, calibration, and improved algorithms.

Features:
- Kalman filter for smooth gaze tracking
- 5-point calibration system for accuracy
- Hough circle detection for precise iris tracking
- Blink detection
- Better gaze mapping

Usage:
  python eye_tracker_enhanced.py
  
Press 'C' to start calibration (look at the dots that appear)
Press 'Q' to quit, 'Space' to toggle visualization
"""

import json
import time
import os
import sys
from pathlib import Path
import math

try:
    import cv2
    import numpy as np
    from scipy import interpolate
    from filterpy.kalman import KalmanFilter
    from imutils import face_utils
except ImportError as e:
    print(f"Missing required packages: {e}")
    print("Install with:")
    print("  pip install opencv-python numpy scipy filterpy imutils")
    sys.exit(1)


class KalmanGazeFilter:
    """Kalman filter for smooth gaze tracking"""
    def __init__(self):
        self.kf_x = KalmanFilter(dim_x=2, dim_z=1)
        self.kf_y = KalmanFilter(dim_x=2, dim_z=1)
        
        # State transition matrix
        dt = 0.033  # ~30fps
        self.kf_x.F = np.array([[1., dt], [0., 1.]])
        self.kf_y.F = np.array([[1., dt], [0., 1.]])
        
        # Measurement function
        self.kf_x.H = np.array([[1., 0.]])
        self.kf_y.H = np.array([[1., 0.]])
        
        # Covariance matrices
        self.kf_x.P *= 1000.
        self.kf_y.P *= 1000.
        self.kf_x.R = 5  # Measurement noise
        self.kf_y.R = 5
        self.kf_x.Q = np.array([[0.01, 0], [0, 0.01]])  # Process noise
        self.kf_y.Q = np.array([[0.01, 0], [0, 0.01]])
        
    def update(self, x, y):
        """Update with new measurement and return filtered position"""
        self.kf_x.predict()
        self.kf_y.predict()
        self.kf_x.update(x)
        self.kf_y.update(y)
        # Return scalar values, not arrays - use .item() to extract from numpy array
        return float(self.kf_x.x[0].item()), float(self.kf_y.x[0].item())


class CalibrationSystem:
    """5-point calibration for accurate gaze mapping"""
    def __init__(self):
        self.calibration_points = [
            (0.05, 0.05),   # Top-left (more extreme)
            (0.95, 0.05),   # Top-right
            (0.5, 0.5),     # Center
            (0.05, 0.95),   # Bottom-left
            (0.95, 0.95),   # Bottom-right
        ]
        self.calibration_data = []
        self.current_point = 0
        self.is_calibrating = False
        self.samples_collected = 0
        self.samples_needed = 30  # 1 second at 30fps
        self.is_calibrated = False
        self.mapping_function_x = None
        self.mapping_function_y = None
        
    def start_calibration(self):
        """Begin calibration process"""
        self.is_calibrating = True
        self.current_point = 0
        self.calibration_data = []
        self.samples_collected = 0
        self.is_calibrated = False
        print("\n=== CALIBRATION STARTED ===")
        print("Look at each dot that appears and keep your gaze steady.")
        
    def add_sample(self, eye_x, eye_y):
        """Add a sample during calibration"""
        if not self.is_calibrating:
            return False
            
        target_x, target_y = self.calibration_points[self.current_point]
        self.calibration_data.append((eye_x, eye_y, target_x, target_y))
        self.samples_collected += 1
        
        if self.samples_collected >= self.samples_needed:
            self.samples_collected = 0
            self.current_point += 1
            
            if self.current_point >= len(self.calibration_points):
                self._compute_mapping()
                self.is_calibrating = False
                self.is_calibrated = True
                print("=== CALIBRATION COMPLETE ===\n")
                return True
            else:
                print(f"Point {self.current_point + 1}/{len(self.calibration_points)}")
                
        return False
        
    def _compute_mapping(self):
        """Compute calibration mapping function"""
        if len(self.calibration_data) < 10:
            print("Not enough calibration data!")
            return
            
        # Separate data
        eye_xs = [d[0] for d in self.calibration_data]
        eye_ys = [d[1] for d in self.calibration_data]
        target_xs = [d[2] for d in self.calibration_data]
        target_ys = [d[3] for d in self.calibration_data]
        
        # Create interpolation functions (2D thin plate spline)
        try:
            # Simple polynomial mapping (more robust than splines)
            self.eye_to_screen_x = np.polyfit(eye_xs, target_xs, 2)
            self.eye_to_screen_y = np.polyfit(eye_ys, target_ys, 2)
        except Exception as e:
            print(f"Calibration error: {e}")
            self.is_calibrated = False
            
    def map_gaze(self, eye_x, eye_y):
        """Map eye position to screen position using calibration"""
        if not self.is_calibrated:
            return eye_x, eye_y
            
        try:
            screen_x = np.polyval(self.eye_to_screen_x, eye_x)
            screen_y = np.polyval(self.eye_to_screen_y, eye_y)
            
            # Clamp to valid range
            screen_x = max(0.0, min(1.0, screen_x))
            screen_y = max(0.0, min(1.0, screen_y))
            
            return screen_x, screen_y
        except:
            return eye_x, eye_y
            
    def get_current_calibration_point(self):
        """Get current calibration target"""
        if not self.is_calibrating:
            return None
        return self.calibration_points[self.current_point]


class EnhancedEyeTracker:
    def __init__(self, output_file="eye_gaze.json"):
        self.output_file = output_file
        
        # Load cascade classifiers
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
        
        # Open webcam
        self.webcam = cv2.VideoCapture(0)
        if not self.webcam.isOpened():
            print("Error: Could not open webcam.")
            sys.exit(1)
        
        # Set higher resolution for better tracking
        self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Get actual frame dimensions
        self.width = int(self.webcam.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.webcam.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Display scaling factor (make window larger on screen)
        self.display_scale = 1.5
        
        # Initialize Kalman filter and calibration
        self.kalman_filter = KalmanGazeFilter()
        self.calibration = CalibrationSystem()
        
        # Tracking state
        self.gaze_x = 0.5
        self.gaze_y = 0.5
        self.face_detected = False
        self.blink_counter = 0
        
        print(f"Enhanced Gaze Tracker initialized")
        print(f"Camera resolution: {self.width}x{self.height}")
        print(f"Output file: {self.output_file}")
        print(f"\n=== CONTROLS ===")
        print(f"C: Start calibration (RECOMMENDED for accuracy)")
        print(f"Space: Toggle visualization")
        print(f"Q: Quit")
        print(f"\nCalibration tip: Sit at your normal distance from screen\n")
        
    def detect_iris(self, eye_region):
        """Detect iris using Hough circles"""
        gray = cv2.cvtColor(eye_region, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        
        h, w = gray.shape
        
        # Detect circles (iris/pupil)
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=w//2,
            param1=50,
            param2=30,
            minRadius=int(min(w, h) * 0.1),
            maxRadius=int(min(w, h) * 0.4)
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            # Get the first (strongest) circle
            x, y, r = circles[0][0]
            
            # Normalize position within eye
            iris_x = x / w
            iris_y = y / h
            
            return max(0.0, min(1.0, iris_x)), max(0.0, min(1.0, iris_y))
        
        # Fallback: use threshold method
        return self._fallback_iris_detection(gray)
        
    def _fallback_iris_detection(self, gray):
        """Fallback iris detection using thresholding"""
        h, w = gray.shape
        
        _, thresh = cv2.threshold(gray, 70, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest = max(contours, key=cv2.contourArea)
            M = cv2.moments(largest)
            
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                return cx / w, cy / h
                
        return 0.5, 0.5
        
    def calculate_eye_aspect_ratio(self, eye_points):
        """Calculate EAR for blink detection"""
        # Vertical distances
        A = np.linalg.norm(eye_points[1] - eye_points[5])
        B = np.linalg.norm(eye_points[2] - eye_points[4])
        
        # Horizontal distance
        C = np.linalg.norm(eye_points[0] - eye_points[3])
        
        ear = (A + B) / (2.0 * C)
        return ear
        
    def run(self):
        """Main tracking loop"""
        show_viz = True
        frame_count = 0
        
        try:
            while True:
                ret, frame = self.webcam.read()
                if not ret:
                    print("Failed to capture frame")
                    break
                
                frame = cv2.flip(frame, 1)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                h, w = frame.shape[:2]
                
                frame_count += 1
                self.face_detected = False
                raw_gaze_x, raw_gaze_y = 0.5, 0.5
                
                # Detect faces
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                
                if len(faces) > 0:
                    self.face_detected = True
                    face = max(faces, key=lambda f: f[2] * f[3])
                    fx, fy, fw, fh = face
                    
                    # ROI for eyes
                    roi_gray = gray[fy:fy + fh//2, fx:fx + fw]
                    roi_color = frame[fy:fy + fh//2, fx:fx + fw]
                    
                    # Detect eyes
                    eyes = self.eye_cascade.detectMultiScale(roi_gray)
                    
                    if len(eyes) >= 2:
                        eyes = sorted(eyes, key=lambda e: e[0])
                        left_eye = eyes[0]
                        right_eye = eyes[-1]
                        
                        # Extract eye regions
                        lex, ley, lew, leh = left_eye
                        rex, rey, rew, reh = right_eye
                        
                        left_eye_region = roi_color[ley:ley+leh, lex:lex+lew]
                        right_eye_region = roi_color[rey:rey+reh, rex:rex+rew]
                        
                        # Detect iris in each eye
                        left_iris_x, left_iris_y = self.detect_iris(left_eye_region)
                        right_iris_x, right_iris_y = self.detect_iris(right_eye_region)
                        
                        # Average both eyes
                        raw_gaze_x = (left_iris_x + right_iris_x) / 2
                        raw_gaze_y = (left_iris_y + right_iris_y) / 2
                        
                        # Apply calibration if available
                        if self.calibration.is_calibrated:
                            raw_gaze_x, raw_gaze_y = self.calibration.map_gaze(raw_gaze_x, raw_gaze_y)
                        
                        # Apply Kalman filter
                        self.gaze_x, self.gaze_y = self.kalman_filter.update(raw_gaze_x, raw_gaze_y)
                        
                        # Ensure values are in valid range
                        self.gaze_x = max(0.0, min(1.0, float(self.gaze_x)))
                        self.gaze_y = max(0.0, min(1.0, float(self.gaze_y)))
                        
                        # Add to calibration if active
                        if self.calibration.is_calibrating:
                            self.calibration.add_sample(raw_gaze_x, raw_gaze_y)
                
                # Write gaze data
                self._write_gaze_data(self.gaze_x, self.gaze_y)
                
                # Visualization
                if show_viz:
                    frame = self._draw_visualization(frame, faces)
                    # Scale up the display window
                    display_frame = cv2.resize(frame, None, fx=self.display_scale, fy=self.display_scale, interpolation=cv2.INTER_LINEAR)
                    cv2.imshow("Enhanced Gaze Tracker", display_frame)
                else:
                    placeholder = np.zeros((100, 400, 3), dtype=np.uint8)
                    cv2.putText(placeholder, "Visualization Hidden (Press Space)", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.imshow("Enhanced Gaze Tracker (Hidden)", placeholder)
                
                # Handle keys
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\nQuitting...")
                    break
                elif key == ord(' '):
                    show_viz = not show_viz
                elif key == ord('c') or key == ord('C'):
                    if not self.calibration.is_calibrating:
                        self.calibration.start_calibration()
        
        finally:
            self.cleanup()
    
    def _write_gaze_data(self, gaze_x, gaze_y):
        """Write gaze coordinates to JSON"""
        # Convert numpy arrays to scalars if needed
        if isinstance(gaze_x, np.ndarray):
            gaze_x = float(gaze_x.item())
        if isinstance(gaze_y, np.ndarray):
            gaze_y = float(gaze_y.item())
            
        data = {
            "timestamp": time.time(),
            "gaze_x": float(gaze_x),
            "gaze_y": float(gaze_y),
            "center_x": float(gaze_x),
            "center_y": float(gaze_y),
            "calibrated": self.calibration.is_calibrated
        }
        
        try:
            with open(self.output_file, 'w') as f:
                json.dump(data, f)
        except IOError as e:
            pass  # Silently fail to avoid spam
    
    def _draw_visualization(self, frame, faces):
        """Draw visualization overlay"""
        h, w = frame.shape[:2]
        
        # Calibration mode
        if self.calibration.is_calibrating:
            cal_point = self.calibration.get_current_calibration_point()
            if cal_point:
                cx, cy = int(cal_point[0] * w), int(cal_point[1] * h)
                
                # Draw large calibration target
                cv2.circle(frame, (cx, cy), 50, (0, 255, 255), 4)
                cv2.circle(frame, (cx, cy), 8, (0, 255, 255), -1)
                
                # Draw crosshair at calibration point
                cv2.line(frame, (cx - 60, cy), (cx + 60, cy), (0, 255, 255), 2)
                cv2.line(frame, (cx, cy - 60), (cx, cy + 60), (0, 255, 255), 2)
                
                # Progress bar
                progress = self.calibration.samples_collected / self.calibration.samples_needed
                bar_w = 300
                bar_h = 30
                bar_x = (w - bar_w) // 2
                bar_y = h - 80
                
                cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (100, 100, 100), -1)
                cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_w * progress), bar_y + bar_h), (0, 255, 0), -1)
                cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (255, 255, 255), 2)
                
                # Instructions
                cv2.putText(frame, f"LOOK AT THE YELLOW CROSS - Point {self.calibration.current_point + 1}/5",
                           (w//2 - 300, bar_y - 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
                cv2.putText(frame, "Keep your HEAD STILL, move only your EYES",
                           (w//2 - 250, bar_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Normal mode
        else:
            # Draw center crosshair (larger)
            cv2.line(frame, (w//2 - 50, h//2), (w//2 + 50, h//2), (0, 255, 0), 3)
            cv2.line(frame, (w//2, h//2 - 50), (w//2, h//2 + 50), (0, 255, 0), 3)
            
            # Draw gaze point (larger)
            gaze_px = int(self.gaze_x * w)
            gaze_py = int(self.gaze_y * h)
            
            color = (0, 0, 255) if self.calibration.is_calibrated else (0, 165, 255)
            cv2.circle(frame, (gaze_px, gaze_py), 35, color, -1)
            cv2.circle(frame, (gaze_px, gaze_py), 42, color, 4)
            
            # Draw faces
            for (x, y, fw, fh) in faces:
                cv2.rectangle(frame, (x, y), (x + fw, y + fh), (255, 0, 0), 3)
            
            # Status text (larger)
            status = "CALIBRATED" if self.calibration.is_calibrated else "NOT CALIBRATED"
            status_color = (0, 255, 0) if self.calibration.is_calibrated else (0, 165, 255)
            
            cv2.putText(frame, f"Status: {status}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, status_color, 3)
            cv2.putText(frame, f"Gaze: ({self.gaze_x:.2f}, {self.gaze_y:.2f})", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            
            if not self.calibration.is_calibrated:
                cv2.putText(frame, "Press 'C' to calibrate for better accuracy", 
                           (10, h - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
            
            cv2.putText(frame, "C: Calibrate | Space: Hide | Q: Quit", 
                       (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
        
        return frame
    
    def cleanup(self):
        """Clean up resources"""
        self.webcam.release()
        cv2.destroyAllWindows()
        print(f"\nTracker stopped. Gaze data: {os.path.abspath(self.output_file)}")


if __name__ == "__main__":
    tracker = EnhancedEyeTracker()
    tracker.run()
