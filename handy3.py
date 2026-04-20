import streamlit as st
from transformers import pipeline
from PIL import Image, ImageDraw
import time

# --- SETUP ---
st.set_page_config(page_title="Safe Pomodoro", page_icon="🍅")

# Modell laden (DETR ist eine KI-Architektur ohne OpenCV-Zwang)
@st.cache_resource
def load_detector():
    # Wir laden ein Objekterkennungs-Modell von Hugging Face
    return pipeline("object-detection", model="facebook/detr-resnet-50")

detector = load_detector()

# --- TIMER LOGIK IM SESSION STATE ---
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "is_break" not in st.session_state:
    st.session_state.is_break = False

st.title("🍅 KI Pomodoro (Safe Mode)")
st.write("Diese Version nutzt keine Grafiktreiber und läuft rein über Python-Logik.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Timer")
    focus_m = st.slider("Arbeitszeit", 1, 60, 25)
    if st.button("Start / Reset"):
        st.session_state.start_time = time.time()
        st.session_state.is_break = False

# --- HAUPTTEIL ---
if st.session_state.start_time:
    elapsed = time.time() - st.session_state.start_time
    if elapsed < (focus_m * 60):
        st.warning("🔥 FOKUS PHASE: Handy-Check aktiv!")
        st.session_state.is_break = False
    else:
        st.success("☕ PAUSE: Du darfst dein Handy nutzen.")
        st.session_state.is_break = True

# Streamlit nativer Kamera-Input (braucht kein webrtc Paket)
img_file = st.camera_input("Scanner (Bitte lächeln oder Handy zeigen)")

if img_file and not st.session_state.is_break:
    img = Image.open(img_file)
    
    # KI-Analyse
    with st.spinner('KI prüft auf Handy...'):
        predictions = detector(img)
    
    found_phone = False
    for res in predictions:
        # DETR erkennt "cell phone"
        if res['label'] == 'cell phone' and res['score'] > 0.5:
            found_phone = True
            break
    
    if found_phone:
        st.error("🚨 ALARM: HANDY ERKANNT! Leg es sofort weg!")
        st.audio("https://www.soundjay.com/buttons/beep-01a.mp3") # Optionaler Beep
    else:
        st.info("✅ Kein Handy im Bild. Sauber!")
