import streamlit as st
from transformers import pipeline
from PIL import Image, ImageOps
import time
import streamlit.components.v1 as components

# --- KI SETUP ---
@st.cache_resource
def load_detector():
    # Wir nehmen DETR - es ist kein YOLO und braucht kein OpenCV/libGL
    return pipeline("object-detection", model="facebook/detr-resnet-50")

detector = load_detector()

st.set_page_config(page_title="Auto-Snap Pomodoro", layout="centered")
st.title("🍅 Automatischer Pomodoro-Wächter")

# --- SESSION STATE ---
if "active" not in st.session_state:
    st.session_state.active = False

with st.sidebar:
    st.header("Steuerung")
    if st.button("▶️ Fokus-Phase Starten"):
        st.session_state.active = True
    if st.button("⏹️ Stop"):
        st.session_state.active = False

# --- DER AUTO-CLICKER HACK (JavaScript) ---
# Dieses Skript sucht den "Take Photo" Button und klickt ihn alle 3 Sekunden
if st.session_state.active:
    components.html(
        """
        <script>
        function clickPhoto() {
            // Suche alle Buttons auf der Seite
            const buttons = window.parent.document.querySelectorAll("button");
            for (const btn of buttons) {
                // Wenn der Button den Text für das Foto enthält (Streamlit Standard)
                if (btn.innerText === "Take Photo" || btn.innerText === "Foto aufnehmen") {
                    btn.click();
                }
            }
        }
        // Alle 3000ms (3 Sek) klicken
        setInterval(clickPhoto, 3000);
        </script>
        """,
        height=0,
    )

# --- HAUPT-ANZEIGE ---
if st.session_state.active:
    st.warning("Automatischer Scan läuft alle 3 Sekunden...")
    
    # Streamlit Kamera Element
    img_file = st.camera_input("Kamera-Feed")

    if img_file:
        img = Image.open(img_file)
        
        # KI-Erkennung
        with st.spinner("KI scannt Bild..."):
            results = detector(img)
        
        handy_gefunden = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
        
        if handy_gefunden:
            st.error("🚨 ALARM: HANDY ERKANNT!")
            # Bild rot einfärben
            alarm_img = ImageOps.colorize(img.convert("L"), black="red", white="white")
            st.image(alarm_img, caption="Handy-Sperre aktiv!")
        else:
            st.success("✅ Fokus aktiv - Kein Handy zu sehen.")
else:
    st.info("Klicke in der Sidebar auf Start, um den automatischen Scan zu aktivieren.")
