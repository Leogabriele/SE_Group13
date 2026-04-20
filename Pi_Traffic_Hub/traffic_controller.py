import time
import threading
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("WARNING: RPi.GPIO not installed. Using mocked logic for testing.")
    class GPIO: 
        BCM = OUT = LOW = 1
        @staticmethod
        def setmode(*a): pass
        @staticmethod
        def setwarnings(*a): pass
        @staticmethod
        def setup(*a): pass
        @staticmethod
        def output(*a): pass

class TrafficController:
    def __init__(self):
        # We hook the 3 small traffic signal modules directly to Pi GPIOs
        # Map: Lane Num -> (Red_Pin, Yellow_Pin, Green_Pin) using standard BCM numbering
        # We carefully selected pins that DO NOT collide with the SPI pins used by the NRF24 radio.
        self.lane_pins = {
            1: (4, 17, 27),   # Lane 1 (Pins 7, 11, 13)
            2: (5, 6, 13),    # Lane 2 (Pins 29, 31, 33)
            3: (16, 20, 21)   # Lane 3 (Pins 36, 38, 40)
        }
        
        self.current_lane = 1
        self.emergency_override = False
        self.pre_override_lane = 1  # Which lane was green before the override
        # Track per-lane light state for dashboard display
        self.lane_states = {1: 'red', 2: 'red', 3: 'red'}
        
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        for lane, pins in self.lane_pins.items():
            for pin in pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)

    def set_lights(self, lane, r, y, g):
        # Helper to set all 3 LEDs for a specific lane. 1 = ON, 0 = OFF
        GPIO.output(self.lane_pins[lane][0], r)
        GPIO.output(self.lane_pins[lane][1], y)
        GPIO.output(self.lane_pins[lane][2], g)
        # Track state for dashboard
        if g:
            self.lane_states[lane] = 'green'
        elif y:
            self.lane_states[lane] = 'yellow'
        else:
            self.lane_states[lane] = 'red'

    def transition_to_red(self, lane):
        """The critical safety mechanic: safely transition a green lane to red."""
        print(f"[{time.strftime('%H:%M:%S')}] Safely transitioning Lane {lane} to Red (5s Yellow)")
        self.set_lights(lane, 0, 1, 0)
        time.sleep(5)
        self.set_lights(lane, 1, 0, 0)

    def run_timed_override(self, emergency_lane_number=1, green_duration=10):
        """
        Self-terminating emergency override:
        1. Save which lane was green before
        2. Transition that lane safely to red
        3. Give emergency lane solid green for `green_duration` seconds
        4. After timer expires, transition emergency lane to red
        5. Resume normal cycle from the lane that was green before the override
        """
        self.emergency_override = True
        self.pre_override_lane = self.current_lane
        print(f"\n!!! --- OVERRIDE INITIATED --- !!!")
        print(f"[{time.strftime('%H:%M:%S')}] Saving pre-override lane: Lane {self.pre_override_lane}")
        
        # Step 1: Safely transition the currently green lane to red (unless it's the emergency lane)
        if self.current_lane != emergency_lane_number:
            self.transition_to_red(self.current_lane)
        
        # Step 2: All lanes red except emergency lane gets green
        for l in [1, 2, 3]:
            if l == emergency_lane_number:
                self.set_lights(l, 0, 0, 1)  # Solid Green
                self.current_lane = l
            else:
                self.set_lights(l, 1, 0, 0)  # Solid Red
                
        print(f"!!! OVERRIDE ACTIVE: Lane {emergency_lane_number} GREEN for {green_duration}s !!!")
        
        # Step 3: Hold green for the specified duration
        time.sleep(green_duration)
        
        # Step 4: Transition emergency lane back to red safely
        print(f"[{time.strftime('%H:%M:%S')}] Override timer expired. Transitioning back...")
        self.transition_to_red(emergency_lane_number)
        
        # Step 5: Resume from the lane that was green before the override
        self.current_lane = self.pre_override_lane
        self.emergency_override = False
        print(f"[{time.strftime('%H:%M:%S')}] Override complete. Resuming from Lane {self.pre_override_lane}.\n")

    def run_normal_cycle_loop(self):
        """Runs the standard Red->Yellow->Green cycle in a background thread."""
        t = threading.Thread(target=self._cycle_logic)
        t.daemon = True
        t.start()

    def _cycle_logic(self):
        # Continuous loop for regular traffic behavior
        while True:
            for lane in [1, 2, 3]:
                if self.emergency_override:
                    time.sleep(1) # We wait dormantly while override is handling the lights
                    continue
                    
                self.current_lane = lane
                
                # Make current lane Green, all others Red
                for other_lane in [1, 2, 3]:
                    if other_lane != lane:
                        self.set_lights(other_lane, 1, 0, 0)
                self.set_lights(lane, 0, 0, 1)
                
                # Stay green for 10 seconds (in small increments for override responsiveness)
                for _ in range(100):
                    if self.emergency_override: break
                    time.sleep(0.1)
                
                if self.emergency_override: continue
                
                # Transition to Yellow for 3 seconds
                self.set_lights(lane, 0, 1, 0)
                for _ in range(30):
                    if self.emergency_override: break
                    time.sleep(0.1)
                    
                if self.emergency_override: continue
                # Loop moves to next lane
