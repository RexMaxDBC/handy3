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

st.set_page_config(page_title="Pomodoro AI Station", layout="centered")
st.title("Pomodoro AI Station")

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
    mode = st.radio("Kategorie:", ["Pomodoro (25 Min)", "Kurze Pause (5 Min)", "Lange Pause (15 Min)"])
    
    if st.button("Timer auf gewählten Modus zurücksetzen"):
        if "Pomodoro" in mode: st.session_state.remaining_sec = 25 * 60
        elif "Kurze" in mode: st.session_state.remaining_sec = 5 * 60
        else: st.session_state.remaining_sec = 15 * 60
        st.session_state.running = False

    st.divider()
    st.header("Steuerung")
    
    if not st.session_state.running:
        if st.button("Start / Fortsetzen"):
            st.session_state.running = True
            st.session_state.last_tick = time.time()
    else:
        if st.button("Pause"):
            st.session_state.running = False

# --- TIMER LOGIK ---
if st.session_state.running and st.session_state.remaining_sec > 0:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now

# --- ANZEIGE ---
mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.metric(label=f"Modus: {mode}", value=f"{mins:02d}:{secs:02d}")

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
        setTimeout(autoSnap, 4000); 
        </script>
        """,
        height=0,
    )

# --- KI & KAMERA ---
if "Pomodoro" in mode and st.session_state.running:
    if st.session_state.remaining_sec > 0:
        img_file = st.camera_input("Handy-Check aktiv", key=f"cam_{st.session_state.cam_key}")

        if img_file:
            img = Image.open(img_file)
            results = detector(img)
            handy = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
            
            if handy:
                st.error("Handy erkannt! Bitte weglegen.")
                st.image(ImageOps.colorize(img.convert("L"), black="red", white="white"))
            
            st.session_state.cam_key += 1
            time.sleep(2)
            st.rerun()
    else:
        st.session_state.running = False
        st.success("Arbeitsphase beendet.")
elif not "Pomodoro" in mode and st.session_state.running:
    st.info("Pausen-Modus: Kamera-Überwachung deaktiviert.")
    if st.session_state.remaining_sec <= 0:
        st.session_state.running = False
        st.success("Pause beendet.")

if st.session_state.running:
    time.sleep(0.1)
    st.rerun()
