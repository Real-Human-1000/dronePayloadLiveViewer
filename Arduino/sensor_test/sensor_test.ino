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


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  while (!Serial);
  Serial.println("Adafruit Sensors Test");
  Serial.println("Waiting for boot...");
  delay(3000);
  Serial.println("Begin");

  // // BMP388
  // if (!bmp.begin_I2C()) {
  //   // hardware I2C
  //   Serial.println("Could not find a valid BMP388");
  //   while (1);
  // }

  // // Set up oversampling and filter initialization
  // bmp.setTemperatureOversampling(BMP3_OVERSAMPLING_2X);
  // bmp.setPressureOversampling(BMP3_OVERSAMPLING_8X);
  // bmp.setIIRFilterCoeff(BMP3_IIR_FILTER_COEFF_3);
  // bmp.setOutputDataRate(BMP3_ODR_50_HZ);

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

  // // SCD-30
  // if (!scd30.begin()) {
  //   Serial.println("Failed to find SCD30 chip");
  //   while (1) { delay(10); }
  // }
  // Serial.println("SCD30 found!");
  // Serial.print("Measurement interval: ");
  // Serial.print(scd30.getMeasurementInterval());
  // Serial.println(" seconds");

  // // PMSA003I
  // if (!pm.begin_I2C()) {
  //   Serial.println("Could not find PM sensor!");
  //   while (1) delay(10);
  // }
  // Serial.println("PM found!");
}

void loop() {
  // put your main code here, to run repeatedly:
  // if (!bmp.performReading()) {
  //   Serial.println("Failed to perform reading");
  //   return;
  // }

  // Serial.print("Temperature = ");
  // Serial.print(bmp.temperature);
  // Serial.println(" *C");

  // Serial.print("Pressure = ");
  // Serial.print(bmp.pressure / 100.0);
  // Serial.println(" hPa");

  // Serial.print("Approx. Altitude = ");
  // Serial.print(bmp.readAltitude(SEALEVELPRESSURE_HPA));
  // Serial.println(" m");

  

  if (ens160.available()) {
    ens160.measure(true);
    ens160.measureRaw(true);
    Serial.print("R HP0: ");Serial.print(ens160.getHP0());Serial.print("Ohm\t");
    Serial.print("R HP1: ");Serial.print(ens160.getHP1());Serial.print("Ohm\t");
    Serial.print("R HP2: ");Serial.print(ens160.getHP2());Serial.print("Ohm\t");
    Serial.print("R HP3: ");Serial.print(ens160.getHP3());Serial.println("Ohm");

    //ens160.measure(0);
    Serial.print("AQI: "); Serial.print(ens160.getAQI()); Serial.print("\t");
    Serial.print("TVOC: "); Serial.print(ens160.getTVOC()); Serial.print(" ppb\t");
    Serial.print("eCO2: "); Serial.print(ens160.geteCO2()); Serial.println(" ppm\t");
  }

  
  // if (scd30.dataReady()) {
  //   Serial.println("Data available from SCD-30!");
  //   if (!scd30.read()) {Serial.println("Error reading sensor data"); return;}

  //   Serial.print("Temperature:");
  //   Serial.print(scd30.temperature);
  //   Serial.println(" *C");

  //   Serial.print("Relative humidity: ");
  //   Serial.print(scd30.relative_humidity);
  //   Serial.println("%");

  //   Serial.print("CO2: ");
  //   Serial.print(scd30.CO2, 3);
  //   Serial.print(" ppm");
  // } else {
  //   Serial.println("No data");
  // }

  // PM25_AQI_Data data;
  // if (!pm.read(&data)) {
  //   Serial.println("Could not read from PM");
  //   delay(500);
  //   return;
  // }
  // Serial.println("PM reading success!");
  // Serial.println(F("Concentration Units (standard)"));
  // Serial.print(F("PM 1.0: ")); Serial.print(data.pm10_standard);
  // Serial.print(F("\t\tPM 2.5: ")); Serial.print(data.pm25_standard);
  // //Serial.print(F("\t\tPM 10: ")); Serial.println(data.pm100_standard);
  // Serial.println(F("---------------------------------------"));
  // Serial.println(F("Concentration Units (environmental)"));
  // Serial.print(F("PM 1.0: ")); Serial.print(data.pm10_env);
  // Serial.print(F("\t\tPM 2.5: ")); Serial.print(data.pm25_env);
  // //Serial.print(F("\t\tPM 10: ")); Serial.println(data.pm100_env);
  // Serial.println(F("---------------------------------------"));
  // Serial.print(F("Particles > 0.3um / 0.1L air:")); Serial.println(data.particles_03um);
  // Serial.print(F("Particles > 0.5um / 0.1L air:")); Serial.println(data.particles_05um);
  // Serial.print(F("Particles > 1.0um / 0.1L air:")); Serial.println(data.particles_10um);
  // Serial.print(F("Particles > 2.5um / 0.1L air:")); Serial.println(data.particles_25um);
  // Serial.print(F("Particles > 5.0um / 0.1L air:")); Serial.println(data.particles_50um);
  // //Serial.print(F("Particles > 10 um / 0.1L air:")); Serial.println(data.particles_100um);

  float measuredvbat = analogRead(VBATPIN);
  measuredvbat *= 2;    // we divided by 2, so multiply back
  measuredvbat *= 3.3;  // Multiply by 3.3V, our reference voltage
  measuredvbat /= 1024; // convert to voltage
  Serial.print("VBat: " ); Serial.print(measuredvbat); Serial.print(" ("); Serial.print(100 * (measuredvbat - 3.2) / 1.0); Serial.println("%)");

  Serial.println();
  delay(2000);
}
