#include <Arduino.h>
#include <DHT.h>
#include <Adafruit_BMP280.h>
#include <ArduinoJson.h>

// ─── Configuration des broches ────────────────────────────────────────────────
#define DHT_PIN  4
#define DHT_TYPE DHT22

// ─── Instances des capteurs ───────────────────────────────────────────────────
DHT dht(DHT_PIN, DHT_TYPE);
Adafruit_BMP280 bmp;

// ─── Intervalle de lecture (ms) ───────────────────────────────────────────────
const unsigned long LECTURE_INTERVAL_MS = 2000;
unsigned long derniereLecture = 0;

// ─── Prototypes ───────────────────────────────────────────────────────────────
bool lireEtPublierCapteurs();
String horodatage();

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("=================================");
  Serial.println(" Station Météo IoT — Module 1");
  Serial.println(" Initialisation des capteurs...");
  Serial.println("=================================");

  dht.begin();
  Serial.println("[DHT22] Initialisé sur GPIO4");

  if (!bmp.begin(0x76)) {
    if (!bmp.begin(0x77)) {
      Serial.println("[ERREUR] BMP280 non trouvé ! Vérifier le câblage I2C.");
    }
  } else {
    bmp.setSampling(
      Adafruit_BMP280::MODE_NORMAL,
      Adafruit_BMP280::SAMPLING_X2,
      Adafruit_BMP280::SAMPLING_X16,
      Adafruit_BMP280::FILTER_X16,
      Adafruit_BMP280::STANDBY_MS_500
    );
    Serial.println("[BMP280] Initialisé sur I2C (0x76)");
  }

  Serial.println("[INFO] Démarrage des lectures dans 2 secondes...");
  delay(2000);
}

void loop() {
  unsigned long maintenant = millis();
  if (maintenant - derniereLecture >= LECTURE_INTERVAL_MS) {
    derniereLecture = maintenant;
    lireEtPublierCapteurs();
  }
}

bool lireEtPublierCapteurs() {
  float temperature = dht.readTemperature();
  float humidite    = dht.readHumidity();

  if (isnan(temperature) || isnan(humidite)) {
    Serial.println("[ERREUR] Lecture DHT22 échouée — capteur déconnecté ?");
    return false;
  }

  float pression = bmp.readPressure() / 100.0F;
  float altitude  = bmp.readAltitude(1013.25);

  StaticJsonDocument<256> doc;
  doc["timestamp"]      = horodatage();
  doc["temperature_c"]  = round(temperature * 10) / 10.0;
  doc["humidity_pct"]   = round(humidite * 10) / 10.0;
  doc["pressure_hpa"]   = round(pression * 10) / 10.0;
  doc["altitude_m"]     = round(altitude * 10) / 10.0;

  serializeJson(doc, Serial);
  Serial.println();

  return true;
}

String horodatage() {
  unsigned long ms = millis();
  unsigned long secondes = ms / 1000;
  unsigned long minutes  = secondes / 60;
  unsigned long heures   = minutes / 60;

  char buf[20];
  snprintf(buf, sizeof(buf), "T+%02lu:%02lu:%02lu",
           heures, minutes % 60, secondes % 60);
  return String(buf);
}
