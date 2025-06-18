#include <SPI.h>
#include <RH_RF95.h>

// Feather 32u4 w/ LoRa:
#define RFM95_CS   8
#define RFM95_RST  4
#define RFM95_INT  7

// Change to 434.0 or other frequency, must match RX's freq!
#define RF95_FREQ 434.0

// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);

void setup() {
  // put your setup code here, to run once:
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
  rf95.setSpreadingFactor(12);

  // The default transmitter power is 13dBm, using PA_BOOST.
  // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then
  // you can set transmitter powers from 5 to 23 dBm:
  //rf95.setTxPower(23, false);
}

void loop() {
  // put your main code here, to run repeatedly:
  if (rf95.available()) {
    // Get the message
    byte buf[RH_RF95_MAX_MESSAGE_LEN];
    byte len = sizeof(buf);

    if (rf95.recv(buf, &len)) {
      //RH_RF95::printBuffer("Received:", buf, len);
      //Serial.println((char*)buf);
      // Serial.print("RSSI: "); Serial.println(rf95.lastRssi(), DEC);
      //Serial.println("Packet:");
      // for (int e = 0; e < len; e++) {
      //   for (int d = 0; d < 8 * sizeof(buf[e]); d++) {
      //     Serial.print(bitRead(buf[e], d));
      //   }
      // }
      // Serial.println();
      Serial.write(buf, len);
    }
    // Serial.println("011110111000000000100010100000000011110001110100010001011001000011000000110000101111001001001100001000000010101001101010111100101100001000100000101001101100001011110010010011000010000000001010101100100000110011001100001000000000101010110010000011001010110000100000000010101011001010001100000011000010000000001010101100100100110010101100001000000000101010110010101011000000110011000000010000101000001000101010001010010100000001111100000000000100011110000000010011100000000001011000000000000000000000000000000000000000000000000000000000000111001111101101");
    delay(1000);
  }
}
