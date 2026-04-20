# Complete Breadboard Connection Guide

Since you are not hooking the ESP32 directly into the breadboard and skipping the TP4056, we will use the small breadboard purely as a **Junction Hub** to distribute the power and hold the capacitor and the switch safely.

## 1. How the Breadboard Works (1-30, a-j)
Your small breadboard is split down the middle by a trench. 
- **Rows**: Numbered 1 to 30.
- **Columns**: `a, b, c, d, e` are on the left, and `f, g, h, i, j` are on the right.
- **The Golden Rule**: Any hole in the **same row and same side** is electrically connected. 
  - (For example, plugging a wire into `Row 1a` and `Row 1c` makes them share the same electricity, but `Row 1a` and `Row 1f` do NOT because the gap separates them).

> [!WARNING]  
> The NRF24L01 has a 2x4 grid pinout at the bottom. **Never** plug it directly into a breadboard! If you do, it shorts out its own pins (VCC connects to GND). You must use Female-to-Male jumper wires to attach the NRF24L01 headers and plug the male ends into the setup below.

---

## 2. The Layout System
We are going to designate **Row 5** as our `3.3V Power Line`, **Row 10** as our `Ground (GND) Line`, and **Row 15** as our `Signal Line`.

Plug everything into the exact coordinates listed below.

| What you are holding | Where to plug it | What it does |
|---|---|---|
| **POWER FROM ESP32** | | |
| Wire coming from ESP32 `3V3` Pin | Plug into **Row 5, Hole a** | Electrifies Row 5 with 3.3 Volts |
| Wire coming from ESP32 `GND` Pin | Plug into **Row 10, Hole a** | Connects Row 10 to Ground |
| | | |
| **STABILITY CAPACITOR (10uF)** | | |
| Capacitor LONG Leg(+) | Plug into **Row 5, Hole b** | Pulls 3.3V power |
| Capacitor SHORT Leg(-) | Plug into **Row 10, Hole b** | Connects to Ground. *(Prevents NRF crashes!)* |
| | | |
| **NRF24L01 TRANSCEIVER** | *(Use female-to-male wire)* | |
| NRF24 VCC (Pin 2) wire | Plug into **Row 5, Hole c** | Powers the Radio |
| NRF24 GND (Pin 1) wire | Plug into **Row 10, Hole c** | Grounds the Radio |
| NRF24 Data Wires (Pins 3-7) | **Connect these directly to your ESP32** Pins (18, 19, 23, 4, 5) | Skips breadboard to prevent messy wiring. |
| | | |
| **THE SWITCH (Haitonc RS-12)** | *(Switch has 2 pins/prongs)* | |
| Switch Prong 1 | Plug into **Row 5, Hole d** | Grabs 3.3V power |
| Switch Prong 2 | Plug into **Row 15, Hole a** | Creates a live Signal Line when Switched ON |
| | | |
| **THE 10k RESISTOR** | | |
| Resistor Leg 1 | Plug into **Row 15, Hole b** | Connects to the Switch Signal |
| Resistor Leg 2 | Plug into **Row 10, Hole d** | Pulls the signal to Ground when switch is OFF |
| | | |
| **ESP32 SENSOR WIRE** | | |
| Empty Wire (Male to Female usually) | Plug into **Row 15, Hole c** | Reads the switch |
| Other end of that Wire | Connect directly to ESP32 Pin **13** | Tells Arduino if SIREN is ON or OFF |


### Why the Resistor is there (The Pull-Down Circuit)
If you don't use the resistor, when you turn the switch OFF, ESP32 Pin 13 is practically "floating" in the air like an antenna and picks up random radio noise, causing fake Ambulance detections! Providing a 10k resistor to Ground (Row 10) holds the pin gently at 0 Volts until the switch punches 3.3 Volts through, overpowering it reliably.

---

## 3. Powering the ESP32 using Batteries
Since you aren't using the TP-4056 USB charger, you must power the ESP32 directly via your batteries.
- **Batteries**: Assuming you are using a standard Lithium battery (which scales from 3.7V to 4.2V), or even your standard double battery pack:
- **Positive (Red) Wire**: Plug it into the ESP32 pin labeled `VIN` (or `5V`).
  - *❗ DO NOT plug a bare 4.2V battery into the ESP32's `3V3` pin, it will fry the board. The `VIN` pin goes through a safe regulator down to 3.3v.*
- **Negative (Black) Wire**: Plug into any ESP32 `GND` pin.
