import cv2
import threading
import time
import os

# Prevent core-dumps on Pi 32-bit OS by restricting OpenMP threads targeting AVX registers
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
if "OPENBLAS_CORETYPE" in os.environ:
    del os.environ["OPENBLAS_CORETYPE"]

import numpy as np
import torch

torch.set_num_threads(1)

from ultralytics import YOLO

# --- PyTorch 2.6+ Security Hotfix ---
_original_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = _patched_load
# ------------------------------------

class CVDetector:
    def __init__(self, model_path='ambulance_model.pt', camera_index=0):
        print(f"Loading custom YOLO model: {model_path}...")
        self.model = YOLO(model_path)
        self.camera_index = camera_index
        
        self.ambulance_detected = False
        self.running = False
        self.current_frame = None
        self.confidence_threshold = 0.75

    def start(self):
        self.running = True
        print("Starting CV Camera detection background thread...")
        t = threading.Thread(target=self._run_inference_loop)
        t.daemon = True
        t.start()

    def _run_inference_loop(self):
        # Initialize camera inside the thread to prevent libcamerify memory map crashes
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print("[!] WARNING: Camera not detected initially.")
            
        # 640x480 gives YOLO enough resolution for reliable detection
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize V4L2 buffer lag
            
        # ---------------------------------------------------------
        # NEW ZERO-LATENCY ENGINE: Decoupled Hardware Polling Thread
        # ---------------------------------------------------------
        class FrameReader:
            def __init__(self, cap, parent):
                self.cap = cap
                self.parent = parent
                self.frame = None
                self.latest_bbox = None
                self.running = True
                threading.Thread(target=self.poll, daemon=True).start()
                
            def poll(self):
                while self.running:
                    ret, f = self.cap.read()
                    if ret:
                        self.frame = f
                        # LIVE UNBLOCKED 30 FPS BROADCAST
                        disp = f.copy()
                        if self.latest_bbox:
                            x1, y1, x2, y2, conf = self.latest_bbox
                            cv2.rectangle(disp, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
                            cv2.putText(disp, f"AMBULANCE {conf:.2f}", (int(x1), int(y1)-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        
                        # Feed the live 30 FPS buffer constantly to Flask
                        self.parent.current_frame = disp
                    else:
                        time.sleep(0.01)
                        
            def get_frame(self):
                return self.frame
                
            def stop(self):
                self.running = False
                
        reader = FrameReader(self.cap, self)
        time.sleep(0.5) # Hardware warmup
        
        while self.running:
            try:
                frame = reader.get_frame()
                if frame is None:
                    # Render error frame directly out if offline
                    error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(error_frame, "CAMERA OFFLINE", (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
                    self.current_frame = error_frame
                    time.sleep(0.5)
                    continue
                    
                # Fix V4L2 Memory Map DMA Crash: Copy the frame directly into contiguous RAM
                safe_frame = np.ascontiguousarray(frame.copy())
                    
                # Run YOLO inference natively on the absolute most recent frame fetched from RAM!
                results = self.model.predict(safe_frame, conf=self.confidence_threshold, imgsz=480, verbose=False)
                
                detected = False
                highest_conf_box = None
                
                for r in results:
                    if len(r.boxes) > 0:
                        detected = True
                        box = r.boxes[0]
                        # Capture the coordinates directly so the 30 FPS thread can draw it unblocked
                        highest_conf_box = (
                            box.xyxy[0][0].item(), box.xyxy[0][1].item(), 
                            box.xyxy[0][2].item(), box.xyxy[0][3].item(), 
                            box.conf[0].item()
                        )
                        break
                        
                self.ambulance_detected = detected
                reader.latest_bbox = highest_conf_box if detected else None
                
            except Exception as e:
                print(f"Inference error bypassed safely: {e}")
                time.sleep(1)
            
        # Cleanup
        reader.stop()
            
    def stop(self):
        self.running = False
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
