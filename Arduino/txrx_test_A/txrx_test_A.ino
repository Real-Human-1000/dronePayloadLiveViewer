// Feather9x_TX
// -*- mode: C++ -*-
// Example sketch showing how to create a simple messaging client (transmitter)
// with the RH_RF95 class. RH_RF95 class does not provide for addressing or
// reliability, so you should only use RH_RF95 if you do not need the higher
// level messaging abilities.
// It is designed to work with the other example Feather9x_RX

#include <SPI.h>
#include <RH_RF95.h>

//#define PRINT_SERIAL

// // Feather 32u4 wired to RFM95 breakout:
// #define RFM95_CS   5
// #define RFM95_RST  12
// #define RFM95_INT  0

// Feather 32u4 w/ LoRa:
#define RFM95_CS   8
#define RFM95_RST  4
#define RFM95_INT  7

// Change to 434.0 or other frequency, must match RX's freq!
#define RF95_FREQ 434.0

// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  //pinMode(RFM95_INT, INPUT);
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  #ifdef PRINT_SERIAL
    Serial.begin(115200);
    while (!Serial) delay(1);
    delay(100);
    Serial.println("Feather LoRa TX Test!");
  #endif

  // manual reset
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  while (!rf95.init()) {
    #ifdef PRINT_SERIAL
      Serial.println("LoRa radio init failed");
      Serial.println("Uncomment '#define SERIAL_DEBUG' in RH_RF95.cpp for detailed debug info");
    #endif
    while (1);
  }
  #ifdef PRINT_SERIAL
    Serial.println("LoRa radio init OK!");
  #endif

  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM
  if (!rf95.setFrequency(RF95_FREQ)) {
    #ifdef PRINT_SERIAL
      Serial.println("setFrequency failed");
    #endif
    while (1);
  }
  #ifdef PRINT_SERIAL
    Serial.print("Set Freq to: "); Serial.println(RF95_FREQ);
  #endif

  // Defaults after init are 434.0MHz, 13dBm, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on
  //rf95.setSpreadingFactor(12);

  // The default transmitter power is 13dBm, using PA_BOOST.
  // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then
  // you can set transmitter powers from 5 to 23 dBm:
  rf95.setTxPower(23, false);
}

int16_t packetnum = 0;  // packet counter, we increment per xmission

void loop() {
  delay(250); // Wait 1 second between transmits, could also 'sleep' here!
  #ifdef PRINT_SERIAL
    Serial.print("Init, Sleep, Cad, Idle, Rx, Tx: "); Serial.print(rf95.RHModeInitialising); Serial.print(rf95.RHModeSleep); Serial.print(rf95.RHModeCad); Serial.print(rf95.RHModeIdle); Serial.print(rf95.RHModeRx); Serial.println(rf95.RHModeTx);
  #endif
  digitalWrite(LED_BUILTIN, HIGH);
  #ifdef PRINT_SERIAL
    Serial.println("Transmitting..."); // Send a message to rf95_server
  #endif

  char radiopacket[35] = "Hello World this is message #      ";
  itoa(packetnum++, radiopacket+29, 10);
  #ifdef PRINT_SERIAL
    Serial.print("Sending "); Serial.println(radiopacket);
  #endif
  radiopacket[35] = 0;

  #ifdef PRINT_SERIAL
    Serial.println("Sending...");
  #endif
  delay(10);
  rf95.send((uint8_t *)radiopacket, 35);

  #ifdef PRINT_SERIAL
    Serial.println("Waiting for packet to complete...");
  #endif
  rf95.waitPacketSent();
  // Now wait for a reply
  uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
  uint8_t len = sizeof(buf);

  digitalWrite(LED_BUILTIN, LOW);
  #ifdef PRINT_SERIAL
    Serial.println("Waiting for reply...");
  #endif
  if (rf95.waitAvailableTimeout(1000)) {
    // Should be a reply message for us now
    if (rf95.recv(buf, &len)) {
      #ifdef PRINT_SERIAL
        Serial.print("Got reply: ");
        Serial.println((char*)buf);
        Serial.print("RSSI: ");
        Serial.println(rf95.lastRssi(), DEC);
      #endif
    } else {
      #ifdef PRINT_SERIAL
        Serial.println("Receive failed");
      #endif
    }
  } else {
    #ifdef PRINT_SERIAL
      Serial.println("No reply, is there a listener around?");
    #endif
  }

}
