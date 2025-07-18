import streamlit as st
import requests
from datetime import datetime, timedelta
from collections import Counter

# Configuración de la app
st.set_page_config(page_title="Dashboard Fidelo", layout="centered")
st.title("📊 Dashboard Fidelo Españolé")

# Token de la API (desde secrets)
API_URL = "https://ih-valencia.fidelo.com/api/1.0/ts/bookings"
HEADERS = {"Authorization": f"Bearer {st.secrets['FIDELO_TOKEN']}"}

# Fechas
today = datetime.today().date()
last_year_today = today - timedelta(days=365)
start_of_year = today.replace(month=1, day=1)

# Función para obtener reservas desde la API
@st.cache_data(ttl=600)
def get_bookings(start_date, end_date):
    params = {
        "start": str(start_date),
        "end": str(end_date),
        "limit": 5000  # Para asegurar que trae suficientes datos
    }
    response = requests.get(API_URL, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json().get("data", [])

# Obtener reservas de este año y del año pasado
bookings_this_year = get_bookings(start_of_year, today)
bookings_last_year = get_bookings(start_of_year - timedelta(days=365), last_year_today)

# Obtener reservas activas HOY
def count_active_today(bookings, reference_date):
    count = 0
    for b in bookings:
        try:
            course = b["booking"]["courses"][0]
            start = datetime.strptime(course["from"], "%Y-%m-%d").date()
            end = datetime.strptime(course["until"], "%Y-%m-%d").date()
            if start <= reference_date <= end:
                count += 1
        except Exception:
            continue
    return count

# Estudiantes activos hoy y hace un año
active_today = count_active_today(bookings_this_year, today)
active_last_year = count_active_today(bookings_last_year, last_year_today)
variation = active_today - active_last_year
variation_percent = (variation / active_last_year * 100) if active_last_year else 0

# Métrica 1: Estudiantes actuales
st.subheader("👥 Estudiantes actualmente en la escuela")
st.metric("Ahora", active_today, f"{variation_percent:+.1f}% vs. hace 1 año")

# Agencia con más estudiantes este año
agency_counter = Counter()
for b in bookings_this_year:
    try:
        agency_name = b.get("agency", {}).get("name")
        if agency_name:
            agency_counter[agency_name] += 1
    except Exception:
        continue

# Top agencia
if agency_counter:
    top_agency, count = agency_counter.most_common(1)[0]
    st.subheader("🏆 Agencia que más ha enviado en 2025")
    st.success(f"{top_agency} ({count} estudiantes)")
else:
    st.info("No hay datos de agencias disponibles.")
