#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

/*
 * EMERGENCY VEHICLE TRANSMITTER (AMBULANCE)
 * Uses ESP32 and NRF24L01 PA LNA
 * 
 * Hardware Layout (ESP32 VSPI Default):
 * NRF SCK   -> ESP32 Pin 18
 * NRF MISO  -> ESP32 Pin 19
 * NRF MOSI  -> ESP32 Pin 23
 * NRF CE    -> ESP32 Pin 4
 * NRF CSN   -> ESP32 Pin 5
 * NRF VCC   -> 3.3V (10uF capacitor between VCC & GND!)
 * NRF GND   -> GND
 * 
 * SWITCH:
 * Pin 1 of Switch -> ESP32 Pin 13
 * Pin 2 of Switch -> GND
 */

#define CE_PIN 4
#define CSN_PIN 5
#define SIREN_SWITCH_PIN 13 

RF24 radio(CE_PIN, CSN_PIN);

const byte address[6] = "1AMB1"; 

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  pinMode(SIREN_SWITCH_PIN, INPUT_PULLUP); 

  // === SWITCH DIAGNOSTIC ===
  Serial.println("\n=== SWITCH PIN DIAGNOSTIC ===");
  Serial.print("Reading pin ");
  Serial.print(SIREN_SWITCH_PIN);
  Serial.println(" five times (1 sec apart):");
  Serial.println("Toggle your switch between reads to verify it works!");
  Serial.println("");
  
  for (int i = 1; i <= 5; i++) {
    int val = digitalRead(SIREN_SWITCH_PIN);
    Serial.print("  Read #");
    Serial.print(i);
    Serial.print(": pin ");
    Serial.print(SIREN_SWITCH_PIN);
    Serial.print(" = ");
    Serial.print(val);
    Serial.print(" (");
    Serial.print(val == HIGH ? "HIGH" : "LOW");
    Serial.println(")");
    delay(1000);
  }
  Serial.println("=== END DIAGNOSTIC ===\n");
  Serial.println("If all reads were the same value, the switch is NOT working.");
  Serial.println("Try: disconnect switch, manually touch pin 13 wire to GND.");
  Serial.println("");

  // === NRF24 INIT ===
  Serial.println("Initializing NRF24L01...");
  if (!radio.begin()) {
    Serial.println("NRF24L01 hardware not responding!");
    while (1) {} 
  }

  radio.setDataRate(RF24_250KBPS); 
  radio.setPALevel(RF24_PA_MIN); 
  radio.setChannel(115);
  radio.setPayloadSize(1);
  radio.openWritingPipe(address);
  radio.stopListening();
  
  Serial.println("TRANSMITTER READY. (Auto-ACK disabled)\n");
}

void loop() {
  int rawPin = digitalRead(SIREN_SWITCH_PIN);
  bool sirenActive = (rawPin == LOW);  // LOW = switch connecting pin to GND
  
  byte payload[1] = { sirenActive ? (byte)1 : (byte)0 };
  bool success = radio.write(payload, 1);
  
  // Print raw pin value so we can see exactly what's happening
  Serial.print("Pin13=");
  Serial.print(rawPin);
  Serial.print(" → ");
  
  if (sirenActive) {
    Serial.print("SIREN=ON (0x01) ");
    Serial.println(success ? "TX:OK" : "TX:FAIL");
    delay(50);
  } else {
    Serial.print("siren=off (0x00) ");
    Serial.println(success ? "tx:ok" : "TX:FAIL");
    delay(200);
  }
}
