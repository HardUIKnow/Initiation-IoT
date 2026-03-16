#!/usr/bin/env python3
"""
Module 2 — Dashboard Streamlit
Visualisation en temps réel des données de la station météo.

Démarrage :
    streamlit run dashboard/app.py
Puis ouvrir : http://localhost:8501
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

# Seuils d'alerte par défaut
SEUIL_TEMP_MAX  = 30.0
SEUIL_TEMP_MIN  = 5.0
SEUIL_HUMID_MAX = 80.0
SEUIL_HUMID_MIN = 20.0


# ─── Chargement des données ───────────────────────────────────────────────────
@st.cache_data(ttl=REFRESH_INTERVAL_S)
def charger_donnees() -> pd.DataFrame:
    """Charge les données CSV. Retourne un DataFrame vide si le fichier n'existe pas."""
    if not CSV_FILE.exists():
        return pd.DataFrame(
            columns=["timestamp", "temperature_c", "humidity_pct", "pressure_hpa", "altitude_m"]
        )
    try:
        df = pd.read_csv(CSV_FILE, parse_dates=["timestamp"])
        return df.tail(500).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


# ─── Interface principale ─────────────────────────────────────────────────────
st.title("🌦️ Station Météo IoT")
st.caption(f"Module 2 — Dashboard naïf · Rafraîchissement toutes les {REFRESH_INTERVAL_S}s")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")
    auto_refresh = st.toggle("Rafraîchissement auto", value=True)
    nb_points    = st.slider("Points affichés", min_value=20, max_value=200, value=60)

    st.divider()
    st.header("🌡️ Seuils d'alerte")
    temp_max  = st.number_input("Température max (°C)",  value=SEUIL_TEMP_MAX)
    temp_min  = st.number_input("Température min (°C)",  value=SEUIL_TEMP_MIN)
    humid_max = st.number_input("Humidité max (%)",       value=SEUIL_HUMID_MAX)
    humid_min = st.number_input("Humidité min (%)",       value=SEUIL_HUMID_MIN)

    st.divider()
    if st.button("🗑️ Effacer les données", type="secondary"):
        if CSV_FILE.exists():
            CSV_FILE.unlink()
            st.success("Données effacées.")
        st.rerun()

# ── Chargement ────────────────────────────────────────────────────────────────
df = charger_donnees()

if df.empty:
    st.warning(
        "⏳ **En attente de données...**\n\n"
        "Démarrer le backend dans un terminal :\n"
        "```bash\npython backend/serial_reader.py\n```"
    )
    if auto_refresh:
        time.sleep(REFRESH_INTERVAL_S)
        st.rerun()
    st.stop()

df_affiche = df.tail(nb_points)
derniere   = df.iloc[-1]

# ── Métriques ─────────────────────────────────────────────────────────────────
st.subheader("📊 Valeurs actuelles")
col1, col2, col3, col4 = st.columns(4)

with col1:
    temp = derniere.get("temperature_c")
    if pd.notna(temp):
        delta = f"{temp - df['temperature_c'].mean():.1f}°C vs moy." if len(df) > 1 else None
        indicateur = " ⚠️" if temp > temp_max or temp < temp_min else ""
        st.metric(f"🌡️ Température{indicateur}", f"{temp:.1f} °C", delta=delta)

with col2:
    hum = derniere.get("humidity_pct")
    if pd.notna(hum):
        delta = f"{hum - df['humidity_pct'].mean():.1f}% vs moy." if len(df) > 1 else None
        indicateur = " ⚠️" if hum > humid_max or hum < humid_min else ""
        st.metric(f"💧 Humidité{indicateur}", f"{hum:.1f} %", delta=delta)

with col3:
    pression = derniere.get("pressure_hpa")
    if pd.notna(pression):
        st.metric("🔵 Pression", f"{pression:.1f} hPa")

with col4:
    altitude = derniere.get("altitude_m")
    if pd.notna(altitude):
        st.metric("⛰️ Altitude", f"{altitude:.1f} m")

st.divider()

# ── Graphiques ────────────────────────────────────────────────────────────────
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

# ── Alertes ───────────────────────────────────────────────────────────────────
alertes = []
if pd.notna(temp):
    if temp > temp_max:
        alertes.append(f"🌡️ Température trop élevée : {temp:.1f}°C > {temp_max}°C")
    if temp < temp_min:
        alertes.append(f"🥶 Température trop basse : {temp:.1f}°C < {temp_min}°C")
if pd.notna(hum):
    if hum > humid_max:
        alertes.append(f"💧 Humidité trop élevée : {hum:.1f}% > {humid_max}%")
    if hum < humid_min:
        alertes.append(f"🏜️ Humidité trop basse : {hum:.1f}% < {humid_min}%")

if alertes:
    st.divider()
    st.subheader("⚠️ Alertes actives")
    for alerte in alertes:
        st.error(alerte)

# ── Données brutes ────────────────────────────────────────────────────────────
with st.expander("📋 Données brutes"):
    st.dataframe(df_affiche.tail(20), use_container_width=True)
    csv_export = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Télécharger le CSV complet",
        data=csv_export,
        file_name=f"station_meteo_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

# ── Audit sécurité ────────────────────────────────────────────────────────────
with st.expander("⚠️ Audit — Ce qui est fragile dans ce système (cliquer pour lire)"):
    st.markdown("""
    ### Ce qui est fragile — et pourquoi ça compte

    | Fragilité | Symptôme concret | Résolu au... |
    |-----------|-----------------|--------------|
    | Données en clair sur port série | Interceptable sur le réseau local | Module 8 — TLS |
    | Pas de résilience | Crash si câble USB débranché | Module 4 — Docker |
    | Pas de vraie persistance | CSV perdu si disque plein ou machine redémarrée | Module 5 — InfluxDB |
    | Point de défaillance unique | Tout sur une machine | Module 3 — MQTT + Raspberry Pi |
    | Aucune authentification | N'importe qui sur le réseau peut lire ce dashboard | Module 8 — ACL |
    | Monitoring externe impossible | Visible seulement sur le réseau local | Module 12 — VPS |

    > Ces 6 points seront résolus un par un dans les niveaux 2 et 3.
    > Chaque module existe parce qu'une de ces fragilités le justifie.
    """)

# ── Pied de page ──────────────────────────────────────────────────────────────
st.divider()
st.caption(
    f"Dernière mise à jour : {datetime.now().strftime('%H:%M:%S')} · "
    f"{len(df)} mesures enregistrées · "
    f"Données depuis : {df['timestamp'].min().strftime('%d/%m %H:%M') if len(df) > 0 else 'N/A'}"
)

# ── Rafraîchissement automatique ──────────────────────────────────────────────
if auto_refresh:
    time.sleep(REFRESH_INTERVAL_S)
    st.rerun()
