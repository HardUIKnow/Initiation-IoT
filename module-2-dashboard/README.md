# Module 2 — Le dashboard naïf

> *Streamlit · Visualisation locale · Premier audit sécurité*

[![Durée estimée](https://img.shields.io/badge/Durée-60%20min-blue)](.)
[![Difficulté](https://img.shields.io/badge/Difficulté-Débutant-brightgreen)](.)
[![Stack](https://img.shields.io/badge/Stack-Python%20%2B%20Streamlit-orange)](.)

---

## 🎯 Objectif du module

Transformer les données JSON du terminal (Module 1) en un **dashboard web interactif** avec graphiques en temps réel, jauges et alertes couleur. Puis, exercice fondamental : regarder ce système en face et identifier ce qui est fragile.

---

## ✅ Livrable

> **Application Streamlit avec graphiques temps réel de température / humidité / pression + sauvegarde CSV + audit des fragilités du système.**

![Dashboard preview](../../docs/screenshots/m2-dashboard-preview.png)

---

## 📋 Contenu du module

### 1. Streamlit — pourquoi ce choix ?

Streamlit permet de construire une interface web avec du Python pur — pas de HTML, pas de JavaScript, pas de CSS. Pour notre cas d'usage (données de capteurs en temps réel, usage local), c'est le choix idéal.

```bash
pip install streamlit
streamlit run dashboard/app.py
```

→ Ouvre automatiquement `http://localhost:8501` dans le navigateur.

### 2. Structure de l'application

```
module-2-dashboard/
├── README.md
├── backend/
│   └── serial_reader.py   ← Lecteur série (évolué du M1) + écriture CSV
└── dashboard/
    └── app.py             ← Application Streamlit
```

### 3. Premier audit de sécurité

Ce point est **fondamental** dans la pédagogie de ce cours. À la fin du Module 2, vous identifiez les fragilités de ce que vous venez de construire :

| Fragilité | Ce qui se passe concrètement |
|-----------|------------------------------|
| Données en clair sur port série | Pas de chiffrement — interceptable |
| Pas de résilience | Le script plante si le câble USB est débranché |
| Pas de vraie persistance | Les données CSV sont perdues si le disque est plein ou le fichier corrompu |
| Point de défaillance unique | Tout sur une seule machine — pas de redondance |
| Aucune authentification | N'importe qui sur le réseau local peut accéder au dashboard |
| Monitoring externe impossible | Le dashboard n'est accessible que sur le réseau local |

> Cet audit n'est pas une honte — c'est **la carte du voyage**. Chaque fragilité identifiée ici sera résolue dans les modules suivants.

---

## 🔧 Code

### Backend — Lecteur série avec CSV

**`backend/serial_reader.py`**

```python
#!/usr/bin/env python3
"""
Module 2 — Lecteur série avec persistance CSV
Lit les données de l'ESP32 et les écrit dans un fichier CSV partagé
avec le dashboard Streamlit.
"""

import serial
import serial.tools.list_ports
import json
import csv
import sys
import time
import os
from datetime import datetime
from pathlib import Path


# Fichier CSV partagé entre le backend et le dashboard
CSV_FILE = Path(__file__).parent.parent / "dashboard" / "data.csv"
CSV_COLUMNS = ["timestamp", "temperature_c", "humidity_pct", "pressure_hpa", "altitude_m"]
MAX_LIGNES_CSV = 1000  # Limiter la taille du fichier en mémoire


def initialiser_csv():
    """Crée le fichier CSV avec les en-têtes s'il n'existe pas."""
    if not CSV_FILE.exists():
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
        print(f"[INFO] Fichier CSV créé : {CSV_FILE}")


def ecrire_mesure_csv(donnees: dict):
    """Ajoute une mesure au fichier CSV."""
    ligne = {col: donnees.get(col, "") for col in CSV_COLUMNS}
    ligne["timestamp"] = datetime.now().isoformat()

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerow(ligne)


def trouver_port_esp32() -> str | None:
    ports = serial.tools.list_ports.comports()
    puces_connues = ["CP210x", "CH340", "CH341", "FTDI", "Silicon Labs"]
    for port in ports:
        for puce in puces_connues:
            if puce.lower() in (port.description or "").lower():
                return port.device
    return ports[0].device if ports else None


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else trouver_port_esp32()

    if port is None:
        print("[ERREUR] Aucun ESP32 détecté.")
        sys.exit(1)

    initialiser_csv()
    print(f"[INFO] Connexion sur {port}")
    print(f"[INFO] Données enregistrées dans : {CSV_FILE}")
    print(f"[INFO] Ctrl+C pour arrêter\n")

    try:
        ser = serial.Serial(port, baudrate=115200, timeout=5)
    except serial.SerialException as e:
        print(f"[ERREUR] {e}")
        sys.exit(1)

    try:
        while True:
            try:
                ligne = ser.readline().decode("utf-8").strip()
                if not ligne or not ligne.startswith("{"):
                    continue

                donnees = json.loads(ligne)
                ecrire_mesure_csv(donnees)

                # Affichage console minimal
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                    f"T={donnees.get('temperature_c', '?')}°C  "
                    f"H={donnees.get('humidity_pct', '?')}%  "
                    f"P={donnees.get('pressure_hpa', '?')}hPa  "
                    f"→ CSV ✓"
                )

            except json.JSONDecodeError:
                pass
            except UnicodeDecodeError:
                pass
            except serial.SerialException:
                print("[WARN] Perte de connexion, tentative de reconnexion...")
                time.sleep(2)
                try:
                    ser.close()
                    ser.open()
                    print("[INFO] Reconnexion réussie")
                except Exception:
                    pass

    except KeyboardInterrupt:
        print("\n[INFO] Arrêt.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
```

### Dashboard Streamlit

**`dashboard/app.py`**

```python
#!/usr/bin/env python3
"""
Module 2 — Dashboard Streamlit
Visualisation en temps réel des données de la station météo.

Démarrage :
    streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import time
from pathlib import Path
from datetime import datetime

# ─── Configuration de la page ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Station Météo IoT",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Constantes ───────────────────────────────────────────────────────────────
CSV_FILE = Path(__file__).parent / "data.csv"
REFRESH_INTERVAL_S = 2

# Seuils d'alerte
SEUIL_TEMP_MAX  = 30.0
SEUIL_TEMP_MIN  = 5.0
SEUIL_HUMID_MAX = 80.0
SEUIL_HUMID_MIN = 20.0


# ─── Chargement des données ───────────────────────────────────────────────────
@st.cache_data(ttl=REFRESH_INTERVAL_S)
def charger_donnees() -> pd.DataFrame:
    """Charge les données CSV. Retourne un DataFrame vide si le fichier n'existe pas."""
    if not CSV_FILE.exists():
        return pd.DataFrame(columns=["timestamp", "temperature_c", "humidity_pct",
                                      "pressure_hpa", "altitude_m"])

    try:
        df = pd.read_csv(CSV_FILE, parse_dates=["timestamp"])
        # Garder les 200 dernières mesures pour les graphiques
        return df.tail(200).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


# ─── Interface ────────────────────────────────────────────────────────────────
st.title("🌦️ Station Météo IoT — Dashboard")
st.caption(f"Rafraîchissement toutes les {REFRESH_INTERVAL_S} secondes · Module 2")

# Sidebar — configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    auto_refresh = st.toggle("Rafraîchissement automatique", value=True)
    nb_points    = st.slider("Points affichés", min_value=20, max_value=200, value=60)
    st.divider()
    st.header("🌡️ Seuils d'alerte")
    temp_max = st.number_input("Temp. max (°C)", value=SEUIL_TEMP_MAX)
    temp_min = st.number_input("Temp. min (°C)", value=SEUIL_TEMP_MIN)
    st.divider()
    if st.button("🗑️ Effacer les données"):
        if CSV_FILE.exists():
            CSV_FILE.unlink()
        st.rerun()

# Chargement des données
df = charger_donnees()

if df.empty:
    st.warning(
        "⏳ En attente de données...\n\n"
        "Démarrer le backend : `python backend/serial_reader.py`"
    )
    if auto_refresh:
        time.sleep(REFRESH_INTERVAL_S)
        st.rerun()
    st.stop()

df_affiche = df.tail(nb_points)
derniere = df.iloc[-1]

# ─── Métriques en temps réel ──────────────────────────────────────────────────
st.subheader("📊 Valeurs actuelles")
col1, col2, col3, col4 = st.columns(4)

with col1:
    temp = derniere.get("temperature_c", None)
    if pd.notna(temp):
        delta = f"{temp - df['temperature_c'].mean():.1f}°C vs moyenne" if len(df) > 1 else None
        couleur = "🔴" if temp > temp_max or temp < temp_min else "🟢"
        st.metric(f"{couleur} Température", f"{temp:.1f} °C", delta=delta)

with col2:
    hum = derniere.get("humidity_pct", None)
    if pd.notna(hum):
        delta = f"{hum - df['humidity_pct'].mean():.1f}% vs moyenne" if len(df) > 1 else None
        couleur = "🔴" if hum > SEUIL_HUMID_MAX or hum < SEUIL_HUMID_MIN else "🟢"
        st.metric(f"{couleur} Humidité", f"{hum:.1f} %", delta=delta)

with col3:
    pression = derniere.get("pressure_hpa", None)
    if pd.notna(pression):
        st.metric("🔵 Pression", f"{pression:.1f} hPa")

with col4:
    altitude = derniere.get("altitude_m", None)
    if pd.notna(altitude):
        st.metric("⛰️ Altitude estimée", f"{altitude:.1f} m")

st.divider()

# ─── Graphiques temporels ─────────────────────────────────────────────────────
st.subheader("📈 Historique")

col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("**🌡️ Température (°C)**")
    if "temperature_c" in df_affiche.columns:
        st.line_chart(
            df_affiche.set_index("timestamp")["temperature_c"],
            use_container_width=True,
            color="#FF6B6B",
        )

with col_g2:
    st.markdown("**💧 Humidité (%)**")
    if "humidity_pct" in df_affiche.columns:
        st.line_chart(
            df_affiche.set_index("timestamp")["humidity_pct"],
            use_container_width=True,
            color="#4ECDC4",
        )

st.markdown("**🔵 Pression atmosphérique (hPa)**")
if "pressure_hpa" in df_affiche.columns:
    st.line_chart(
        df_affiche.set_index("timestamp")["pressure_hpa"],
        use_container_width=True,
        color="#45B7D1",
    )

# ─── Alertes ─────────────────────────────────────────────────────────────────
alertes = []
if pd.notna(temp) and temp > temp_max:
    alertes.append(f"🌡️ Température trop élevée : {temp:.1f}°C > {temp_max}°C")
if pd.notna(temp) and temp < temp_min:
    alertes.append(f"🥶 Température trop basse : {temp:.1f}°C < {temp_min}°C")
if pd.notna(hum) and hum > SEUIL_HUMID_MAX:
    alertes.append(f"💧 Humidité trop élevée : {hum:.1f}% > {SEUIL_HUMID_MAX}%")

if alertes:
    st.divider()
    st.subheader("⚠️ Alertes actives")
    for alerte in alertes:
        st.error(alerte)

# ─── Données brutes ───────────────────────────────────────────────────────────
with st.expander("📋 Données brutes (dernières mesures)"):
    st.dataframe(df_affiche.tail(20), use_container_width=True)

    # Téléchargement CSV
    csv_export = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Télécharger le CSV complet",
        data=csv_export,
        file_name=f"station_meteo_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

# ─── Audit sécurité ───────────────────────────────────────────────────────────
with st.expander("⚠️ Audit — Ce qui est fragile dans ce système"):
    st.markdown("""
    À la fin du Module 2, voici les fragilités à identifier dans notre système :

    | Fragilité | Symptôme | Résolu au... |
    |-----------|----------|--------------|
    | Données en clair sur port série | Pas de chiffrement | Module 8 (TLS) |
    | Pas de résilience | Crash si câble débranché | Module 4 (Docker) |
    | Pas de vraie persistance | Données perdues au redémarrage | Module 5 (InfluxDB) |
    | Point de défaillance unique | Tout sur une machine | Module 3 (MQTT + RPi) |
    | Aucune authentification | N'importe qui peut lire le dashboard | Module 8 (ACL) |
    | Impossible de monitorer depuis l'extérieur | Réseau local uniquement | Module 12 (VPS) |

    > Cet audit plante les graines qui justifient chaque module suivant.
    > L'étudiant comprend **pourquoi** il apprend ce qu'il apprend.
    """)

# ─── Rafraîchissement automatique ────────────────────────────────────────────
st.divider()
st.caption(f"Dernière mise à jour : {datetime.now().strftime('%H:%M:%S')} · {len(df)} mesures enregistrées")

if auto_refresh:
    time.sleep(REFRESH_INTERVAL_S)
    st.rerun()
```

---

## 🚀 Démarrage

```bash
# Terminal 1 — Backend (lecture série + CSV)
cd module-2-dashboard
python backend/serial_reader.py

# Terminal 2 — Dashboard (interface web)
pip install streamlit pandas
streamlit run dashboard/app.py
# → Ouvre http://localhost:8501 dans le navigateur
```

---

## 🧪 Vérification

Votre module 2 est terminé si :

- [ ] Le backend écrit les données dans `dashboard/data.csv`
- [ ] Le dashboard s'ouvre sur `http://localhost:8501`
- [ ] Les 4 métriques (température, humidité, pression, altitude) s'affichent
- [ ] Les graphiques se mettent à jour toutes les 2 secondes
- [ ] Les alertes s'affichent quand un seuil est dépassé
- [ ] Le CSV peut être téléchargé depuis le dashboard
- [ ] **Vous avez lu et compris l'audit de sécurité**

---

## ⚠️ L'audit — Ce qui est fragile

Ce système fonctionne. Mais il est fragile. Voici pourquoi chaque point compte :

**1. Données en clair**
Les données transitent du capteur vers Python via USB, puis sont stockées dans un CSV en clair sur votre disque. Aucun chiffrement à aucune étape.

**2. Pas de résilience**
Débranchez le câble USB : le script `serial_reader.py` plante. Il faut le relancer manuellement. Sur un vrai système, personne ne surveille 24h/24.

**3. Pas de vraie persistance**
Le CSV grossit indéfiniment. Il n'y a pas de politique de rétention, pas de backup, pas de détection de corruption.

**4. Point de défaillance unique**
Votre ordinateur est le capteur, le broker, la base de données et le dashboard. Si votre machine redémarre, tout s'arrête.

**5. Aucune authentification**
N'importe qui sur votre réseau WiFi peut accéder au dashboard sur `http://IP_DE_VOTRE_MACHINE:8501`.

**6. Monitoring externe impossible**
Le dashboard n'est visible que depuis votre réseau local. Impossible de surveiller depuis l'extérieur sans configuration complexe.

> Ces 6 points seront résolus un par un dans les niveaux 2 et 3.

---

## 🎓 Conclusion du Niveau 1

Félicitations ! Vous avez construit votre première station météo IoT fonctionnelle. Ce que vous maîtrisez maintenant :

- ✅ Environnement de développement professionnel (VS Code + PlatformIO + Git)
- ✅ Programmation ESP32 avec deux capteurs (DHT22 + BMP280)
- ✅ Communication série et parsing JSON en Python
- ✅ Dashboard web temps réel avec Streamlit
- ✅ Identification des fragilités d'un système simple

**La suite → [Niveau 2 — Je structure](../../niveau-2/)** : MQTT, Raspberry Pi, Docker, InfluxDB, Grafana.

---

*Module 2 / Niveau 1 — Architecture pédagogique IoT v1.0*
