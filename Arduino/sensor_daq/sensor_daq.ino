// DAQ Sketch: Take readings from sensors when it's time, collect that into packets, and send them over the radio
// Define necessary libraries, values, and files
#define PRINT_SERIAL false
#define SD_LOGGING true

#include <Wire.h>
// #include <SPI.h>
// #include <Adafruit_Sensor.h>
// #include <RH_RF95.h>
#include <LoRa.h>
// #include <SD.h>
#include <SdFat.h>

// BMP388 things
#include "Adafruit_BMP3XX.h"
#define SEALEVELPRESSURE_HPA 977.00
Adafruit_BMP3XX bmp;

// ENS160 things
#include "ScioSense_ENS160.h"
ScioSense_ENS160 ens160(ENS160_I2CADDR_1);

// SCD-30 things
#include <Adafruit_SCD30.h>
Adafruit_SCD30 scd30;

// PMSA003I things
#include "Adafruit_PM25AQI.h"
Adafruit_PM25AQI pm = Adafruit_PM25AQI();

// Battery
#define VBATPIN A9

// Feather 32u4 wired to RFM95 breakout:
#define RFM95_CS   5
#define RFM95_RST  12
#define RFM95_INT  0

// Change to 434.0 or other frequency, must match RX's freq!
#define RF95_FREQ 434.0

#define SD_CS 4
#define SPI_SPEED SD_SCK_MHZ(4)

#define packet_period 10  // deciseconds (tenths of seconds)
#define ens160_period 10 
#define scd30_period 15
#define pm_period 25
#define battery_period 50

SdFat sd;
SdFile myFile;

word packet_num;
unsigned short loop_decis;

unsigned short last_packet;
unsigned short last_ens160;
unsigned short last_scd30;
unsigned short last_pm;
unsigned short last_battery;

float recent_bmp388_temperature;
byte recent_bmp388_altitude;

// byte recent_ens160_aqi;  // Small value
word recent_ens160_tvoc;
word recent_ens160_eco2;

float recent_scd30_temperature;
float recent_scd30_humidity;
word recent_scd30_co2;

word recent_pm_particles_03um;  // I'm going to assume that these aren't going to go above 65,535
word recent_pm_particles_05um;
word recent_pm_particles_10um;
word recent_pm_particles_25um;
word recent_pm_particles_50um;

word recent_battery_voltage;  // multiply actual value (3-5) by 13107 & truncate (--> new range is up to about 65535)

// Singleton instance of the radio driver
// RH_RF95 rf95(RFM95_CS, RFM95_INT);


void setup() {
  // Setup pins for radio control
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  // manually reset radio
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  // Remove the Serial code when not testing
  if (PRINT_SERIAL) {
    Serial.begin(115200);
    while (!Serial);
  }

  if (PRINT_SERIAL) {
    Serial.println(F("Boot..."));
  }
  delay(3000);
  if (PRINT_SERIAL) {
    Serial.println(F("Begin"));
  }

  // BMP388
  if (!bmp.begin_I2C()) {
    // hardware I2C
    Serial.println(F("No BMP388"));
    while (1);
  }

  // Set up oversampling and filter initialization
  bmp.setTemperatureOversampling(BMP3_OVERSAMPLING_2X);
  bmp.setPressureOversampling(BMP3_OVERSAMPLING_8X);
  bmp.setIIRFilterCoeff(BMP3_IIR_FILTER_COEFF_3);
  bmp.setOutputDataRate(BMP3_ODR_50_HZ);

  // ENS160
  bool ok = ens160.begin();
  if (PRINT_SERIAL) {
    Serial.print("ENS160... ");
    Serial.println(ens160.available() ? F("done") : F("failed"));
  }
  if (ens160.available()) {
    // Print ENS160 versions
    if (PRINT_SERIAL) {
      Serial.print(F("\tREV: ")); Serial.print(ens160.getMajorRev());
      Serial.print(F(".")); Serial.print(ens160.getMinorRev());
      Serial.print(F(".")); Serial.println(ens160.getBuild());
    }

    // Serial.print("\tCustom mode ");
    // ens160.initCustomMode(3);  // example has 3 steps, max 20 steps possible
    // // Step time is a multiple of 24ms and must not be smaller than 48ms
    // ens160.addCustomStep(40, 0, 0, 0, 0, 80, 80, 80, 80);  // Step 1: all hotplates at low temps
    // ens160.addCustomStep(196, 0, 0, 0, 0, 160, 215, 215, 200);  // Step 2: all hotplates at medium temps
    // ens160.addCustomStep(600, 1, 1, 1, 1, 250, 350, 350, 325);  // Step 3: measurements, hot plates
    // Serial.println(ens160.setMode(ENS160_OPMODE_CUSTOM) ? "done" : "failed");
    bool ens_set = ens160.setMode(ENS160_OPMODE_STD);
    if (PRINT_SERIAL) {
      Serial.print("Set mode: "); Serial.println(ens_set ? F("done") : F("failed"));
    }
  }

  // SCD-30
  if (!scd30.begin()) {
    if (PRINT_SERIAL) {
      Serial.println(F("No SCD30"));
    }
    while (1) { delay(10); }
  }
  if (PRINT_SERIAL) {
    Serial.println(F("SCD30 found"));
  }

  // PMSA003I
  if (!pm.begin_I2C()) {
    if (PRINT_SERIAL) {
      Serial.println(F("No PM sensor"));
    }
    while (1) delay(10);
  }
  if (PRINT_SERIAL) {
    Serial.println(F("PM found!"));
  }

  // RFM95 Radio
  // while (!rf95.init()) {
  //   if (PRINT_SERIAL) {
  //     Serial.println(F("Radio init failed"));
  //   }
  //   while (1);
  // }
  // if (PRINT_SERIAL) {
  //   Serial.println(F("Radio init OK!"));
  // }

  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM
  // if (!rf95.setFrequency(RF95_FREQ)) {
  //   if (PRINT_SERIAL) {
  //     Serial.println(F("setFrequency failed"));
  //   }
  //   while (1);
  // }
  // if (PRINT_SERIAL) {
  //   Serial.print(F("Freq: ")); Serial.println(RF95_FREQ);
  // }

  // // Defaults after init are 434.0MHz, 13dBm, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on
  // rf95.setSpreadingFactor(9);

  // // The default transmitter power is 13dBm, using PA_BOOST.
  // // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then
  // // you can set transmitter powers from 5 to 23 dBm:
  // rf95.setTxPower(20, false);

  LoRa.setPins(RFM95_CS, RFM95_RST, RFM95_INT);
  if (!LoRa.begin(RF95_FREQ * 1000000)) {
    if (PRINT_SERIAL) {
      Serial.println(F("Starting LoRa failed!"));
    }
    while (1);
  }
  LoRa.setSpreadingFactor(9);

  // if (SD_LOGGING) {
  //   if (!SD.begin(SD_CS)) {
  //     if (PRINT_SERIAL) {
  //       Serial.println(F("Card failed"));
  //     }
  //     while (1);
  //   }
  //   if (PRINT_SERIAL) {
  //     Serial.println(F("Card initialized."));
  //   }
  // }

  if (SD_LOGGING) {
    if (!sd.begin(SD_CS, SPI_HALF_SPEED)) {
      if (PRINT_SERIAL) {
        Serial.println(F("Card failed"));
      }
      while (1);
    }
    if (PRINT_SERIAL) {
      Serial.println(F("Card initialized."));
    }
  }
}

void loop() {
  // Independent variables:
  loop_decis = (unsigned short)(millis() / 100);

  // BMP Temperature & Pressure/Altimeter
  // We will assume that this is fast and reliable enough to always be correct
  if (bmp.performReading()) {
    if (PRINT_SERIAL) {
      Serial.println(F("BMP388"));
    }
    recent_bmp388_temperature = bmp.temperature;  // float
    recent_bmp388_altitude = (byte) max(round(bmp.readAltitude(SEALEVELPRESSURE_HPA)) * 2, 0);  // to int half-meters
  }

  // Sensors / dependent variables:
  // SCD-30 CO2 / Temp / Humidity sensor
  if (loop_decis - last_scd30 > scd30_period) {
    if (scd30.dataReady()) {
      if (scd30.read()) {
        if (PRINT_SERIAL) {
          Serial.println(F("SCD30"));
        }
        recent_scd30_temperature = scd30.temperature;  // floats
        recent_scd30_humidity = scd30.relative_humidity;
        recent_scd30_co2 = (word) max(round(scd30.CO2), 0);
        last_scd30 = loop_decis;
      }
    }
  }

  // ENS160 Gas Sensor
  if (loop_decis - last_ens160 > ens160_period) {
    if (ens160.available()) {
      if (PRINT_SERIAL) {
        Serial.println(F("ENS160"));
      }
      ens160.measure(true);  // this takes a lot of time
      // recent_ens160_aqi = ens160.getAQI();  // shorts
      recent_ens160_tvoc = max(ens160.getTVOC(), 0);
      recent_ens160_eco2 = max(ens160.geteCO2(), 0);
      last_ens160 = loop_decis;
    }
  }

  // PMSA003I Particle sensor
  if (loop_decis - last_pm > pm_period) {
    PM25_AQI_Data data;
    if (pm.read(&data)) {
      if (PRINT_SERIAL) {
        Serial.println(F("PM"));
      }
      recent_pm_particles_03um = max(data.particles_03um, 0);  // uint16_t
      recent_pm_particles_05um = max(data.particles_05um, 0);
      recent_pm_particles_10um = max(data.particles_10um, 0);
      recent_pm_particles_25um = max(data.particles_25um, 0);
      recent_pm_particles_50um = max(data.particles_50um, 0);
      last_pm = loop_decis;
    }
  }

  // Battery
  if (loop_decis - last_battery > battery_period) {
    if (PRINT_SERIAL) {
      Serial.println(F("Battery"));
    }
    float measuredvbat = analogRead(VBATPIN);
    measuredvbat *= 2;    // we divided by 2, so multiply back
    measuredvbat *= 3.3;  // Multiply by 3.3V, our reference voltage
    measuredvbat /= 1024; // convert to voltage
    recent_battery_voltage = (word) max(floor(13107 * measuredvbat), 0);
    last_battery = loop_decis;
  }

  // Time to send a packet
  if (loop_decis - last_packet > packet_period) {
    // The server can accept packets with multiple samples, but it's actually a lot more difficult to do that, so I won't
    // Also, because I am lazy, this packet is actually much more static than the server version
    if (PRINT_SERIAL) {
      Serial.println(F("Packet"));
    }
    digitalWrite(LED_BUILTIN, HIGH); 

    byte length_of_packet = 6 + (2 + 1 + 1) + (2 + 1 + 1) + ((1 + 3) + (1 + 4) + (1 + 4) + (1 + 4) + (1 + 4) + (1 + 4) + (1 + 4) + (1 + 4) + (1 + 3)) + (2 * 9);
    byte packet [length_of_packet] = {};

    // callsign
    char callsign[6] = {'K', 'J', '5', 'I', 'R', 'C'};  // This is Henry Prendergast's callsign; change is Henry isn't present
    memcpy(&packet[0], &callsign, 6);
    byte pindex = 6;

    // Packet number (2b)
    memcpy(&packet[pindex], &packet_num, 2);
    pindex = pindex + 2;

    // Packet type = "D" (1b)
    char packet_type = 'D';
    memcpy(&packet[pindex], &packet_type, 1);
    pindex = pindex + 1;

    // Number of samples (1b)
    byte num_samples = 1;
    memcpy(&packet[pindex], &num_samples, 1);
    pindex = pindex + 1;

    // Sample 1
    // Time (quarter-seconds, 2b)
    word sample_time = loop_decis * 4 / 10;
    memcpy(&packet[pindex], &sample_time, 2);
    pindex = pindex + 2;

    // Altitude (half-meters from the ground, 1 byte)
    memcpy(&packet[pindex], &recent_bmp388_altitude, 1);
    pindex = pindex + 1;

    // Begin section of packet that's basically always the same

    // // Number of sensors (variable value, 1 byte)
    // byte num_sensors = 9;
    // memcpy(&packet[pindex], &num_sensors, 1);
    // pindex = pindex + 1;

    // // Number of characters in name of sensor 1 = 3
    // byte numchar_sens1 = 3;
    // memcpy(&packet[pindex], &numchar_sens1, 1); 
    // pindex = pindex + 1;

    // // Name of sensor 1 = "CO2"
    // char name_sens1[3] = {'C', 'O', '2'};
    // memcpy(&packet[pindex], &name_sens1, numchar_sens1);
    // pindex = pindex + numchar_sens1;

    // // // Number of characters in name of sensor 2 = 4
    // byte numchar_sens2 = 4;
    // memcpy(&packet[pindex], &numchar_sens2, 1);
    // pindex = pindex + 1;

    // // // Name of sensor 2 = "TVOC"
    // char name_sens2[4] = {'T', 'V', 'O', 'C'};
    // memcpy(&packet[pindex], &name_sens2, numchar_sens2);
    // pindex = pindex + numchar_sens2;

    // // Number of characters in name of sensor 3 = 4
    // byte numchar_sens3 = 4;
    // memcpy(&packet[pindex], &numchar_sens3, 1);
    // pindex = pindex + 1;

    // // Name of sensor 3 = "eCO2"
    // char name_sens3[4] = {'e', 'C', 'O', '2'};
    // memcpy(&packet[pindex], &name_sens3, numchar_sens3);
    // pindex = pindex + numchar_sens3;

    // // Number of characters in name of sensor 4 = 4
    // byte numchar_sens4 = 4;
    // memcpy(&packet[pindex], &numchar_sens4, 1);
    // pindex = pindex + 1;

    // // Name of sensor 4 = "PM03"
    // char name_sens4[4] = {'P', 'M', '0', '3'};
    // memcpy(&packet[pindex], &name_sens4, numchar_sens4);
    // pindex = pindex + numchar_sens4;

    // // Number of characters in name of sensor 5 = 4
    // byte numchar_sens5 = 4;
    // memcpy(&packet[pindex], &numchar_sens5, 1);
    // pindex = pindex + 1;

    // // Name of sensor 5 = "PM05"
    // char name_sens5[4] = {'P', 'M', '0', '5'};
    // memcpy(&packet[pindex], &name_sens5, numchar_sens5);
    // pindex = pindex + numchar_sens5;

    // // Number of characters in name of sensor 6 = 4
    // byte numchar_sens6 = 4;
    // memcpy(&packet[pindex], &numchar_sens6, 1);
    // pindex = pindex + 1;

    // // Name of sensor 6 = "PM10"
    // char name_sens6[4] = {'P', 'M', '1', '0'};
    // memcpy(&packet[pindex], &name_sens6, numchar_sens6);
    // pindex = pindex + numchar_sens6;

    // // Number of characters in name of sensor 7 = 4
    // byte numchar_sens7 = 4;
    // memcpy(&packet[pindex], &numchar_sens7, 1);
    // pindex = pindex + 1;

    // // Name of sensor 7 = "PM25"
    // char name_sens7[4] = {'P', 'M', '2', '5'};
    // memcpy(&packet[pindex], &name_sens7, numchar_sens7);
    // pindex = pindex + numchar_sens7;

    // // Number of characters in name of sensor 8 = 4
    // byte numchar_sens8 = 4;
    // memcpy(&packet[pindex], &numchar_sens8, 1);
    // pindex = pindex + 1;

    // // Name of sensor 8 = "PM50"
    // char name_sens8[4] = {'P', 'M', '5', '0'};
    // memcpy(&packet[pindex], &name_sens8, numchar_sens8);
    // pindex = pindex + numchar_sens8;

    // // Number of characters in name of sensor 9 = 3
    // byte numchar_sens9 = 3;
    // memcpy(&packet[pindex], &numchar_sens9, 1);
    // pindex = pindex + 1;

    // // Name of sensor 9 = "BAT"
    // char name_sens9[3] = {'B', 'A', 'T'};
    // memcpy(&packet[pindex], &name_sens9, numchar_sens9);
    // pindex = pindex + 3;

    // End section of packet that's always the same
    // Just directly applying this portion of the packet to save space
    byte section[44] = {9,3,67,79,50,4,84,86,79,67,4,101,67,79,50,4,80,77,48,51,4,80,77,48,53,4,80,77,49,48,4,80,77,50,53,4,80,77,53,48,3,66,65,84};
    memcpy(&packet[pindex], &section, 44);
    pindex = pindex + 44;

    // We can put all the sensor values in a loop because they're all words
    word sensor_vals [9] = {recent_scd30_co2, recent_ens160_tvoc, recent_ens160_eco2, recent_pm_particles_03um, recent_pm_particles_05um, recent_pm_particles_10um, recent_pm_particles_25um, recent_pm_particles_50um, recent_battery_voltage};
    for (byte s = 0; s < 9; s++) {
      memcpy(&packet[pindex], &sensor_vals[s], 2);
      pindex = pindex + 2;
    }

    // // Value of sensor 1
    // //recent_scd30_co2
    // memcpy(&packet[pindex], &recent_scd30_co2, 2);
    // pindex = pindex + 2;

    // // Value of sensor 2
    // //recent_ens160_tvoc
    // memcpy(&packet[pindex], &recent_ens160_tvoc, 2);
    // pindex = pindex + 2;

    // // Value of sensor 3
    // //recent_ens160_eco2
    // memcpy(&packet[pindex], &recent_ens160_eco2, 2);
    // pindex = pindex + 2;

    // // Value of sensor 4
    // //recent_pm_particles_03um
    // memcpy(&packet[pindex], &recent_pm_particles_03um, 2);
    // pindex = pindex + 2;

    // // Value of sensor 5
    // //recent_pm_particles_05um
    // memcpy(&packet[pindex], &recent_pm_particles_05um, 2);
    // pindex = pindex + 2;

    // // Value of sensor 6
    // //recent_pm_particles_10um
    // memcpy(&packet[pindex], &recent_pm_particles_10um, 2);
    // pindex = pindex + 2;

    // // Value of sensor 7
    // //recent_pm_particles_25um
    // memcpy(&packet[pindex], &recent_pm_particles_25um, 2);
    // pindex = pindex + 2;

    // // Value of sensor 8
    // //recent_pm_particles_50um
    // memcpy(&packet[pindex], &recent_pm_particles_50um, 2);
    // pindex = pindex + 2;

    // // Value of sensor 9
    // //recent_battery_voltage
    // memcpy(&packet[pindex], &recent_battery_voltage, 2);
    // pindex = pindex + 2;

    if (PRINT_SERIAL) {
      Serial.write(packet, length_of_packet);
      Serial.println();
    }

    // Send packet over radio
    // rf95.send((uint8_t *)packet, length_of_packet);
    while (LoRa.beginPacket() == 0) {
      if (PRINT_SERIAL) {
        Serial.print(F("Waiting for radio ... "));
      }
      delay(100);
    }
    LoRa.beginPacket();
    LoRa.write(packet, length_of_packet);
    LoRa.endPacket(true); // true = async / non-blocking mode

    // Save packet to log file
    if (SD_LOGGING) {
      // // Open the file. note that only one file can be open at a time,
      // // so you have to close this one before opening another.
      // File dataFile = SD.open("datalog2.txt", FILE_WRITE);

      // // if the file is available, write to it:
      // if (dataFile) {
      //   if (PRINT_SERIAL) {
      //     Serial.println(F("Saving data"));
      //   }
      //   dataFile.write(packet, length_of_packet);
      //   dataFile.println();
      //   if (unflushed_packets > packet_flush_limit) {
      //     dataFile.flush();
      //     unflushed_packets = 0;
      //   } else {
      //     unflushed_packets ++;
      //   }
      //   dataFile.close();
      // }
      // // if the file isn't open, pop up an error:
      // else {
      //   if (PRINT_SERIAL) {
      //     Serial.println(F("Error opening log file"));
      //   }
      // }
      if (!myFile.open("test.txt", O_RDWR | O_CREAT | O_AT_END)) {
        if (PRINT_SERIAL) {
          Serial.println(F("Error opening log file"));
        }
      }
      // if the file opened okay, write to it:
      myFile.println("testing 1, 2, 3.");

      // close the file:
      myFile.close();
    }
    
    digitalWrite(LED_BUILTIN, LOW);
    packet_num ++;
    last_packet = (unsigned short)(millis() / 100);  // Keep the loop from getting bogged down with packets
  }
  if (PRINT_SERIAL) {
    Serial.println(F("Waiting..."));
  }
  delay(100);
}
