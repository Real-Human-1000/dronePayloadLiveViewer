// DAQ Sketch: Take readings from sensors when it's time, collect that into packets, and send them over the radio
// Define necessary libraries, values, and files
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>

// BMP388 things
#include "Adafruit_BMP3XX.h"
#define SEALEVELPRESSURE_HPA (975.40)
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

const word packet_period = 750;  // millis
const word ens160_period = 1000; 
const word scd30_period = 2500;
const word pm_period = 5000;
const word battery_period = 10000;

word packet_num;
unsigned long loop_millis;

unsigned long last_packet;
unsigned long last_ens160;
unsigned long last_scd30;
unsigned long last_pm;
unsigned long last_battery;

float recent_bmp388_temperature;
byte recent_bmp388_altitude;

byte recent_ens160_aqi;  // Small value
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

byte recent_battery_voltage;  // multiply actual value (3-5) by 51 & truncate or round


void setup() {
  // Remove the Serial code when not testing
  Serial.begin(115200);
  while (!Serial);

  Serial.println("Adafruit Sensors Test");
  Serial.println("Waiting for boot...");
  delay(3000);
  Serial.println("Begin");

  // BMP388
  if (!bmp.begin_I2C()) {
    // hardware I2C
    Serial.println("Could not find a valid BMP388");
    while (1);
  }

  // Set up oversampling and filter initialization
  bmp.setTemperatureOversampling(BMP3_OVERSAMPLING_2X);
  bmp.setPressureOversampling(BMP3_OVERSAMPLING_8X);
  bmp.setIIRFilterCoeff(BMP3_IIR_FILTER_COEFF_3);
  bmp.setOutputDataRate(BMP3_ODR_50_HZ);

  // ENS160
  Serial.print("ENS160... ");
  bool ok = ens160.begin();
  Serial.println(ens160.available() ? "done" : "failed!");
  if (ens160.available()) {
    // Print ENS160 versions
    Serial.print("\tREV: "); Serial.print(ens160.getMajorRev());
    Serial.print("."); Serial.print(ens160.getMinorRev());
    Serial.print("."); Serial.println(ens160.getBuild());

    // Serial.print("\tCustom mode ");
    // ens160.initCustomMode(3);  // example has 3 steps, max 20 steps possible
    // // Step time is a multiple of 24ms and must not be smaller than 48ms
    // ens160.addCustomStep(40, 0, 0, 0, 0, 80, 80, 80, 80);  // Step 1: all hotplates at low temps
    // ens160.addCustomStep(196, 0, 0, 0, 0, 160, 215, 215, 200);  // Step 2: all hotplates at medium temps
    // ens160.addCustomStep(600, 1, 1, 1, 1, 250, 350, 350, 325);  // Step 3: measurements, hot plates
    // Serial.println(ens160.setMode(ENS160_OPMODE_CUSTOM) ? "done" : "failed");
    Serial.println(ens160.setMode(ENS160_OPMODE_STD) ? "done." : "failed!");
  }

  // SCD-30
  if (!scd30.begin()) {
    Serial.println("Failed to find SCD30 chip");
    while (1) { delay(10); }
  }
  Serial.println("SCD30 found!");
  Serial.print("Measurement interval: "); Serial.print(scd30.getMeasurementInterval()); Serial.println(" seconds");

  // PMSA003I
  if (!pm.begin_I2C()) {
    Serial.println("Could not find PM sensor!");
    while (1) delay(10);
  }
  Serial.println("PM found!");
}

void loop() {
  // Independent variables:
  loop_millis = millis();

  // BMP Temperature & Pressure/Altimeter
  // We will assume that this is fast and reliable enough to always be correct
  if (bmp.performReading()) {
    Serial.println("BMP388");
    recent_bmp388_temperature = bmp.temperature;  // floats
    recent_bmp388_altitude = (byte) round(bmp.readAltitude(SEALEVELPRESSURE_HPA)) * 2;  // to int half-meters
  }

  // Sensors / dependent variables:
  // SCD-30 CO2 / Temp / Humidity sensor
  if (loop_millis - last_scd30 > scd30_period) {
    if (scd30.dataReady()) {
      if (scd30.read()) {
        Serial.println("SCD30");
        recent_scd30_temperature = scd30.temperature;  // floats
        recent_scd30_humidity = scd30.relative_humidity;
        recent_scd30_co2 = (word) round(scd30.CO2);
        last_scd30 = loop_millis;
      }
    }
  }

  // ENS160 Gas Sensor
  if (loop_millis - last_ens160 > ens160_period) {
    if (ens160.available()) {
      Serial.println("ENS160");
      ens160.measure(true);
      recent_ens160_aqi = ens160.getAQI();  // shorts
      recent_ens160_tvoc = ens160.getTVOC();
      recent_ens160_eco2 = ens160.geteCO2();
      last_ens160 = loop_millis;
    }
  }

  // PMSA003I Particle sensor
  if (loop_millis - last_pm > pm_period) {
    PM25_AQI_Data data;
    if (pm.read(&data)) {
      Serial.println("PM");
      recent_pm_particles_03um = data.particles_03um;  // uint16_t
      recent_pm_particles_05um = data.particles_05um;
      recent_pm_particles_10um = data.particles_10um;
      recent_pm_particles_25um = data.particles_25um;
      recent_pm_particles_50um = data.particles_50um;
      last_pm = loop_millis;
    }
  }

  // Battery
  if (loop_millis - last_battery > battery_period) {
    Serial.println("Battery");
    float measuredvbat = analogRead(VBATPIN);
    measuredvbat *= 2;    // we divided by 2, so multiply back
    measuredvbat *= 3.3;  // Multiply by 3.3V, our reference voltage
    measuredvbat /= 1024; // convert to voltage
    recent_battery_voltage = (byte) round(50 * measuredvbat);
    last_battery = battery_period;
  }

  // Time to send a packet
  if (loop_millis - last_packet > packet_period) {
    // The server can accept packets with multiple samples, but it's actually a lot more difficult to do that, so I won't

    // Packet number

    // Packet type = "D"

    // Number of samples (1)

    // Sample 1
    // Time (quarter-seconds, 2 bytes)
    word sample_time = loop_millis * 4 / 1000;

    // Altitude (half-meters from the ground, 1 byte)
    recent_bmp388_altitude

    // Number of sensors (variable value, 1 byte)
    8

    // Number of characters in name of sensor 1 = 3
    3

    // Name of sensor 1 = "CO2"
    "CO2"

    // Number of characters in name of sensor 2 = 4
    4

    // Name of sensor 2 = "TVOC"
    "TVOC"

    // Number of characters in name of sensor 3 = 4
    4

    // Name of sensor 3 = "eCO2"
    "eCO2"

    // Number of characters in name of sensor 4 = 4
    4

    // Name of sensor 4 = "PM03"
    "PM03"

    // Number of characters in name of sensor 5 = 4
    4

    // Name of sensor 5 = "PM05"
    "PM05"

    // Number of characters in name of sensor 6 = 4

    // Name of sensor 6 = "PM10"

    // Number of characters in name of sensor 7 = 4

    // Name of sensor 7 = "PM25"

    // Number of characters in name of sensor 8 = 4

    // Name of sensor 8 = "PM50"

    // Value of sensor 1

    // Value of sensor 2

    // Value of sensor 3

    // Value of sensor 4

    // Value of sensor 5

    // Value of sensor 6

    // Value of sensor 7

    // Value of sensor 8
    

    last_packet = loop_millis;
  }
}
