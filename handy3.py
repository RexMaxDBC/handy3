import streamlit as st
from transformers import pipeline
from PIL import Image, ImageOps
import time
import streamlit.components.v1 as components

# --- KI SETUP ---
@st.cache_resource
def load_detector():
    return pipeline("object-detection", model="facebook/detr-resnet-50")

detector = load_detector()

st.set_page_config(page_title="Pro Pomodoro AI", layout="centered")
st.title("🍅 AI Pomodoro Station")

# --- SESSION STATE INITIALISIERUNG ---
if "running" not in st.session_state:
    st.session_state.running = False
if "remaining_sec" not in st.session_state:
    st.session_state.remaining_sec = 25 * 60
if "last_tick" not in st.session_state:
    st.session_state.last_tick = time.time()
if "cam_key" not in st.session_state:
    st.session_state.cam_key = 0

# --- SIDEBAR: KATEGORIEN & STEUERUNG ---
with st.sidebar:
    st.header("Modus wählen")
    # Timer-Optionen
    mode = st.radio("Kategorie:", ["Pomodoro (25m)", "Short Break (5m)", "Long Break (15m)"])
    
    if st.button("Timer auf Modus zurücksetzen"):
        if "Pomodoro" in mode: st.session_state.remaining_sec = 25 * 60
        elif "Short" in mode: st.session_state.remaining_sec = 5 * 60
        else: st.session_state.remaining_sec = 15 * 60
        st.session_state.running = False

    st.divider()
    st.header("Steuerung")
    
    if not st.session_state.running:
        if st.button("▶️ Start / Fortsetzen"):
            st.session_state.running = True
            st.session_state.last_tick = time.time()
    else:
        if st.button("⏸️ Pause"):
            st.session_state.running = False

# --- TIMER LOGIK (Die "Uhr") ---
if st.session_state.running and st.session_state.remaining_sec > 0:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now

# --- ANZEIGE ---
mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.metric(label=f"Aktueller Modus: {mode}", value=f"{mins:02d}:{secs:02d}")

# --- AUTOMATISIERUNG (JavaScript für Auto-Snap) ---
if st.session_state.running and "Pomodoro" in mode:
    components.html(
        """
        <script>
        function autoSnap() {
            const root = window.parent.document;
            const buttons = Array.from(root.querySelectorAll("button"));
            const takeBtn = buttons.find(btn => 
                btn.innerText.includes("Photo") || 
                btn.innerText.includes("aufnehmen") ||
                btn.getAttribute("aria-label") === "Take Photo"
            );
            if (takeBtn) takeBtn.click();
        }
        setTimeout(autoSnap, 4000); // Alle 4 Sekunden ein Foto
        </script>
        """,
        height=0,
    )

# --- KI & KAMERA (Nur im Pomodoro-Modus aktiv) ---
if "Pomodoro" in mode and st.session_state.running:
    if st.session_state.remaining_sec > 0:
        img_file = st.camera_input("Handy-Check", key=f"cam_{st.session_state.cam_key}")

        if img_file:
            img = Image.open(img_file)
            results = detector(img)
            handy = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
            
            if handy:
                st.error("🚨 HANDY ERKANNT! Zurück an die Arbeit!")
                st.image(ImageOps.colorize(img.convert("L"), black="red", white="white"))
            
            # Reset für das nächste Foto vorbereiten
            st.session_state.cam_key += 1
            time.sleep(2)
            st.rerun()
    else:
        st.session_state.running = False
        st.balloons()
        st.success("Arbeitsphase beendet! Zeit für eine Pause.")
elif not "Pomodoro" in mode and st.session_state.running:
    st.info("Pausen-Modus: Die Kamera-Überwachung ist deaktiviert. Entspann dich!")
    if st.session_state.remaining_sec <= 0:
        st.session_state.running = False
        st.balloons()
        st.success("Pause vorbei! Bereit für die nächste Runde?")

# Kontinuierliches Update der UI (wichtig für die Sekunden-Anzeige)
if st.session_state.running:
    time.sleep(0.1)
    st.rerun()
