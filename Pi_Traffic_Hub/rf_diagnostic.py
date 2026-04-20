#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
  SHADOW-VIKING  |  NRF24L01+ Hardware Diagnostic Tool
═══════════════════════════════════════════════════════════════

Run this script STANDALONE to check if your NRF24L01+ module
is alive, correctly wired, and can see RF signals.

Usage:
    python3 rf_diagnostic.py

What it tests:
    1. SPI Bus connectivity (can the Pi talk to the chip?)
    2. Chip identification (is it a real nRF24L01+?)
    3. Register dump (full configuration readout)
    4. Channel scan (is there RF interference?)
    5. Live receive test (listens for 10 seconds for any data on 1AMB1)
"""

import sys
import time

def separator(title=""):
    print(f"\n{'═'*60}")
    if title:
        print(f"  {title}")
        print(f"{'═'*60}")

def main():
    separator("NRF24L01+ HARDWARE DIAGNOSTIC")
    print("  CE Pin: 22 (GPIO 22)")
    print("  CSN:    SPI Bus 0, Device 0")
    print("  Channel: 115")
    print("  Address: 1AMB1")
    print("  Data Rate: 250KBPS")

    # ──────────────────────────────────────────────
    # TEST 1: Can we even import the library?
    # ──────────────────────────────────────────────
    separator("TEST 1: Library Import")
    try:
        from pyrf24 import RF24, RF24_PA_MIN, RF24_PA_LOW, RF24_250KBPS
        print("  ✓ pyrf24 library imported successfully.")
    except ImportError:
        print("  ✗ FATAL: pyrf24 is NOT installed!")
        print("    Fix: pip install pyrf24")
        sys.exit(1)

    # ──────────────────────────────────────────────
    # TEST 2: SPI Initialization (radio.begin())
    # ──────────────────────────────────────────────
    separator("TEST 2: SPI Bus Init (radio.begin())")
    radio = RF24(22, 0)  # CE=22, CSN=SPI0
    
    if not radio.begin():
        print("  ✗ FATAL: radio.begin() returned False!")
        print("")
        print("  Diagnosis:")
        print("  ─ The Pi CANNOT talk to the NRF24L01+ chip over SPI.")
        print("  ─ This means either:")
        print("    1. SPI is not enabled  → Run: sudo raspi-config → Interfaces → SPI → Enable")
        print("    2. Wiring is wrong     → Double-check MOSI/MISO/SCK/CSN/CE pins")
        print("    3. Module is dead      → Try swapping with a spare NRF24L01+")
        print("    4. No 10µF capacitor   → Solder one across VCC/GND on the module")
        print("    5. Power issue         → NRF24L01+ needs 3.3V, never 5V")
        sys.exit(1)
    else:
        print("  ✓ radio.begin() succeeded — SPI communication is WORKING.")

    # ──────────────────────────────────────────────
    # TEST 3: Chip Connected Check
    # ──────────────────────────────────────────────
    separator("TEST 3: Chip Identity Verification")
    try:
        connected = radio.is_chip_connected
        if connected:
            print("  ✓ is_chip_connected = True — Chip is genuine and responsive.")
        else:
            print("  ✗ is_chip_connected = False!")
            print("  The chip responds on SPI but registers look wrong.")
            print("  Possible counterfeit/damaged module.")
    except (AttributeError, TypeError):
        print("  ⚠ is_chip_connected not available in this pyrf24 version.")
        print("    Skipping (begin() success suggests chip is fine).")

    # ──────────────────────────────────────────────
    # TEST 4: Check if it's an nRF24L01+ (plus variant)
    # ──────────────────────────────────────────────
    separator("TEST 4: Plus Variant Check")
    try:
        # pyrf24 exposes this as a property
        is_plus = radio.is_plus_variant
        if is_plus:
            print("  ✓ Module is an nRF24L01+ (plus variant) — supports 250KBPS.")
        else:
            print("  ⚠ Module is a standard nRF24L01 (NOT plus).")
            print("    250KBPS data rate may not work. Consider using 1MBPS.")
    except (AttributeError, TypeError):
        print("  ⚠ Cannot determine variant. Continuing anyway.")

    # ──────────────────────────────────────────────
    # TEST 5: Full Register Dump
    # ──────────────────────────────────────────────
    separator("TEST 5: Configuration Register Dump")
    print("  Configuring radio with project settings...")
    
    radio.setDataRate(RF24_250KBPS)
    radio.setPALevel(RF24_PA_MIN)
    radio.setChannel(115)
    radio.openReadingPipe(1, b"1AMB1")
    
    try:
        radio.payload_size = 1
    except:
        try:
            radio.setPayloadSize(1)
        except:
            pass
    
    print("")
    try:
        radio.printPrettyDetails()
    except AttributeError:
        try:
            radio.print_details()
        except AttributeError:
            try:
                radio.printDetails()
            except:
                print("  ⚠ Could not print register details (API not available).")
                print(f"    Channel:   {radio.channel if hasattr(radio, 'channel') else 'unknown'}")
                print(f"    PA Level:  {radio.pa_level if hasattr(radio, 'pa_level') else 'unknown'}")
                print(f"    Data Rate: {radio.data_rate if hasattr(radio, 'data_rate') else 'unknown'}")

    # ──────────────────────────────────────────────
    # TEST 6: RF Channel Noise Scan
    # ──────────────────────────────────────────────
    separator("TEST 6: RF Channel 115 Noise Check")
    print("  Scanning for ambient RF noise on channel 115...")
    print("  (Listening for 2 seconds)")
    
    radio.listen = True
    
    noise_hits = 0
    scan_start = time.time()
    while time.time() - scan_start < 2.0:
        try:
            rpd = radio.rpd
            if rpd:
                noise_hits += 1
        except (AttributeError, TypeError):
            try:
                rpd = radio.testRPD
                if rpd:
                    noise_hits += 1
            except:
                print("  ⚠ RPD not available. Skipping noise scan.")
                noise_hits = -1
                break
        time.sleep(0.01)
    
    if noise_hits >= 0:
        if noise_hits == 0:
            print(f"  ✓ Channel 115 is CLEAN — No RF interference detected.")
        elif noise_hits < 20:
            print(f"  ⚠ Light noise detected ({noise_hits} hits). Should be fine.")
        else:
            print(f"  ✗ HEAVY noise on channel 115 ({noise_hits} hits)!")
            print("    Consider changing to a different channel.")

    # ──────────────────────────────────────────────
    # TEST 7: Live Receive — Wait for ESP32 Transmitter
    # ──────────────────────────────────────────────
    separator("TEST 7: Live Receive Test (10 seconds)")
    print("  Listening for data on pipe 1 (address: 1AMB1)...")
    print("  *** Turn ON your ESP32 transmitter now! ***")
    print("")
    
    radio.listen = True
    
    received_count = 0
    listen_start = time.time()
    
    while time.time() - listen_start < 10.0:
        remaining = int(10 - (time.time() - listen_start))
        
        if radio.available:
            try:
                payload = radio.read(radio.payload_size)
                received_count += 1
                payload_hex = payload.hex() if payload else "empty"
                payload_val = payload[0] if len(payload) > 0 else "N/A"
                print(f"    📡 RECEIVED packet #{received_count}: raw={payload_hex} value={payload_val}")
                
                if len(payload) > 0 and payload[0] == 1:
                    print(f"       ✓ This is a valid SIREN=ON signal!")
                elif len(payload) > 0 and payload[0] == 0:
                    print(f"       ─ This is a SIREN=OFF signal.")
                else:
                    print(f"       ⚠ Unexpected payload value.")
            except Exception as e:
                print(f"    ✗ Read error: {e}")
        else:
            # Print countdown every second
            if int(time.time()) != int(time.time() - 0.05):
                sys.stdout.write(f"\r  Waiting... {remaining}s remaining  ")
                sys.stdout.flush()
        
        time.sleep(0.02)
    
    print("")
    
    if received_count > 0:
        print(f"\n  ✓ SUCCESS! Received {received_count} packets in 10 seconds.")
        print("    Your NRF24L01+ receiver is WORKING and communicating with the transmitter.")
    else:
        print(f"\n  ✗ No packets received in 10 seconds.")
        print("")
        print("  Possible causes:")
        print("  ─ ESP32 transmitter is not powered on or not sending")
        print("  ─ ESP32 address mismatch (must be exactly: 1AMB1)")
        print("  ─ ESP32 channel mismatch (must be exactly: 115)")
        print("  ─ ESP32 data rate mismatch (must be: 250KBPS)")
        print("  ─ Modules are too far apart (start with < 1 meter distance)")
        print("  ─ ESP32-side NRF24 module is dead")

    # ──────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────
    separator("DIAGNOSTIC SUMMARY")
    print("  SPI Communication:     ✓ Working")
    print(f"  Packets Received:      {'✓ ' + str(received_count) + ' packets' if received_count > 0 else '✗ None'}")
    
    if received_count > 0:
        print("\n  🟢 RF SYSTEM IS FULLY OPERATIONAL")
    else:
        print("\n  🟡 RF HARDWARE IS ALIVE BUT NO DATA FROM TRANSMITTER")
        print("     → The PI-SIDE module is fine. Check the ESP32 transmitter side.")
    
    print("")

if __name__ == '__main__':
    main()
