# 🌦️ Niveau 1 — Je construis

> **De zéro à un dashboard météo fonctionnel en moins de 3 heures**

[![Niveau](https://img.shields.io/badge/Niveau-Débutant-brightgreen)](.)
[![Modules](https://img.shields.io/badge/Modules-3-blue)](.)
[![Matériel](https://img.shields.io/badge/Matériel-ESP32%20%2B%20Raspberry%20Pi-orange)](.)
[![Licence](https://img.shields.io/badge/Licence-MIT-lightgrey)](.)

---

## 🎯 Objectif du Niveau 1

Le Niveau 1 est la porte d'entrée du cours. Aucun prérequis technique n'est exigé. À la fin de ce niveau, vous aurez construit **une station météo complète** qui affiche en temps réel température, humidité et pression atmosphérique dans un dashboard web.

> **Ce niveau est diffusé gratuitement sur YouTube.** Il sert de vitrine et de première victoire concrète avant d'aborder les niveaux 2 (architecture) et 3 (sécurité).

---

## 📦 Les 3 modules

| Module | Titre | Ce que vous construisez |
|--------|-------|------------------------|
| [M0 — Environnement](./module-0-environnement/) | L'environnement professionnel | Dépôt Git + structure de projet + LED qui clignote via PlatformIO |
| [M1 — Capteurs](./module-1-capteurs/) | Le capteur parle | Terminal Python affichant température / humidité / pression en JSON temps réel |
| [M2 — Dashboard](./module-2-dashboard/) | Le dashboard naïf | Application Streamlit avec graphiques en direct + audit des fragilités |

---

## 🗺️ Progression pédagogique

```
M0 : Environnement professionnel
│   VS Code · PlatformIO · Git · Datasheet · Breadboard
│   ✅ Livrable : dépôt Git initialisé + LED qui clignote
│
▼
M1 : Le capteur parle
│   ESP32 · DHT22 · BMP280 · I2C · JSON · pyserial
│   ✅ Livrable : terminal Python → données capteurs structurées en JSON
│
▼
M2 : Le dashboard naïf
    Streamlit · Graphiques temps réel · CSV · Audit sécurité
    ✅ Livrable : dashboard local + liste des fragilités identifiées
```

---

## 🛠️ Matériel requis

| Composant | Référence recommandée | Alternative |
|-----------|-----------------------|-------------|
| Microcontrôleur | ESP32 DevKit v1 (30 broches) | ESP32-S3, ESP32-C3 |
| Température / Humidité | DHT22 (AM2302) | SHT31 (I2C), HDC1080 |
| Pression / Altitude | BMP280 | BME280, BMP388 |
| Câble | USB-A → micro-USB ou USB-C | selon variante ESP32 |
| Prototypage | Breadboard 400 pts + jumpers M/F | — |

**Coût estimé du kit Niveau 1 : 15–20 €** (ESP32 + capteurs + breadboard + câbles)

> Le Raspberry Pi n'est pas nécessaire au Niveau 1. Il sera introduit au Module 3 (Niveau 2).

---

## 💻 Logiciels requis

- [VS Code](https://code.visualstudio.com/) + extension [PlatformIO](https://platformio.org/)
- [Git](https://git-scm.com/)
- [Python 3.10+](https://www.python.org/) + pip
- Bibliothèques Python : `pyserial`, `streamlit`, `pandas`

---

## 🚀 Démarrage rapide

```bash
# 1. Cloner ce dépôt
git clone https://github.com/votre-compte/iot-station-meteo.git
cd iot-station-meteo/niveau-1

# 2. Installer les dépendances Python
pip install -r requirements.txt

# 3. Suivre les modules dans l'ordre
# → Commencer par module-0-environnement/README.md
```

---

## 📋 Structure du dépôt

```
niveau-1/
├── README.md                        ← Vous êtes ici
├── requirements.txt                 ← Dépendances Python communes
├── module-0-environnement/
│   ├── README.md
│   └── firmware/
│       └── blink/                   ← Projet PlatformIO LED
├── module-1-capteurs/
│   ├── README.md
│   ├── firmware/
│   │   └── station-meteo/          ← Firmware ESP32 complet
│   └── backend/
│       └── serial_reader.py        ← Lecture port série → JSON
└── module-2-dashboard/
    ├── README.md
    ├── backend/
    │   └── serial_reader.py        ← Lecteur série (avec CSV)
    └── dashboard/
        └── app.py                  ← Application Streamlit
```

---

## 🔍 Le fil conducteur : la station météo

Ce projet n'est pas un exercice jetable. La **station météo** est le fil rouge de tout le cours :

- **Niveau 1** → données en direct sur un dashboard local
- **Niveau 2** → communication MQTT, Docker, historique 30 jours, Grafana
- **Niveau 3** → chiffrement TLS, threat modeling, pentesting, déploiement cloud

Chaque module justifie le suivant. Vous ne construisez pas des gadgets déconnectés, vous faites **évoluer un vrai système**.

---

## ⚠️ L'audit de fin de Niveau 1

À la fin du Module 2, vous serez invité à regarder votre propre travail de façon critique. Voici ce que vous aurez construit — et ce qui est fragile :

| Fragilité | Symptôme | Solution (Niveau 2+) |
|-----------|----------|----------------------|
| Données en clair sur port série | Pas de chiffrement | TLS (Module 8) |
| Pas de résilience | Crash si câble débranché | Docker + restart policies (Module 4) |
| Pas de vraie persistance | Données perdues au redémarrage | InfluxDB (Module 5) |
| Point de défaillance unique | Tout sur une machine | Architecture distribuée (Module 3) |
| Aucune authentification | N'importe qui peut lire | ACL + certificats (Module 8) |
| Pas de monitoring externe | Invisible hors réseau local | VPS + Traefik (Module 12) |

> Cet audit n'est pas une critique — c'est la **carte du voyage** qui justifie chaque module suivant.

---

## 📚 Pour aller plus loin

- [Niveau 2 — Je structure](../niveau-2/) : MQTT, Docker, InfluxDB, Grafana
- [Niveau 3 — Je sécurise & déploie](../niveau-3/) : TLS, Threat Modeling, Pentesting, VPS
- [Guide hardware complet](../docs/hardware-guide.md)
- [FAQ débutants](../docs/faq.md)

---

## 🤝 Contribuer

Ce dépôt est la base pédagogique du cours. Les issues et PR sont bienvenus pour :
- Corrections de bugs dans les exemples de code
- Ajout d'alternatives matérielles testées
- Traductions de commentaires

---

*Architecture pédagogique v1.0 — Document de référence disponible dans `/docs/`*
