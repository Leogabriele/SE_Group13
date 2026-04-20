import time
import threading
try:
    from pyrf24 import RF24, RF24_PA_MIN, RF24_250KBPS
    PYRF24_AVAILABLE = True
except ImportError:
    print("WARNING: pyrf24 library not installed. RF Module will not function.")
    PYRF24_AVAILABLE = False
    RF24_PA_MIN = 0
    RF24_250KBPS = 0

class RFReceiver:
    def __init__(self):
        self.radio = None
        self.address = b"1AMB1"
        self.ambulance_detected = False
        self.running = False
        self.hw_online = False
        self.last_packet_time = 0
        self.total_packets = 0
        self.siren_on_packets = 0
        self.last_payload_val = None
        self.packets_per_sec = 0.0    # Tracks actual packet rate
        self.esp32_connected = False  # True when we see real ESP32 traffic (>3 pkt/sec)
        self.diag_info = "Not initialized"
        
    def setup(self):
        if not PYRF24_AVAILABLE:
            self.diag_info = "pyrf24 library not installed"
            raise RuntimeError("pyrf24 library not installed. Cannot use RF hardware.")
        
        self.radio = RF24(22, 0)
        
        if not self.radio.begin():
            self.diag_info = "SPI FAIL: radio.begin() returned False"
            raise RuntimeError("NRF24L01 SPI init failed!")
        
        try:
            if hasattr(self.radio, 'is_chip_connected'):
                if not self.radio.is_chip_connected:
                    raise RuntimeError("NRF24L01 chip registers invalid")
        except (AttributeError, TypeError):
            pass
        
        self.radio.setDataRate(RF24_250KBPS)
        self.radio.setPALevel(RF24_PA_MIN)
        self.radio.setChannel(115)
        self.radio.openReadingPipe(1, self.address)
        self.radio.payload_size = 1
        
        # Flush any stale data from RX FIFO
        try:
            self.radio.flush_rx()
        except:
            pass
        
        self.radio.listen = True
        
        self.hw_online = True
        self.diag_info = "Online — Listening on ch115 / 1AMB1"
        print("RF Receiver initialized successfully. Listening on pipeline 1AMB1.")

    def start(self):
        if not self.hw_online:
            self.diag_info = "Cannot start: hardware not initialized"
            return
        self.running = True
        t = threading.Thread(target=self._poll_for_emergency)
        t.daemon = True
        t.start()

    def _poll_for_emergency(self):
        last_siren_time = 0
        debug_printed = 0
        
        # Packet rate tracking
        rate_window_start = time.time()
        rate_window_count = 0
        
        while self.running:
            try:
                if self.radio and self.radio.available:
                    # Read the payload
                    try:
                        payload = self.radio.read(self.radio.payload_size)
                    except TypeError:
                        payload = self.radio.read()
                    
                    now = time.time()
                    self.last_packet_time = now
                    self.total_packets += 1
                    rate_window_count += 1
                    
                    # Calculate packet rate every 2 seconds
                    elapsed = now - rate_window_start
                    if elapsed >= 2.0:
                        self.packets_per_sec = rate_window_count / elapsed
                        # Real ESP32 sends at least 5 pkt/sec (200ms heartbeat when idle)
                        self.esp32_connected = self.packets_per_sec >= 3.0
                        rate_window_count = 0
                        rate_window_start = now
                    
                    # Debug: print first 20 packets + every 200th
                    if debug_printed < 20 or self.total_packets % 200 == 0:
                        debug_printed += 1
                        print(f"  [RF PKT #{self.total_packets}] "
                              f"val={payload[0] if payload else '?'} "
                              f"hex={payload.hex() if payload else '??'} "
                              f"rate={self.packets_per_sec:.1f}/s "
                              f"esp32={'YES' if self.esp32_connected else 'NO'}")
                    
                    # Extract the siren value
                    raw_val = payload[0] if payload and len(payload) > 0 else None
                    self.last_payload_val = raw_val
                    
                    if raw_val is not None and raw_val > 0:
                        self.siren_on_packets += 1
                        self.ambulance_detected = True
                        last_siren_time = now
                        self.diag_info = (f"SIREN ON (val={raw_val}, "
                                         f"{self.packets_per_sec:.0f} pkt/s)")
                    else:
                        if self.esp32_connected:
                            self.diag_info = (f"Heartbeat OK, siren OFF "
                                             f"({self.packets_per_sec:.0f} pkt/s)")
                        else:
                            self.diag_info = (f"Low traffic ({self.packets_per_sec:.1f} pkt/s) "
                                             f"— noise or ESP32 offline")
                        
            except Exception as e:
                self.diag_info = f"Read error: {str(e)[:50]}"
                if debug_printed < 20:
                    debug_printed += 1
                    print(f"  [RF ERROR] {e}")
                time.sleep(0.1)
                continue
                    
            # If we don't hear a siren ping for 2 seconds, reset
            if self.ambulance_detected and (time.time() - last_siren_time > 2.0):
                self.ambulance_detected = False
                self.diag_info = f"Siren timeout ({self.packets_per_sec:.0f} pkt/s)"
                
            time.sleep(0.05)
            
    def get_diagnostic(self):
        return {
            'hw_online': self.hw_online,
            'lib_available': PYRF24_AVAILABLE,
            'total_packets': self.total_packets,
            'siren_packets': self.siren_on_packets,
            'packets_per_sec': round(self.packets_per_sec, 1),
            'esp32_connected': self.esp32_connected,
            'last_packet_age': round(time.time() - self.last_packet_time, 1) if self.last_packet_time > 0 else -1,
            'last_payload_val': self.last_payload_val,
            'siren_active': self.ambulance_detected,
            'info': self.diag_info
        }
            
    def reset_flag(self):
        self.ambulance_detected = False
