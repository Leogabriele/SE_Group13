import time
import cv2
from cv_detector import CVDetector
from rf_receiver import RFReceiver
from traffic_controller import TrafficController

def check_for_override(rf, cv, junction):
    """
    Core Mission Logic: We only trigger an emergency override if BOTH the RF confirms
    a siren is active, AND the camera physically verifies an ambulance is present.
    """
    while True:
        # Normal Traffic State Monitoring
        if not junction.emergency_override:
            # We implemented the AND conditional as per your dual-verification requirement.
            if rf.ambulance_detected and cv.ambulance_detected:
                print("\n[MAIN] VERIFICATION COMPLETE: RF Signal + Visual Confirmation.")
                # We assume Camera 1 is pointed at Lane 1 for our prototype setup.
                junction.activate_override(emergency_lane_number=1)
                
        # Override Monitor: Keep the light green until the ambulance leaves the area
        else:
            # If the camera no longer sees it AND the RF stops, it has driven past.
            if not rf.ambulance_detected and not cv.ambulance_detected:
                junction.reset_to_normal()
                
        # Handle the live Camera GUI in the Main Thread
        if hasattr(cv, 'current_frame') and cv.current_frame is not None:
            cv2.imshow("SHADOW-VIKING YOLO Scanner", cv.current_frame)
            if cv2.waitKey(30) & 0xFF == ord('q'):
                print("Manual GUI Exit")
                break
        else:
            time.sleep(0.05)

if __name__ == "__main__":
    print("==================================================")
    print("  Emergency Vehicle Traffic Hub OS - INIT         ")
    print("==================================================")
    
    # 1. Initialize our three core systems
    controller = TrafficController()
    rf_subsystem = RFReceiver()
    cv_subsystem = CVDetector(model_path='ambulance_model.pt', camera_index=0)
    
    try:
        rf_subsystem.setup()
    except RuntimeError as e:
        print(f"\n[!] Hardware Warning: {e}")
        print("[!] The main script will continue for testing purposes.")
        
    print("\nStarting background threads...")
    controller.run_normal_cycle_loop()
    rf_subsystem.start()
    cv_subsystem.start()
    
    print("\nSYSTEM FULLY OPERATIONAL. Standard traffic loops are running.")
    print("Monitoring for incoming sirens...")
    
    # 3. Hand control over to the core intersection logic loop
    try:
        check_for_override(rf_subsystem, cv_subsystem, controller)
    except KeyboardInterrupt:
        print("\nManual Shutdown Detected.")
    finally:
        cv_subsystem.stop()
        try:
            cv2.destroyAllWindows()
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except: pass
        print("Offline.")
