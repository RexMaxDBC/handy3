import streamlit as st  # <--- Das hat gefehlt!
from transformers import pipeline
from PIL import Image, ImageOps
import time
import streamlit.components.v1 as components

# --- KI SETUP (DETR Modell) ---
@st.cache_resource
def load_detector():
    # Lädt das Modell einmalig in den Cache
    return pipeline("object-detection", model="facebook/detr-resnet-50")

detector = load_detector()

# --- SEITEN-LAYOUT ---
st.set_page_config(page_title="Auto-Snap Pomodoro", layout="centered")
st.title("🍅 Automatischer Pomodoro-Wächter")

# Session State initialisieren
if "active" not in st.session_state:
    st.session_state.active = False
if "timer_start" not in st.session_state:
    st.session_state.timer_start = None

# --- SIDEBAR STEUERUNG ---
with st.sidebar:
    st.header("Steuerung")
    minutes = st.number_input("Fokus-Zeit (Min)", min_value=1, value=25)
    if st.button("▶️ Fokus Starten"):
        st.session_state.active = True
        st.session_state.timer_start = time.time()
    
    if st.button("⏹️ Stop / Pause"):
        st.session_state.active = False

# --- DER AUTO-CLICKER HACK (JavaScript) ---
if st.session_state.active:
    # Dieses Skript drückt erst "Löschen" und dann "Aufnehmen"
    components.html(
        """
        <script>
        function autoStep() {
            const buttons = window.parent.document.querySelectorAll("button");
            
            // 1. Suche den Clear-Button (X oder Text)
            for (const btn of buttons) {
                if (btn.innerText === "Clear photo" || 
                    btn.innerText === "Foto löschen" || 
                    btn.getAttribute("aria-label") === "Clear photo") {
                    btn.click();
                }
            }

            // 2. Kurz warten und dann neu schießen
            setTimeout(() => {
                const newButtons = window.parent.document.querySelectorAll("button");
                for (const btn of newButtons) {
                    if (btn.innerText === "Take Photo" || btn.innerText === "Foto aufnehmen") {
                        btn.click();
                    }
                }
            }, 600); 
        }

        // Alle 5 Sekunden wiederholen (gibt der KI genug Zeit)
        setInterval(autoStep, 5000);
        </script>
        """,
        height=0,
    )

# --- HAUPT-ANZEIGE & KI ---
if st.session_state.active:
    elapsed = time.time() - st.session_state.timer_start
    remaining = (minutes * 60) - elapsed
    
    if remaining > 0:
        mins, secs = divmod(int(remaining), 60)
        st.subheader(f"⌛ Zeit übrig: {mins:02d}:{secs:02d}")

        # Kamera Element
        img_file = st.camera_input("Kamera-Wächter aktiv", label_visibility="collapsed")

        if img_file:
            img = Image.open(img_file)
            
            # KI-Erkennung (DETR)
            with st.spinner("Analysiere..."):
                results = detector(img)
            
            # Prüfen auf Handy
            handy_gefunden = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
            
            if handy_gefunden:
                st.error("🚨 HANDY ERKANNT! Leg es sofort weg!")
                # Visueller Alarm (Rot-Filter)
                st.image(ImageOps.colorize(img.convert("L"), black="red", white="white"), use_column_width=True)
            else:
                st.success("✅ Fokus gehalten! Kein Handy im Bild.")
                st.image(img, use_column_width=True)
    else:
        st.session_state.active = False
        st.balloons()
        st.success("🎉 Zeit abgelaufen! Du hast jetzt Pause.")
else:
    st.info("Klicke in der Sidebar auf Start. Der automatische Scan beginnt dann sofort.")
