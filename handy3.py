import streamlit as st
from transformers import pipeline
from PIL import Image
import time

# --- SETUP ---
st.set_page_config(page_title="Safe Pomodoro", page_icon="🍅")

# Modell laden - Wir nutzen DETR, weil es KEIN YOLO ist und KEIN OpenCV braucht
@st.cache_resource
def load_detector():
    # Wir laden den Object-Detector explizit
    return pipeline("object-detection", model="facebook/detr-resnet-50")

# --- APP START ---
st.title("🍅 KI Pomodoro (No-CV2 / No-YOLO)")

# Session State initialisieren
if "start_time" not in st.session_state:
    st.session_state.start_time = None

# Sidebar für die Steuerung
with st.sidebar:
    st.header("Timer-Einstellungen")
    focus_m = st.slider("Fokus-Zeit (Minuten)", 1, 60, 25)
    if st.button("Timer Start/Reset"):
        st.session_state.start_time = time.time()

# Logik
if st.session_state.start_time:
    elapsed = time.time() - st.session_state.start_time
    focus_sec = focus_m * 60
    
    if elapsed < focus_sec:
        remaining = int(focus_sec - elapsed)
        mins, secs = divmod(remaining, 60)
        st.metric("Fokus-Zeit übrig", f"{mins:02d}:{secs:02d}")
        
        # Kamera-Input (Streamlit nativ)
        img_file = st.camera_input("Scanner")
        
        if img_file:
            img = Image.open(img_file)
            detector = load_detector()
            predictions = detector(img)
            
            phone_found = any(res['label'] == 'cell phone' and res['score'] > 0.5 for res in predictions)
            
            if phone_found:
                st.error("🚨 HANDY ERKANNT! Zurück an die Arbeit!")
            else:
                st.success("✅ Alles gut! Kein Handy im Fokus.")
    else:
        st.balloons()
        st.success("☕ PAUSE! Der Handy-Check ist jetzt deaktiviert.")
        st.info("Du kannst jetzt dein Handy benutzen, bis du den Timer neu startest.")
else:
    st.info("Klicke auf 'Start' in der Sidebar, um die Fokus-Phase zu beginnen.")
