import streamlit as st
from transformers import pipeline
from PIL import Image, ImageOps
import time

# --- KI SETUP ---
@st.cache_resource
def load_detector():
    return pipeline("object-detection", model="facebook/detr-resnet-50")

detector = load_detector()

st.title("🍅 Automatischer Handy-Wächter")

# Session State initialisieren
if "active" not in st.session_state:
    st.session_state.active = False
if "timer_start" not in st.session_state:
    st.session_state.timer_start = None

# --- SIDEBAR ---
with st.sidebar:
    st.header("Einstellungen")
    minutes = st.number_input("Fokus-Zeit (Min)", min_value=1, value=25)
    if st.button("▶️ Start"):
        st.session_state.active = True
        st.session_state.timer_start = time.time()
    if st.button("⏹️ Stop"):
        st.session_state.active = False

# --- LOGIK ---
if st.session_state.active:
    elapsed = time.time() - st.session_state.timer_start
    remaining = (minutes * 60) - elapsed
    
    if remaining > 0:
        mins, secs = divmod(int(remaining), 60)
        st.subheader(f"⌛ Zeit übrig: {mins:02d}:{secs:02d}")

        # Die Kamera-Komponente
        # Hinweis: Bei dieser Komponente musst du beim ersten Mal auf "Zulassen" klicken.
        # Manche Browser blockieren die Kamera, wenn die Seite nicht über HTTPS läuft.
        img_file = st.camera_input("Scanner läuft...", label_visibility="collapsed")

        if img_file:
            img = Image.open(img_file)
            
            # Analyse
            with st.spinner("Analysiere..."):
                results = detector(img)
            
            phone_found = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
            
            if phone_found:
                st.error("🚨 HANDY GEFUNDEN!")
                # Sofortiges Feedback
                st.image(ImageOps.colorize(img.convert("L"), black="red", white="white"))
            else:
                st.success("✅ Fokus gehalten!")
        
        # Der Trick für "Automatik": 
        # Wir erzwingen alle paar Sekunden einen Rerun, damit das System aktiv bleibt.
        time.sleep(2)
        st.rerun()
        
    else:
        st.session_state.active = False
        st.balloons()
        st.success("Pause!")
else:
    st.info("Bitte auf Start drücken. Falls kein Kamerabild erscheint, prüfe oben in der Adressleiste deines Browsers, ob die Kamera blockiert wird.")
