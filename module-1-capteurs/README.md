# Module 1 — Le capteur parle

> *ESP32 + DHT22/BMP280 → données série*

[![Durée estimée](https://img.shields.io/badge/Durée-60%20min-blue)](.)
[![Difficulté](https://img.shields.io/badge/Difficulté-Débutant-brightgreen)](.)
[![Matériel](https://img.shields.io/badge/Matériel-ESP32%20%2B%20DHT22%20%2B%20BMP280-orange)](.)

---

## 🎯 Objectif du module

L'ESP32 lit deux capteurs physiques en parallèle et envoie les données structurées en JSON vers le port série. Un script Python reçoit, parse et affiche ces données en temps réel.

---

## ✅ Livrable

> **Terminal Python affichant en temps réel : température, humidité, pression, horodatage — structurés en JSON.**

```json
{
  "timestamp": "2024-01-15T14:32:05",
  "temperature_c": 22.4,
  "humidity_pct": 58.1,
  "pressure_hpa": 1013.2,
  "altitude_m": 42.5
}
```

---

## 🛠️ Matériel

| Composant | Référence | Alternative |
|-----------|-----------|-------------|
| Microcontrôleur | ESP32 DevKit v1 | ESP32-S3, ESP32-C3 |
| Temp / Humidité | DHT22 (AM2302) | SHT31 (I2C, plus précis), HDC1080 |
| Pression / Altitude | BMP280 | BME280 (ajoute humidité), BMP388 |
| Résistance | 10kΩ (pull-up DHT22) | — |
| Breadboard | 400 points | — |
| Jumpers | M/M et M/F | — |

---

## 📋 Contenu du module

### 1. Protocoles de communication embarquée

Avant de brancher, il faut comprendre **comment** les composants communiquent.

| Protocole | Fils | Débit | Cas d'usage typique |
|-----------|------|-------|---------------------|
| GPIO | 1 | Très faible | Bouton, LED, DHT22 |
| I2C | 2 (SDA + SCL) | Moyen | BMP280, SHT31, écrans OLED |
| SPI | 4 (MOSI/MISO/SCK/CS) | Rapide | Cartes SD, écrans TFT |
| UART | 2 (TX + RX) | Variable | Port série, GPS, Bluetooth |

> **Règle pratique** : si le composant a 2 fils de données, c'est probablement I2C. Si c'est 1 fil avec timing précis, c'est probablement GPIO "one-wire" (DHT22).

### 2. Câblage DHT22

```
DHT22 (vue de face, broches vers le bas)
┌──────────┐
│ 1  2  3  4 │
└──────────┘
  │  │     │
 VCC DATA GND

VCC  → ESP32 3.3V
DATA → ESP32 GPIO4 + résistance 10kΩ vers 3.3V (pull-up)
GND  → ESP32 GND
```

> ⚠️ La résistance pull-up de 10kΩ est **obligatoire** sur le DHT22. Sans elle, les lectures sont instables ou impossibles.

### 3. Câblage BMP280 (I2C)

```
BMP280
┌──────────────────┐
│ VCC SDA SCL GND  │
└──────────────────┘
    │   │   │   │
   3.3V GPIO21 GPIO22 GND

ESP32 (I2C par défaut)
SDA → GPIO21
SCL → GPIO22
```

> Le BMP280 supporte aussi SPI. Pour ce cours, on utilise I2C (moins de fils, suffisamment rapide).

### 4. Structure du firmware

```
firmware/station-meteo/
├── platformio.ini
└── src/
    └── main.cpp
```

---

## 🔧 Code

### Firmware ESP32

**`firmware/station-meteo/platformio.ini`**

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200
upload_speed = 921600

lib_deps =
  adafruit/DHT sensor library @ ^1.4.6
  adafruit/Adafruit BMP280 Library @ ^2.6.8
  bblanchon/ArduinoJson @ ^7.0.0
```

**`firmware/station-meteo/src/main.cpp`**

```cpp
#include <Arduino.h>
#include <DHT.h>
#include <Adafruit_BMP280.h>
#include <ArduinoJson.h>

// ─── Configuration des broches ───────────────────────────────────────────────
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

  // Initialisation DHT22
  dht.begin();
  Serial.println("[DHT22] Initialisé sur GPIO4");

  // Initialisation BMP280
  if (!bmp.begin(0x76)) {
    // Essayer l'adresse I2C alternative
    if (!bmp.begin(0x77)) {
      Serial.println("[ERREUR] BMP280 non trouvé ! Vérifier le câblage I2C.");
      // On continue sans le BMP280 plutôt que de bloquer
    }
  } else {
    // Paramètres de précision recommandés
    bmp.setSampling(
      Adafruit_BMP280::MODE_NORMAL,
      Adafruit_BMP280::SAMPLING_X2,   // Température
      Adafruit_BMP280::SAMPLING_X16,  // Pression
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
  // ── Lecture DHT22 ──────────────────────────────────────────────────────────
  float temperature = dht.readTemperature();
  float humidite    = dht.readHumidity();

  // Validation des données DHT22
  if (isnan(temperature) || isnan(humidite)) {
    Serial.println("[ERREUR] Lecture DHT22 échouée — capteur déconnecté ?");
    return false;
  }

  // ── Lecture BMP280 ─────────────────────────────────────────────────────────
  float pression = bmp.readPressure() / 100.0F; // Conversion Pa → hPa
  float altitude  = bmp.readAltitude(1013.25);  // Altitude estimée (pression mer standard)

  // ── Sérialisation JSON ─────────────────────────────────────────────────────
  StaticJsonDocument<256> doc;
  doc["timestamp"]      = horodatage();
  doc["temperature_c"]  = round(temperature * 10) / 10.0;
  doc["humidity_pct"]   = round(humidite * 10) / 10.0;
  doc["pressure_hpa"]   = round(pression * 10) / 10.0;
  doc["altitude_m"]     = round(altitude * 10) / 10.0;

  // Publication sur le port série
  serializeJson(doc, Serial);
  Serial.println(); // Saut de ligne pour faciliter le parsing

  return true;
}

// Horodatage basique basé sur le temps d'exécution
// (sera remplacé par NTP au Module 3)
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
```

### Script Python — Lecteur série

**`backend/serial_reader.py`**

```python
#!/usr/bin/env python3
"""
Module 1 — Lecteur port série
Reçoit les données JSON de l'ESP32 et les affiche en terminal.
"""

import serial
import serial.tools.list_ports
import json
import sys
from datetime import datetime


def trouver_port_esp32() -> str | None:
    """Détecte automatiquement le port série de l'ESP32."""
    ports = serial.tools.list_ports.comports()
    
    # Identifiants connus des puces USB-série ESP32
    puces_connues = ["CP210x", "CH340", "CH341", "FTDI", "Silicon Labs"]
    
    for port in ports:
        for puce in puces_connues:
            if puce.lower() in (port.description or "").lower():
                return port.device
    
    # Si non détecté, retourner le premier port disponible
    if ports:
        return ports[0].device
    
    return None


def afficher_mesure(donnees: dict) -> None:
    """Affiche une mesure de façon lisible dans le terminal."""
    heure = datetime.now().strftime("%H:%M:%S")
    
    print(f"\n{'─' * 40}")
    print(f"  📡 Mesure reçue à {heure}")
    print(f"{'─' * 40}")
    
    if "temperature_c" in donnees:
        print(f"  🌡️  Température : {donnees['temperature_c']:.1f} °C")
    
    if "humidity_pct" in donnees:
        print(f"  💧 Humidité    : {donnees['humidity_pct']:.1f} %")
    
    if "pressure_hpa" in donnees:
        print(f"  🔵 Pression    : {donnees['pressure_hpa']:.1f} hPa")
    
    if "altitude_m" in donnees:
        print(f"  ⛰️  Altitude    : {donnees['altitude_m']:.1f} m")
    
    print(f"  ⏱️  Horodatage  : {donnees.get('timestamp', 'N/A')}")


def main():
    # ── Détection du port ──────────────────────────────────────────────────────
    port = trouver_port_esp32()
    
    if port is None:
        print("[ERREUR] Aucun ESP32 détecté.")
        print("  → Vérifier que l'ESP32 est branché en USB")
        print("  → Installer les drivers CP210x ou CH340 si nécessaire")
        sys.exit(1)
    
    print(f"[INFO] ESP32 détecté sur {port}")
    print(f"[INFO] Démarrage de la lecture... (Ctrl+C pour arrêter)")
    
    # ── Connexion série ────────────────────────────────────────────────────────
    try:
        ser = serial.Serial(port, baudrate=115200, timeout=5)
    except serial.SerialException as e:
        print(f"[ERREUR] Impossible d'ouvrir {port}: {e}")
        sys.exit(1)
    
    erreurs_consecutives = 0
    MAX_ERREURS = 5

    # ── Boucle de lecture ──────────────────────────────────────────────────────
    try:
        while True:
            try:
                ligne = ser.readline().decode("utf-8").strip()
                
                if not ligne:
                    continue
                
                # On ne parse que les lignes JSON (commencent par '{')
                if not ligne.startswith("{"):
                    print(f"[LOG ESP32] {ligne}")
                    continue
                
                donnees = json.loads(ligne)
                afficher_mesure(donnees)
                erreurs_consecutives = 0  # Remise à zéro après succès
                
            except json.JSONDecodeError:
                print(f"[WARN] Ligne non-JSON ignorée : {ligne[:50]}...")
                
            except serial.SerialException:
                erreurs_consecutives += 1
                print(f"[ERREUR] Perte de connexion série ({erreurs_consecutives}/{MAX_ERREURS})")
                
                if erreurs_consecutives >= MAX_ERREURS:
                    print("[FATAL] Trop d'erreurs — arrêt.")
                    break
                
                # Tentative de reconnexion
                import time
                time.sleep(2)
                try:
                    ser.close()
                    ser.open()
                    print("[INFO] Reconnexion réussie")
                    erreurs_consecutives = 0
                except Exception:
                    pass
                    
    except KeyboardInterrupt:
        print("\n\n[INFO] Arrêt demandé par l'utilisateur.")
    
    finally:
        ser.close()
        print("[INFO] Port série fermé.")


if __name__ == "__main__":
    main()
```

---

## 🚀 Démarrage

```bash
# 1. Flasher le firmware
cd firmware/station-meteo
pio run --target upload

# 2. Lancer le lecteur Python (dans un autre terminal)
cd backend
pip install pyserial
python serial_reader.py

# Pour spécifier manuellement le port
python serial_reader.py /dev/ttyUSB0     # Linux
python serial_reader.py COM3             # Windows
```

---

## 🧪 Vérification

Votre module 1 est terminé si :

- [ ] DHT22 câblé avec résistance pull-up 10kΩ
- [ ] BMP280 câblé en I2C (SDA→GPIO21, SCL→GPIO22)
- [ ] Firmware compilé et flashé sans erreur
- [ ] Moniteur série affiche des JSON valides (vérifier avec [jsonlint.com](https://jsonlint.com))
- [ ] Script Python affiche les 4 valeurs en temps réel
- [ ] La reconnexion fonctionne (débrancher/rebrancher le câble USB)

---

## ❓ Problèmes fréquents

**DHT22 retourne `nan`**
→ Vérifier la résistance pull-up de 10kΩ. Sans elle, le signal est instable.
→ Certains modules DHT22 ont la résistance intégrée (3 broches) — retirer alors la résistance externe.

**BMP280 non trouvé (adresse I2C)**
→ Tester l'adresse `0x77` si `0x76` échoue (dépend du câblage de la broche SDO).
→ Utiliser un [scanner I2C](https://randomnerdtutorials.com/esp32-i2c-scanner/) pour détecter l'adresse.

**Python ne trouve pas le port série**
→ Sur Linux : `ls /dev/ttyUSB*` pour voir les ports disponibles
→ Sur Windows : Gestionnaire de périphériques → Ports COM
→ Sur Mac : `ls /dev/cu.*` 

---

## ➡️ Module suivant

**[Module 2 — Le dashboard naïf](../module-2-dashboard/README.md)**

Les données JSON de l'ESP32 vont maintenant alimenter un dashboard web interactif avec des graphiques en temps réel — et un premier regard critique sur les fragilités du système.

---

*Module 1 / Niveau 1 — Architecture pédagogique IoT v1.0*
