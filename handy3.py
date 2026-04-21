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

# --- INITIALISIERUNG ---
if "active" not in st.session_state:
    st.session_state.active = False
if "remaining_sec" not in st.session_state:
    st.session_state.remaining_sec = 25 * 60
if "mode" not in st.session_state:
    st.session_state.mode = "Pomodoro"
if "last_tick" not in st.session_state:
    st.session_state.last_tick = time.time()
if "cam_key" not in st.session_state:
    st.session_state.cam_key = 0

st.set_page_config(page_title="Pomofocus AI", layout="centered")

# --- CSS FÜR LAYOUT UND POSITIONIERUNG ---
st.markdown("""
    <style>
    /* Hintergrund und Text zentrieren */
    .main {
        text-align: center;
    }
    
    /* Buttons wie Pomofocus */
    .stButton>button {
        border-radius: 5px;
        height: 3em;
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    /* Kamera-Bereich ganz nach unten verschieben */
    .fixed-bottom {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: rgba(0, 0, 0, 0.8);
        padding: 10px;
        z-index: 999;
        border-top: 1px solid #333;
    }
    
    /* Verhindert, dass der Inhalt hinter der Kamera verschwindet */
    .content-spacer {
        margin-bottom: 350px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HAUPTINHALT (TIMER) ---
st.title("Pomodoro Wächter")

# Modus-Auswahl
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Pomodoro"):
        st.session_state.mode = "Pomodoro"
        st.session_state.remaining_sec = 25 * 60
        st.session_state.active = False
with col2:
    if st.button("Short Break"):
        st.session_state.mode = "Short Break"
        st.session_state.remaining_sec = 5 * 60
        st.session_state.active = False
with col3:
    if st.button("Long Break"):
        st.session_state.mode = "Long Break"
        st.session_state.remaining_sec = 15 * 60
        st.session_state.active = False

# Timer Logik
if st.session_state.active and st.session_state.remaining_sec > 0:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now

# Große Zeitanzeige
mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<h1 style='text-align: center; font-size: 100px; margin: 20px 0;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)

# Start / Stop
button_label = "STOP" if st.session_state.active else "START"
if st.button(button_label, use_container_width=True):
    st.session_state.active = not st.session_state.active
    st.session_state.last_tick = time.time()

# Platzhalter, damit die Kamera nichts Wichtiges verdeckt
st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)

# --- AUTOMATISIERUNG (JavaScript) ---
if st.session_state.active and st.session_state.mode == "Pomodoro":
    components.html(
        """
        <script>
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
        setInterval(forceClick, 5000);
        </script>
        """,
        height=0,
    )

# --- KAMERA BEREICH AM UNTEREN RAND ---
if st.session_state.mode == "Pomodoro" and st.session_state.active:
    # Wir packen alles in ein div mit der Klasse 'fixed-bottom'
    st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
    
    img_file = st.camera_input("Kamera", key=f"cam_{st.session_state.cam_key}", label_visibility="collapsed")
    
    if img_file:
        img = Image.open(img_file)
        results = detector(img)
        handy_gefunden = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
        
        if handy_gefunden:
            st.error("Handy erkannt")
            st.image(ImageOps.colorize(img.convert("L"), black="red", white="white"), width=200)
        else:
            st.success("Fokus aktiv")
            st.image(img, width=200)
            
        st.session_state.cam_key += 1
        time.sleep(2)
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)

# Rerun für flüssige Uhr
if st.session_state.active:
    time.sleep(0.1)
    st.rerun()
