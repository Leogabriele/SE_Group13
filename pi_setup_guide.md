# Raspberry Pi 4 First-Time Setup Guide

Since you just installed the OS, we need to do a little bit of prep work so the Raspberry Pi can talk to the radio module, access the camera, and run the AI models.

## Step 1: Boot Up & Network
1. Connect your Raspberry Pi to a monitor using your **micro HDMI to HDMI cable**.
2. Connect a USB mouse and keyboard.
3. Power the Pi on.
4. Once on the desktop, connect it to your Wi-Fi network (top right corner).

## Step 2: Enable Hardware Features (SPI & Camera)
The Raspberry Pi has its hardware pins "locked" by default. We have to unlock the SPI bus so the Pi can understand the NRF24 radio module.
1. Open the **Terminal** (the black box icon at the top of the screen).
2. Type `sudo raspi-config` and press Enter.
3. Use your arrow keys to go down to `3 Interface Options` and press Enter.
4. Go to `I4 SPI` and press Enter. Select **Yes** to enable the SPI interface.
5. Go back to `Interface Options`. Look for a **Camera** or **Legacy Camera** option. Select it and choose **Yes** to enable the camera port.
6. Exit the menu and **Reboot** the Pi.

## Step 3: Transfer the Code
You are currently viewing this project on your main computer, but the code needs to run on the Pi.
1. Get a standard USB Flash Drive.
2. Copy the entire `Pi_Traffic_Hub` folder from this computer onto the USB drive.
3. Copy your custom `ambulance_model.pt` weights file into that `Pi_Traffic_Hub` folder as well.
4. Plug the USB drive into the Raspberry Pi and drag the folder onto the Pi's Desktop.

## Step 4: Install the Python Libraries
Newer Raspberry Pi operating systems protect their main Python installation, so we use a "Virtual Environment" to install your specific AI and hardware libraries.

1. Open the Terminal on your Raspberry Pi.
2. Navigate to the folder you just copied:
   ```bash
   cd ~/Desktop/Pi_Traffic_Hub
   ```
3. Create a python virtual environment:
   ```bash
   python3 -m venv venv
   ```
4. Activate it:
   ```bash
   source venv/bin/activate
   ```
   *(You should see `(venv)` appear at the start of your terminal line).*
5. Install the required libraries:
   ```bash
   pip install -r requirements.txt
   ```
   *(This step might take 5-10 minutes because Ultralytics and OpenCV are large libraries).*

## Step 5: Plug In the Hardware
While it installs, you can wire the hardware directly to the Pi's GPIO pins.

**The Camera**:
- Lift the tab on the "CAMERA" port (located between the HDMI and Audio jack). Slide the ribbon cable in (silver contacts facing the HDMI ports), and press the tab gently down to lock it.

**The NRF24L01 Receiver**:
*(Use female-to-female jumper wires to connect the module directly to the matching pins on the Pi)*
- **VCC:** Pin 1 (3.3V) -> *Remember to plug your 100uF capacitor across VCC and GND here too!*
- **GND:** Pin 6 (Ground)
- **CE:** Pin 15 (GPIO 22)
- **CSN:** Pin 24 (GPIO 8 / SPI0 CE0)
- **SCK:** Pin 23 (GPIO 11)
- **MISO:** Pin 21 (GPIO 9)
- **MOSI:** Pin 19 (GPIO 10)

**The Traffic Lights**:
- Connect their grounds to any available Pi Ground (like Pin 9, 39, etc.).
- Connect the signal wires directly to:
  - **Lane 1 module:** Red=Pin 11, Yel=Pin 13, Grn=Pin 15
  - **Lane 2 module:** Red=Pin 19, Yel=Pin 21, Grn=Pin 23
  - **Lane 3 module:** Red=Pin 29, Yel=Pin 31, Grn=Pin 33

## Step 6: Start the System!
Once everything is wired and the pip installation finishes, make sure you are in the folder and type:
```bash
# Don't forget to run 'source venv/bin/activate' first if you closed the terminal!
python3 main.py
```
