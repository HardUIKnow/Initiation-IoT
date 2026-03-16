#include <Arduino.h>

// GPIO2 = LED intégrée sur la plupart des ESP32 DevKit v1
const int LED_PIN = 2;

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  Serial.println("=================================");
  Serial.println(" Station Météo IoT — Module 0");
  Serial.println(" Environnement professionnel");
  Serial.println("=================================");
  Serial.println("[INFO] LED configurée sur GPIO2");
  Serial.println("[BOOT] Prêt.");
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  Serial.println("[LED] ON  — 1 seconde");
  delay(1000);

  digitalWrite(LED_PIN, LOW);
  Serial.println("[LED] OFF — 1 seconde");
  delay(1000);
}
