import streamlit as st
from camera_input_live import camera_input_live
from transformers import pipeline
from PIL import Image, ImageOps
import time

# --- KI MODELL (DETR - Kein YOLO!) ---
@st.cache_resource
def load_detector():
    return pipeline("object-detection", model="facebook/detr-resnet-50")

detector = load_detector()

st.set_page_config(page_title="Auto-Fokus Wächter", layout="centered")
st.title("🍅 Automatischer Pomodoro-Check")

# --- TIMER & STATUS ---
if "active" not in st.session_state:
    st.session_state.active = False
if "start_time" not in st.session_state:
    st.session_state.start_time = 0

with st.sidebar:
    st.header("Steuerung")
    minutes = st.number_input("Fokus-Zeit", min_value=1, value=25)
    if st.button("▶️ Start"):
        st.session_state.active = True
        st.session_state.start_time = time.time()
    if st.button("⏹️ Stop"):
        st.session_state.active = False

# --- AUTOMATISCHE KAMERA-LOGIK ---
if st.session_state.active:
    elapsed = time.time() - st.session_state.start_time
    remaining = (minutes * 60) - elapsed
    
    if remaining > 0:
        mins, secs = divmod(int(remaining), 60)
        st.metric("Restzeit", f"{mins:02d}:{secs:02d}")

        # Das hier ist der "Magische" Teil: Es nimmt automatisch Bilder auf!
        image = camera_input_live(show_controls=False)

        if image:
            img = Image.open(image)
            
            # KI-Check (DETR erkennt Handys)
            results = detector(img)
            handy_da = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
            
            if handy_da:
                st.error("🚨 HANDY ERKANNT! Leg es weg!")
                # Optional: Alarm-Farbe anzeigen
                st.image(ImageOps.colorize(img.convert("L"), black="red", white="white"), use_column_width=True)
            else:
                st.success("✅ Fokus aktiv - Kein Handy gefunden.")
                st.image(img, use_column_width=True)
    else:
        st.session_state.active = False
        st.balloons()
        st.success("Zeit um! Genieße deine Pause.")
else:
    st.info("Drücke Start, um die automatische Überwachung zu aktivieren.")
