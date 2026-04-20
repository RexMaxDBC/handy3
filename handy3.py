import streamlit as st
from transformers import pipeline
from PIL import Image, ImageOps
import time

# --- KI MODELL LADEN ---
@st.cache_resource
def load_detector():
    # Wir nutzen DETR (kein YOLO), es ist stabil und erkennt 'cell phone'
    return pipeline("object-detection", model="facebook/detr-resnet-50")

detector = load_detector()

# --- APP SETUP ---
st.set_page_config(page_title="Pomodoro Wächter", layout="centered")
st.title("🍅 Automatischer Fokus-Wächter")

# Session State für den Timer und Status
if "active" not in st.session_state:
    st.session_state.active = False
if "end_time" not in st.session_state:
    st.session_state.end_time = 0

# --- SIDEBAR ---
with st.sidebar:
    st.header("Einstellungen")
    minutes = st.number_input("Fokus-Minuten", min_value=1, value=25)
    if st.button("▶️ Fokus Starten"):
        st.session_state.active = True
        st.session_state.end_time = time.time() + (minutes * 60)
    
    if st.button("⏹️ Pause / Stop"):
        st.session_state.active = False

# --- HAUPT-LOGIK ---
if st.session_state.active:
    remaining = st.session_state.end_time - time.time()
    
    if remaining > 0:
        mins, secs = divmod(int(remaining), 60)
        st.metric("Verbleibende Zeit", f"{mins:02d}:{secs:02d}")
        
        # DER AUTOMATISMUS:
        # st.camera_input ist hier der Clou. 
        # Um es "automatisch" zu machen, nutzen wir eine kurze Anweisung.
        img_file = st.camera_input("Kamera-Wächter aktiv", label_visibility="visible")

        if img_file:
            img = Image.open(img_file)
            
            # KI-Erkennung
            with st.spinner("KI prüft..."):
                results = detector(img)
            
            # Suche nach dem Label 'cell phone'
            handy_gefunden = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
            
            if handy_gefunden:
                st.error("🚨 HANDY ERKANNT! Bitte weglegen!")
                # Visueller Alarm: Wir zeigen das Bild rot eingefärbt
                st.image(ImageOps.colorize(img.convert("L"), black="red", white="white"), caption="Alarm-Zustand!")
            else:
                st.success("✅ Fokus ist sauber. Gut gemacht!")
        
        # Kleiner Trick: Die Seite lädt sich alle 10 Sekunden neu, falls kein Bild gemacht wurde
        # (Optional, aber gut für den Timer-Refresh)
        time.sleep(1)
        if int(remaining) % 10 == 0:
            st.rerun()

    else:
        st.session_state.active = False
        st.balloons()
        st.success("Pause! Du hast es geschafft.")
else:
    st.info("Stelle die Zeit ein und klicke auf Start. Während der Pause ist die KI im Ruhezustand.")
