#!/usr/bin/env python3
"""
Module 1 — Lecteur port série
Reçoit les données JSON de l'ESP32 et les affiche dans le terminal.

Usage:
    python serial_reader.py                  # Détection automatique du port
    python serial_reader.py /dev/ttyUSB0    # Linux — port explicite
    python serial_reader.py COM3            # Windows — port explicite
"""

import serial
import serial.tools.list_ports
import json
import sys
import time
from datetime import datetime


def trouver_port_esp32() -> str | None:
    """Détecte automatiquement le port série de l'ESP32."""
    ports = serial.tools.list_ports.comports()
    puces_connues = ["CP210x", "CH340", "CH341", "FTDI", "Silicon Labs"]

    for port in ports:
        for puce in puces_connues:
            if puce.lower() in (port.description or "").lower():
                print(f"[INFO] ESP32 détecté automatiquement : {port.device} ({port.description})")
                return port.device

    if ports:
        print(f"[WARN] Puce non reconnue, utilisation de {ports[0].device}")
        return ports[0].device

    return None


def afficher_mesure(donnees: dict) -> None:
    """Affiche une mesure de façon lisible dans le terminal."""
    heure = datetime.now().strftime("%H:%M:%S")

    print(f"\n{'─' * 45}")
    print(f"  📡  Mesure reçue à {heure}")
    print(f"{'─' * 45}")

    if "temperature_c" in donnees:
        temp = donnees["temperature_c"]
        emoji = "🥵" if temp > 30 else ("🥶" if temp < 10 else "🌡️")
        print(f"  {emoji}  Température : {temp:.1f} °C")

    if "humidity_pct" in donnees:
        hum = donnees["humidity_pct"]
        print(f"  💧  Humidité    : {hum:.1f} %")

    if "pressure_hpa" in donnees:
        pression = donnees["pressure_hpa"]
        print(f"  🔵  Pression    : {pression:.1f} hPa")

    if "altitude_m" in donnees:
        alt = donnees["altitude_m"]
        print(f"  ⛰️   Altitude    : {alt:.1f} m")

    print(f"  ⏱️   Horodatage  : {donnees.get('timestamp', 'N/A')}")


def main():
    # ── Détection ou saisie du port ────────────────────────────────────────────
    if len(sys.argv) > 1:
        port = sys.argv[1]
        print(f"[INFO] Port spécifié : {port}")
    else:
        port = trouver_port_esp32()

    if port is None:
        print("[ERREUR] Aucun ESP32 détecté.")
        print("  → Vérifier que l'ESP32 est branché en USB")
        print("  → Ou spécifier le port : python serial_reader.py /dev/ttyUSB0")
        sys.exit(1)

    print(f"[INFO] Connexion sur {port} à 115200 baud...")
    print(f"[INFO] Appuyer sur Ctrl+C pour arrêter.\n")

    # ── Connexion série ────────────────────────────────────────────────────────
    try:
        ser = serial.Serial(port, baudrate=115200, timeout=5)
    except serial.SerialException as e:
        print(f"[ERREUR] Impossible d'ouvrir {port} : {e}")
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

                # Afficher les logs ESP32 (non-JSON)
                if not ligne.startswith("{"):
                    print(f"  [ESP32] {ligne}")
                    continue

                # Parser et afficher les données JSON
                donnees = json.loads(ligne)
                afficher_mesure(donnees)
                erreurs_consecutives = 0

            except json.JSONDecodeError:
                print(f"  [WARN] Ligne ignorée (JSON invalide) : {ligne[:60]}...")

            except UnicodeDecodeError:
                pass  # Ignorer les bytes parasites au démarrage

            except serial.SerialException:
                erreurs_consecutives += 1
                print(f"\n[ERREUR] Perte de connexion ({erreurs_consecutives}/{MAX_ERREURS})")

                if erreurs_consecutives >= MAX_ERREURS:
                    print("[FATAL] Trop d'erreurs consécutives — arrêt.")
                    break

                print("[INFO] Tentative de reconnexion dans 2 secondes...")
                time.sleep(2)
                try:
                    ser.close()
                    ser.open()
                    print("[INFO] Reconnexion réussie ✓")
                    erreurs_consecutives = 0
                except Exception:
                    print("[WARN] Reconnexion échouée, nouvelle tentative...")

    except KeyboardInterrupt:
        print("\n\n[INFO] Arrêt demandé par l'utilisateur.")

    finally:
        ser.close()
        print("[INFO] Port série fermé proprement.")


if __name__ == "__main__":
    main()
