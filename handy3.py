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

st.title("Vollautomatischer XXL Pomodoro-Wächter")

# --- SESSION STATE INITIALISIERUNG ---
if "active" not in st.session_state:
    st.session_state.active = False
if "remaining_sec" not in st.session_state:
    st.session_state.remaining_sec = 25 * 60
if "last_tick" not in st.session_state:
    st.session_state.last_tick = time.time()
if "cam_key" not in st.session_state:
    st.session_state.cam_key = 0

# --- SIDEBAR: MODI UND STEUERUNG ---
with st.sidebar:
    st.header("Modus wählen")
    mode = st.radio("Kategorie:", ["Pomodoro (25 Min)", "Kurze Pause (5 Min)", "Lange Pause (15 Min)"])
    
    if st.button("Timer auf gewählten Modus setzen"):
        if "Pomodoro" in mode:
            st.session_state.remaining_sec = 25 * 60
        elif "Kurze" in mode:
            st.session_state.remaining_sec = 5 * 60
        else:
            st.session_state.remaining_sec = 15 * 60
        st.session_state.active = False

    st.divider()
    st.header("Steuerung")
    
    if not st.session_state.active:
        if st.button("Start / Fortsetzen"):
            st.session_state.active = True
            st.session_state.last_tick = time.time()
    else:
        if st.button("Anhalten (Pause)"):
            st.session_state.active = False

# --- TIMER LOGIK ---
if st.session_state.active and st.session_state.remaining_sec > 0:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now

# --- AUTOMATISIERUNG (JavaScript) ---
# Nur im Pomodoro-Modus und wenn der Timer aktiv ist
if st.session_state.active and "Pomodoro" in mode:
    components.html(
        """
        <script>
        const intervalTime = 5000; 
        function forceClick() {
            const root = window.parent.document;
            const buttons = Array.from(root.querySelectorAll("button"));
            const takeBtn = buttons.find(btn =>
                btn.innerText.includes("Photo") ||
                btn.innerText.includes("aufnehmen") ||
                btn.getAttribute("aria-label") === "Take Photo"
            );
            if (takeBtn) {
                takeBtn.focus();
                takeBtn.click();
            }
        }
        setInterval(forceClick, intervalTime);
        </script>
        """,
        height=0,
    )

# --- HAUPT-ANZEIGE ---
mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.subheader(f"Zeit übrig: {mins:02d}:{secs:02d}")
st.write(f"Aktueller Modus: {mode}")

if st.session_state.active:
    if st.session_state.remaining_sec > 0:
        
        # Kamera nur im Pomodoro-Modus anzeigen
        if "Pomodoro" in mode:
            img_file = st.camera_input("Scanner", key=f"cam_{st.session_state.cam_key}")
            
            if img_file:
                img = Image.open(img_file)
                with st.spinner("KI prüft..."):
                    results = detector(img)
                
                handy_gefunden = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
                
                if handy_gefunden:
                    st.error("HANDY ERKANNT!")
                    st.image(ImageOps.colorize(img.convert("L"), black="red", white="white"))
                else:
                    st.success("Fokus aktiv!")
                
                st.session_state.cam_key += 1
                time.sleep(3)
                st.rerun()
        else:
            st.info("Pausenzeit: Kamera-Überwachung ist deaktiviert.")
            time.sleep(1)
            st.rerun()
            
    else:
        st.session_state.active = False
        st.balloons()
        st.success("Zeit abgelaufen.")
else:
    st.info("Timer pausiert oder inaktiv. Klicke auf Start in der Sidebar.")
