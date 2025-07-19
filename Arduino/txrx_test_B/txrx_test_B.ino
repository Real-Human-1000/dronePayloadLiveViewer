// Feather9x_RX
// -*- mode: C++ -*-
// Example sketch showing how to create a simple messaging client (receiver)
// with the RH_RF95 class. RH_RF95 class does not provide for addressing or
// reliability, so you should only use RH_RF95 if you do not need the higher
// level messaging abilities.
// It is designed to work with the other example Feather9x_TX

#define PRINT_SERIAL

#include <SPI.h>
#include <RH_RF95.h>

// // Feather 32u4 w/ LoRa:
// #define RFM95_CS   8
// #define RFM95_RST  4
// #define RFM95_INT  7

// Feather 32u4 wired to RFM95 breakout:
#define RFM95_CS   5
#define RFM95_RST  12
#define RFM95_INT  0

// Change to 434.0 or other frequency, must match RX's freq!
#define RF95_FREQ 434.0

// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);

// Single buffer and length of buffer to use for receiving
uint8_t recv_buf[RH_RF95_MAX_MESSAGE_LEN];
uint8_t recv_buf_len = sizeof(recv_buf);  // note that this gets reset to the number of bytes received/copied when rf95.recv() is called

// Buffer for the actual message in the most recent packet
char recv_message[RH_RF95_MAX_MESSAGE_LEN];
uint8_t recv_message_len = sizeof(recv_buf);  // this will not be reset; memory will just be copied into it

byte blocking_recv() {
  // Wait for a reply
  if (rf95.waitAvailableTimeout(3000)) {
    // Should be a reply message for us now
    if (rf95.recv(recv_buf, &recv_buf_len)) {
      #ifdef PRINT_SERIAL
        Serial.print("recv_buf_len: "); Serial.print(recv_buf_len); Serial.print(", recv_buf: "); Serial.println((char*)recv_buf);
      #endif
      if (recv_buf_len > 6) {
        memcpy(&recv_message, &recv_buf[6], recv_buf_len - 6);
        recv_message_len = recv_buf_len - 6;
        #ifdef PRINT_SERIAL
          Serial.print("recv_message: "); Serial.println(recv_message);
        #endif
        return 1;  // set so I can do "if (blocking_recv())"
      } else {
        #ifdef PRINT_SERIAL
          Serial.println("Packet isn't long enough!");
        #endif
        return 0;
      }
    } else {
      #ifdef PRINT_SERIAL
        Serial.println("Receive failed");
      #endif
      return 0;
    }
  } else {
    #ifdef PRINT_SERIAL
      Serial.println("No reply, is there a listener around?");
    #endif
    return 0;
  }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  Serial.begin(115200);
  while (!Serial) delay(1);
  delay(100);

  Serial.println("Feather LoRa RX Test!");

  // manual reset
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  while (!rf95.init()) {
    Serial.println("LoRa radio init failed");
    Serial.println("Uncomment '#define SERIAL_DEBUG' in RH_RF95.cpp for detailed debug info");
    while (1);
  }
  Serial.println("LoRa radio init OK!");

  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM
  if (!rf95.setFrequency(RF95_FREQ)) {
    Serial.println("setFrequency failed");
    while (1);
  }
  Serial.print("Set Freq to: "); Serial.println(RF95_FREQ);

  // Defaults after init are 434.0MHz, 13dBm, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on
  //rf95.setSpreadingFactor(12);

  // The default transmitter power is 13dBm, using PA_BOOST.
  // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then
  // you can set transmitter powers from 5 to 23 dBm:
  rf95.setTxPower(23, false);

  rf95.setModeRx();

  Serial.print("Radio mode, receive mode: "); Serial.print(rf95.mode()); Serial.print(", "); Serial.println(rf95.RHModeRx);
}

void loop() {
  if (rf95.available()) {
    Serial.println("Packet is available!");
    // Should be a message for us now
    // uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
    // uint8_t len = sizeof(buf);

    if (blocking_recv()) {
      digitalWrite(LED_BUILTIN, HIGH);
      RH_RF95::printBuffer("Received: ", recv_buf, recv_buf_len);
      Serial.print("Got: ");
      Serial.println((char*)recv_buf);
      Serial.print("RSSI: ");
      Serial.println(rf95.lastRssi(), DEC);
      Serial.println(recv_message);

      // Send a reply
      uint8_t data[] = "And hello back to you";
      rf95.send(data, sizeof(data));
      rf95.waitPacketSent();
      Serial.println("Sent a reply");
      digitalWrite(LED_BUILTIN, LOW);
    } else {
      Serial.println("Receive failed");
    }
  }
}
