#include <SPI.h>
// #include <RH_RF95.h>
#include <LoRa.h>

// Feather 32u4 w/ LoRa:
#define RFM95_CS   8
#define RFM95_RST  4
#define RFM95_INT  7

// Change to 434.0 or other frequency, must match RX's freq!
#define RF95_FREQ 434.0

// Singleton instance of the radio driver
// RH_RF95 rf95(RFM95_CS, RFM95_INT);

void setup() {
  // put your setup code here, to run once:
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  Serial.begin(115200);
  while (!Serial) delay(1);
  delay(100);

  Serial.println("Waiting for packets...");

  // manual reset
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  // while (!rf95.init()) {
  //   Serial.println("LoRa radio init failed");
  //   while (1);
  // }
  // Serial.println("LoRa radio init OK!");

  // // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM
  // if (!rf95.setFrequency(RF95_FREQ)) {
  //   Serial.println("setFrequency failed");
  //   while (1);
  // }
  // Serial.print("Set Freq to: "); Serial.println(RF95_FREQ);

  // // Defaults after init are 434.0MHz, 13dBm, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on
  // rf95.setSpreadingFactor(9);

  // The default transmitter power is 13dBm, using PA_BOOST.
  // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then
  // you can set transmitter powers from 5 to 23 dBm:
  //rf95.setTxPower(23, false);

  LoRa.setPins(RFM95_CS, RFM95_RST, RFM95_INT);
  if (!LoRa.begin(RF95_FREQ * 1000000)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }
  LoRa.setSpreadingFactor(9);
}

void loop() {
  // put your main code here, to run repeatedly:
  // if (rf95.available()) {
  //   // Get the message
  //   byte buf[RH_RF95_MAX_MESSAGE_LEN];
  //   byte len = sizeof(buf);

  //   if (rf95.recv(buf, &len)) {
  //     Serial.write(buf, len);
  //   }
  //   delay(100);
  // }

  // try to parse packet
  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    // received a packet
    // read packet
    // Serial.println(packetSize);
    char buf [packetSize] = {};
    byte idx = 0;
    // Serial.println(packetSize);
    // Serial.println(LoRa.available());
    while (LoRa.available()) {
      char c = (char)LoRa.read();
      // Serial.print(c);
      memcpy(&buf[idx], &c, 1);
      idx++;
      // for (byte i = 0; i < 16; i++) {
      //   Serial.print(bitRead(c, i));
      // }
      // Serial.print("-");
    }
    Serial.write(buf, packetSize);
    Serial.println();
    // for (byte e = 0; e < sizeof(buf); e++) {
    //   for (byte i = 0; i < sizeof(buf[e]) * 8; i++) {
    //     Serial.print(bitRead(buf[e], i));
    //   }
    // }

    // print RSSI of packet
    // Serial.print("' with RSSI ");
    // Serial.println(LoRa.packetRssi());
  }
  delay(100);
}
