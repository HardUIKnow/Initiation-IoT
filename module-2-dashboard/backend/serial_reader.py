#!/usr/bin/env python3
"""
Module 2 — Lecteur série avec persistance CSV
Lit les données de l'ESP32 et les écrit dans un fichier CSV partagé
avec le dashboard Streamlit.

Usage:
    python backend/serial_reader.py                  # Détection automatique
    python backend/serial_reader.py /dev/ttyUSB0    # Port explicite
"""

import serial
import serial.tools.list_ports
import json
import csv
import sys
import time
from datetime import datetime
from pathlib import Path


# ─── Configuration ────────────────────────────────────────────────────────────
CSV_FILE = Path(__file__).parent.parent / "dashboard" / "data.csv"
CSV_COLUMNS = ["timestamp", "temperature_c", "humidity_pct", "pressure_hpa", "altitude_m"]


def initialiser_csv():
    """Crée le fichier CSV avec les en-têtes s'il n'existe pas."""
    CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not CSV_FILE.exists():
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
        print(f"[INFO] Fichier CSV créé : {CSV_FILE}")
    else:
        print(f"[INFO] Fichier CSV existant : {CSV_FILE}")


def ecrire_mesure_csv(donnees: dict):
    """Ajoute une mesure au fichier CSV avec horodatage système."""
    ligne = {col: donnees.get(col, "") for col in CSV_COLUMNS}
    ligne["timestamp"] = datetime.now().isoformat()

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerow(ligne)


def trouver_port_esp32() -> str | None:
    """Détecte automatiquement le port série de l'ESP32."""
    ports = serial.tools.list_ports.comports()
    puces_connues = ["CP210x", "CH340", "CH341", "FTDI", "Silicon Labs"]
    for port in ports:
        for puce in puces_connues:
            if puce.lower() in (port.description or "").lower():
                print(f"[INFO] ESP32 détecté : {port.device} ({port.description})")
                return port.device
    if ports:
        print(f"[WARN] Puce non reconnue, utilisation de {ports[0].device}")
        return ports[0].device
    return None


def main():
    # ── Port ──────────────────────────────────────────────────────────────────
    port = sys.argv[1] if len(sys.argv) > 1 else trouver_port_esp32()

    if port is None:
        print("[ERREUR] Aucun ESP32 détecté.")
        sys.exit(1)

    initialiser_csv()

    print(f"[INFO] Connexion sur {port} à 115200 baud")
    print(f"[INFO] Écriture dans : {CSV_FILE}")
    print(f"[INFO] Ctrl+C pour arrêter\n")

    try:
        ser = serial.Serial(port, baudrate=115200, timeout=5)
    except serial.SerialException as e:
        print(f"[ERREUR] Impossible d'ouvrir {port} : {e}")
        sys.exit(1)

    # ── Boucle de lecture ──────────────────────────────────────────────────────
    try:
        while True:
            try:
                ligne = ser.readline().decode("utf-8").strip()

                if not ligne:
                    continue

                if not ligne.startswith("{"):
                    print(f"  [ESP32] {ligne}")
                    continue

                donnees = json.loads(ligne)
                ecrire_mesure_csv(donnees)

                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                    f"T={donnees.get('temperature_c', '?'):5.1f}°C  "
                    f"H={donnees.get('humidity_pct', '?'):5.1f}%  "
                    f"P={donnees.get('pressure_hpa', '?'):7.1f}hPa  "
                    f"→ CSV ✓"
                )

            except json.JSONDecodeError:
                pass
            except UnicodeDecodeError:
                pass
            except serial.SerialException:
                print("[WARN] Perte de connexion, tentative de reconnexion dans 2s...")
                time.sleep(2)
                try:
                    ser.close()
                    ser.open()
                    print("[INFO] Reconnexion réussie ✓")
                except Exception:
                    print("[WARN] Reconnexion échouée, nouvelle tentative...")

    except KeyboardInterrupt:
        print("\n[INFO] Arrêt demandé.")
    finally:
        ser.close()
        print("[INFO] Port série fermé proprement.")


if __name__ == "__main__":
    main()
