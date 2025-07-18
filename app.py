import streamlit as st
import requests
from datetime import datetime, timedelta, date
from collections import Counter

# Configuración de la app
st.set_page_config(page_title="Dashboard Fidelo", layout="centered")
st.title("📊 Dashboard Fidelo Españolé")

# Token seguro desde secrets
API_URL = "https://ih-valencia.fidelo.com/api/1.0/ts/bookings"
HEADERS = {"Authorization": f"Bearer {st.secrets['FIDELO_TOKEN']}"}

# Fechas importantes
today = date.today()
last_year_today = today - timedelta(days=365)
start_of_year = today.replace(month=1, day=1)

# 🔁 Función para obtener reservas en un rango corto
@st.cache_data(ttl=600)
def get_bookings(start_date, end_date):
    params = {
        "start": str(start_date),
        "end": str(end_date),
        "limit": 500  # más que suficiente para 30 días
    }
    response = requests.get(API_URL, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json().get("data", [])

# 🔍 Contar estudiantes activos en una fecha concreta
def count_active_on_date(bookings, reference_date):
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

# 🔁 Función optimizada para estudiantes activos hoy / hace 1 año
def get_active_count(reference_date):
    delta = timedelta(days=15)
    bookings = get_bookings(reference_date - delta, reference_date + delta)
    return count_active_on_date(bookings, reference_date)

# 📊 Estudiantes activos hoy vs hace 1 año
active_today = get_active_count(today)
active_last_year = get_active_count(last_year_today)
variation = active_today - active_last_year
variation_percent = (variation / active_last_year * 100) if active_last_year else 0

# 👉 Mostrar métrica de estudiantes actuales
st.subheader("👥 Estudiantes actualmente en la escuela")
st.metric("Ahora", active_today, f"{variation_percent:+.1f}% vs. hace 1 año")

# 🏆 Agencia top del año (esto sí puede traer más datos)
@st.cache_data(ttl=3600)
def get_all_bookings_for_agency():
    return get_bookings(start_of_year, today)

bookings_year = get_all_bookings_for_agency()

# Contar estudiantes por agencia
agency_counter = Counter()
for b in bookings_year:
    try:
        agency_name = b.get("agency", {}).get("name")
        if agency_name:
            agency_counter[agency_name] += 1
    except Exception:
        continue

# Mostrar la agencia top
if agency_counter:
    top_agency, top_count = agency_counter.most_common(1)[0]
    st.subheader("🏆 Agencia que más ha enviado en 2025")
    st.success(f"{top_agency} ({top_count} estudiantes)")
else:
    st.info("No hay datos de agencias disponibles.")
