# Exact Big Breadboard Layout for Raspberry Pi (1-60, a-j)

This guide maps out the literal hole coordinates for every single wire to create a visually beautiful and hyper-organized 3-way junction on your large breadboard.

## The Rules for this Layout
- We will use the **Left Power Rails** (the long red/blue stripes) as our main power hub.
- We will route **ALL NRF24 signal lines** through the top left side (Rows 5-9, holes a-e).
- We will physically stick the **3 Traffic Light Modules** into the right side of the breadboard (Rows 20-43, hole j) and wire them across.

---

## 1. Master Power & Capacitor (The Foundation)
These wires supply the whole breadboard with 3.3V and Ground from the Pi.

| Component / Wire | From | To Exact Breadboard Hole |
|:---|:---|:---|
| **Pi Power Wire** | Raspberry Pi **Pin 1** (3.3V) | **Left Power Rail (+ Red)** (Any hole, e.g., row 1) |
| **Pi Ground Wire** | Raspberry Pi **Pin 6** (GND) | **Left Power Rail (- Blue)** (Any hole, e.g., row 1) |
| **100uF Capacitor** (+) | Long Leg of Capacitor | **Left Power Rail (+ Red)** (Any hole, e.g., row 2) |
| **100uF Capacitor** (-) | Short Leg of Capacitor | **Left Power Rail (- Blue)** (Any hole, e.g., row 2) |

---

## 2. NRF24L01 Receiver Hub
*(Attach Female-to-Male jumper wires to the NRF pins. We will plug the male ends into the breadboard's left side (holes a), and then run wires from holes (e) to the Raspberry Pi).*

| NRF Pin | Plug NRF Wire Into: | Plug secondary wire into: | Which goes to Pi Pin: |
|:---|:---|:---|:---|
| **VCC** (Pin 2) | **Left Power Rail (+ Red)** | *(No secondary wire)* | N/A |
| **GND** (Pin 1) | **Left Power Rail (- Blue)** | *(No secondary wire)* | N/A |
| **CE** (Pin 3) | **Row 5, Hole a** | **Row 5, Hole e** | Pi **Pin 15** |
| **CSN** (Pin 4) | **Row 6, Hole a** | **Row 6, Hole e** | Pi **Pin 24** |
| **SCK** (Pin 5) | **Row 7, Hole a** | **Row 7, Hole e** | Pi **Pin 23** |
| **MOSI** (Pin 6) | **Row 8, Hole a** | **Row 8, Hole e** | Pi **Pin 19** |
| **MISO** (Pin 7) | **Row 9, Hole a** | **Row 9, Hole e** | Pi **Pin 21** |

---

## 3. Traffic Light Modules (Physical Placement)
*(Most traffic light modules have 4 pins in a straight line: `GND, R, Y, G`. We will physically stick the entire modules into the `j` holes on the right side of the board so they stand up like real traffic lights!)*

### LANE 1 Traffic Light
*Push the module's 4 pins into `Row 20j`, `21j`, `22j`, and `23j`.*

| Module Pin in Board | What it is | Wire from Board Hole: | To Destination: |
|:---|:---|:---|:---|
| **Row 20, Hole j** | Module GND | **Row 20, Hole f** | **Left Power Rail (- Blue)** |
| **Row 21, Hole j** | Module RED | **Row 21, Hole f** | Pi **Pin 7** |
| **Row 22, Hole j** | Module YELLOW | **Row 22, Hole f** | Pi **Pin 11** |
| **Row 23, Hole j** | Module GREEN | **Row 23, Hole f** | Pi **Pin 13** |

### LANE 2 Traffic Light
*Push the module's 4 pins into `Row 30j`, `31j`, `32j`, and `33j`.*

| Module Pin in Board | What it is | Wire from Board Hole: | To Destination: |
|:---|:---|:---|:---|
| **Row 30, Hole j** | Module GND | **Row 30, Hole f** | **Left Power Rail (- Blue)** |
| **Row 31, Hole j** | Module RED | **Row 31, Hole f** | Pi **Pin 29** |
| **Row 32, Hole j** | Module YELLOW | **Row 32, Hole f** | Pi **Pin 31** |
| **Row 33, Hole j** | Module GREEN | **Row 33, Hole f** | Pi **Pin 33** |

### LANE 3 Traffic Light
*Push the module's 4 pins into `Row 40j`, `41j`, `42j`, and `43j`.*

| Module Pin in Board | What it is | Wire from Board Hole: | To Destination: |
|:---|:---|:---|:---|
| **Row 40, Hole j** | Module GND | **Row 40, Hole f** | **Left Power Rail (- Blue)** |
| **Row 41, Hole j** | Module RED | **Row 41, Hole f** | Pi **Pin 36** |
| **Row 42, Hole j** | Module YELLOW | **Row 42, Hole f** | Pi **Pin 38** |
| **Row 43, Hole j** | Module GREEN | **Row 43, Hole f** | Pi **Pin 40** |


*(Note: If your traffic light modules have a different pin order, like `Green, Yellow, Red, GND`, just make sure the `GND` lines always route back to the Left Blue Power Rail, and the colored signals route to their matching Pi Pin).*
