import streamlit as st
from transformers import pipeline
from PIL import Image
import time

# --- KI SETUP (DETR Modell - Kein YOLO) ---
@st.cache_resource
def load_detector():
    return pipeline("object-detection", model="facebook/detr-resnet-50")

detector = load_detector()

# --- INITIALISIERUNG ---
if "run" not in st.session_state:
    st.session_state.run = False
if "end_time" not in st.session_state:
    st.session_state.end_time = 0

st.set_page_config(page_title="Pomodoro Wächter", page_icon="🍅")
st.title("🍅 Simpler Pomodoro Wächter")

# --- SIDEBAR (Einstellungen) ---
with st.sidebar:
    st.header("Einstellungen")
    duration = st.slider("Fokus-Dauer (Minuten)", 1, 60, 25)
    
    col1, col2 = st.columns(2)
    if col1.button("▶️ Start"):
        st.session_state.run = True
        st.session_state.end_time = time.time() + (duration * 60)
        
    if col2.button("⏹️ Stop/Pause"):
        st.session_state.run = False

# --- HAUPTTEIL ---
if st.session_state.run:
    remaining = st.session_state.end_time - time.time()
    
    if remaining > 0:
        mins, secs = divmod(int(remaining), 60)
        st.subheader(f"⏳ Verbleibende Zeit: {mins:02d}:{secs:02d}")
        
        # Kamera-Input
        # Hinweis: In dieser simplen Version musst du das Foto kurz bestätigen.
        # Das spart extrem viel Rechenleistung und verhindert das Aufhängen.
        img_file = st.camera_input("Handy-Check (Bitte kurz lächeln)")

        if img_file:
            img = Image.open(img_file)
            with st.spinner("KI scannt..."):
                predictions = detector(img)
                
            found_phone = any(res['label'] == 'cell phone' and res['score'] > 0.5 for res in predictions)
            
            if found_phone:
                st.error("🚨 HANDY GEFUNDEN! Leg es sofort weg!")
                st.audio("https://www.soundjay.com/buttons/beep-01a.mp3")
            else:
                st.success("✅ Alles super, kein Handy zu sehen. Weiterarbeiten!")
    else:
        st.session_state.run = False
        st.balloons()
        st.success("🎉 Zeit abgelaufen! Du hast jetzt Pause.")
else:
    st.info("Stelle die Zeit ein und drücke auf Start. Während der Pause findet kein Check statt.")

# --- INFO FÜR DAS PROJEKT ---
with st.expander("Wie funktioniert das?"):
    st.write("""
    - **KI-Modell:** DETR (Detection Transformer) von Facebook.
    - **Vorteil:** Es braucht keine Grafiktreiber (libGL) und ist kein YOLO.
    - **Logik:** Der Handy-Check wird nur ausgeführt, wenn der Timer aktiv ist.
    """)
