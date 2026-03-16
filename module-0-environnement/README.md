# Module 0 — L'environnement professionnel

> *La base que les autres formations ignorent*

[![Durée estimée](https://img.shields.io/badge/Durée-45%20min-blue)](.)
[![Difficulté](https://img.shields.io/badge/Difficulté-Débutant-brightgreen)](.)
[![Matériel](https://img.shields.io/badge/Matériel-ESP32%20%2B%20LED-orange)](.)

---

## 🎯 Objectif du module

La majorité des formations IoT commencent avec le premier capteur. Ce module fait le choix inverse : **installer de bonnes habitudes dès le premier jour** — des habitudes qu'un technicien professionnel a naturellement.

À la fin de ce module, vous aurez :
- Un environnement de développement professionnel configuré
- Un dépôt Git opérationnel avec la bonne structure
- Un firmware qui fait clignoter une LED via PlatformIO

Simple en apparence. Professionnel dans la méthode.

---

## ✅ Livrable

> **Un dépôt Git initialisé avec la bonne arborescence, et une LED qui clignote via PlatformIO.**

```
projet-iot/
├── .gitignore          ← Exclusions ESP32 / PlatformIO
├── README.md
├── firmware/           ← Code embarqué (ESP32)
│   └── blink/
│       ├── platformio.ini
│       └── src/
│           └── main.cpp
├── backend/            ← Scripts Python (vide pour l'instant)
└── infra/              ← Configuration infrastructure (vide pour l'instant)
```

---

## 📋 Contenu du module

### 1. VS Code + PlatformIO vs. Arduino IDE

| Critère | Arduino IDE | VS Code + PlatformIO |
|---------|-------------|----------------------|
| Autocomplétion | Basique | Complète (IntelliSense) |
| Gestion des librairies | Manuelle | Déclarée dans `platformio.ini` |
| Multi-projets | Difficile | Natif |
| Git integration | Absente | Native dans VS Code |
| Débogage | Inexistant | Intégré |

> **Règle** : les professionnels n'utilisent pas Arduino IDE au-delà du prototypage rapide. Autant partir du bon outil.

### 2. Git dès le premier jour

Git n'est pas optionnel. Chaque ligne de code que vous écrirez dans ce cours sera versionnée.

```bash
# Initialisation du projet
git init projet-iot
cd projet-iot
git checkout -b main

# Premier commit
git add .
git commit -m "feat: initialisation structure projet IoT"

# Convention de commits recommandée
# feat:     nouvelle fonctionnalité
# fix:      correction de bug
# docs:     documentation
# chore:    maintenance (gitignore, configs...)
# refactor: restructuration sans changement de comportement
```

**`.gitignore` adapté à ESP32 / PlatformIO :**

```gitignore
# PlatformIO
.pio/
.pioenvs/
.piolibdeps/

# VS Code
.vscode/
*.code-workspace

# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/
*.env

# Données locales
*.csv
*.log
data/

# OS
.DS_Store
Thumbs.db
```

### 3. Lire une datasheet

Avant de brancher quoi que ce soit, prenez 5 minutes pour lire la datasheet du composant. Cette habitude vous évitera de **griller du matériel**.

Ce qu'on cherche dans une datasheet :
- **Tension d'alimentation** (VCC) : 3.3V ou 5V ? L'ESP32 est en 3.3V.
- **Broches de communication** : GPIO, I2C (SDA/SCL), SPI (MOSI/MISO/SCK/CS)
- **Pull-up requis** : certains capteurs (DHT22) nécessitent une résistance externe
- **Temps de démarrage** : certains capteurs ont besoin de quelques millisecondes avant d'être fiables

> 📄 Les datasheets des composants de ce cours sont dans le dossier [`/docs/datasheets/`](../../docs/datasheets/)

### 4. Premier câblage : LED clignotante

**Schéma de câblage :**

```
ESP32 DevKit v1
┌─────────────────┐
│           GPIO2 ├──── Résistance 220Ω ──── Anode LED (+) ──── GND
│           GND   ├──── Cathode LED (-)
└─────────────────┘
```

> ⚠️ **Règle de sécurité** : toujours insérer une résistance en série avec une LED. Sans résistance, la LED grille immédiatement (et parfois l'ESP32 avec elle).

**Calcul de la résistance :**
- Tension ESP32 GPIO : 3.3V
- Tension directe LED rouge : ~2V
- Courant souhaité : 10mA
- Résistance = (3.3 - 2) / 0.01 = **130Ω → arrondir à 220Ω** (valeur standard)

### 5. Arborescence de projet propre

```
projet-iot/
├── firmware/        ← JAMAIS de code Python ici
│   └── blink/
├── backend/         ← JAMAIS de code C++ ici
│   └── ...
└── infra/           ← Docker, configs, scripts déploiement
    └── ...
```

> Cette séparation paraît inutile maintenant. Elle devient indispensable dès le Module 3.

---

## 🔧 Installation pas à pas

### Étape 1 : VS Code + PlatformIO

1. Télécharger [VS Code](https://code.visualstudio.com/)
2. Ouvrir VS Code → Extensions (`Ctrl+Shift+X`) → rechercher **PlatformIO IDE** → Installer
3. Redémarrer VS Code

### Étape 2 : Créer le projet PlatformIO

1. Icône PlatformIO dans la barre latérale → **New Project**
2. Nom : `blink`
3. Board : `Espressif ESP32 Dev Module`
4. Framework : `Arduino`
5. Location : dans votre dossier `firmware/`

### Étape 3 : Le firmware `blink`

**`firmware/blink/src/main.cpp`**

```cpp
#include <Arduino.h>

// GPIO2 = LED intégrée sur la plupart des ESP32 DevKit
const int LED_PIN = 2;

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  Serial.println("[BOOT] Station météo - Module 0");
  Serial.println("[INFO] LED configurée sur GPIO2");
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  Serial.println("[LED] ON");
  delay(1000);

  digitalWrite(LED_PIN, LOW);
  Serial.println("[LED] OFF");
  delay(1000);
}
```

**`firmware/blink/platformio.ini`**

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200
upload_speed = 921600
```

### Étape 4 : Compiler et flasher

```bash
# Via la ligne de commande PlatformIO
cd firmware/blink

# Compiler
pio run

# Flasher (ESP32 branché en USB)
pio run --target upload

# Ouvrir le moniteur série
pio device monitor --baud 115200
```

Ou via VS Code : bouton **→** (Upload) en bas de l'écran.

### Étape 5 : Commit du livrable

```bash
git add .
git commit -m "feat(M0): LED clignotante via PlatformIO - livrable module 0"
```

---

## 🧪 Vérification

Votre module 0 est terminé si :

- [ ] VS Code + PlatformIO installés
- [ ] Dépôt Git initialisé avec `.gitignore` adapté
- [ ] Arborescence `firmware/` / `backend/` / `infra/` créée
- [ ] LED clignote à 1 Hz sur l'ESP32
- [ ] Moniteur série affiche `[LED] ON` / `[LED] OFF`
- [ ] Commit effectué avec un message clair

---

## ❓ Problèmes fréquents

**ESP32 non détecté par l'ordinateur**
→ Installer le driver [CP210x](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers) (Windows/Mac) ou [CH340](https://github.com/nodemcu/nodemcu-devkit/tree/master/Drivers) selon la puce USB de votre board.

**`Permission denied` sur le port série (Linux)**
```bash
sudo usermod -aG dialout $USER
# Puis se déconnecter/reconnecter
```

**PlatformIO télécharge des dépendances au premier lancement**
→ Normal. La première compilation peut prendre 2–3 minutes.

---

## ➡️ Module suivant

**[Module 1 — Le capteur parle](../module-1-capteurs/README.md)**

L'ESP32 va maintenant lire de vraies données physiques : température, humidité, pression atmosphérique — et les envoyer en JSON vers Python.

---

*Module 0 / Niveau 1 — Architecture pédagogique IoT v1.0*
