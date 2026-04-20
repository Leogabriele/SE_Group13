import time
import cv2
import threading
from flask import Flask, render_template, Response
from flask_socketio import SocketIO
from cv_detector import CVDetector
from rf_receiver import RFReceiver
from traffic_controller import TrafficController

app = Flask(__name__)
# threading async_mode prevents conflicts with OpenCV and RPi.GPIO
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# Initialize Systems
controller = TrafficController()
rf_subsystem = RFReceiver()
cv_subsystem = CVDetector(model_path='ambulance_model.pt', camera_index=0)

system_logs = []

def add_log(msg):
    """Pushes an event log string to the web UI instantly"""
    timestamp = time.strftime('%H:%M:%S')
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry) # Standard console output
    system_logs.insert(0, log_entry)
    if len(system_logs) > 50:
        system_logs.pop()
    socketio.emit('new_log', {'log': log_entry})

def state_broadcast_loop():
    """Background loop to constantly send hardware status to the web app."""
    while True:
        rf_diag = rf_subsystem.get_diagnostic()
        payload = {
            'emergency_override': controller.emergency_override,
            'current_lane': controller.current_lane,
            'lane_states': controller.lane_states,
            'rf_detected': rf_subsystem.ambulance_detected,
            'cv_detected': cv_subsystem.ambulance_detected,
            'rf_diag': rf_diag
        }
        socketio.emit('state_update', payload)
        time.sleep(0.3)

def check_for_override(rf, cv, junction):
    """Master intersection logic — dual sensor verification with timed override."""
    add_log("System Online. Awaiting sirens...")
    while True:
        # Only trigger if NOT already in an override
        if not junction.emergency_override:
            if rf.ambulance_detected and cv.ambulance_detected:
                add_log("!!! OVERRIDE ENGAGED: Dual Sensor Verification !!!")
                add_log("Locking Intersection. Priority: Lane 1 (10s green).")
                
                # This call BLOCKS for ~20s total (5s yellow transition + 10s green + 5s yellow back)
                junction.run_timed_override(emergency_lane_number=1, green_duration=10)
                
                add_log("Override complete. Normal cycle resumed.")
                
                # Brief cooldown to prevent immediate re-triggering
                time.sleep(5)
                
        time.sleep(0.3)


# ------ FLASK ROUTES ------ #

@app.route('/')
def index():
    return render_template('index.html')

# ── Optimized MJPEG Stream ──
STREAM_FPS = 15
JPEG_QUALITY = 80  # Good clarity with reasonable bandwidth

def gen_frames():
    """Creates an MJPEG video stream from the YOLO annotated frames"""
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
    frame_interval = 1.0 / STREAM_FPS
    
    while True:
        t_start = time.monotonic()
        
        if hasattr(cv_subsystem, 'current_frame') and cv_subsystem.current_frame is not None:
            ret, buffer = cv2.imencode('.jpg', cv_subsystem.current_frame, encode_params)
            if ret:
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        elapsed = time.monotonic() - t_start
        sleep_time = frame_interval - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('connect')
def handle_connect():
    add_log("Authorized Command Device Connected.")
    for msg in reversed(system_logs[:10]):
        socketio.emit('new_log', {'log': msg})

if __name__ == '__main__':
    # Initialize RF hardware
    try:
        rf_subsystem.setup()
        add_log("RF NRF24L01 hardware initialized successfully.")
    except RuntimeError as e:
        add_log(f"RF Hardware: {e}")
        
    print("Starting hardware threads...")
    controller.run_normal_cycle_loop()
    rf_subsystem.start()
    cv_subsystem.start()
    
    # Start web broadcast thread
    t2 = threading.Thread(target=state_broadcast_loop)
    t2.daemon = True
    t2.start()

    # Start logic manager thread
    t1 = threading.Thread(target=check_for_override, args=(rf_subsystem, cv_subsystem, controller))
    t1.daemon = True
    t1.start()

    print("\n[!] ========================================== [!]")
    print("    FLASK IOT SERVER LIVE. OPEN DASHBOARD AT:    ")
    print("    http://127.0.0.1:5000  (on this Pi)    ")
    print("    http://<pi_ip_address>:5000 (from laptop)  ")
    print("[!] ========================================== [!]\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, log_output=False, allow_unsafe_werkzeug=True)
