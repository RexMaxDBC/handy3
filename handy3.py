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

st.set_page_config(page_title="Pomodoro Wächter", layout="centered")

# --- CSS FÜR LAYOUT ---
st.markdown("""
    <style>
    .main { text-align: center; }
    .stButton>button {
        border-radius: 5px;
        height: 3em;
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    /* Kamera-Bereich fest am unteren Rand */
    .fixed-bottom {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #0e1117;
        padding: 10px;
        z-index: 1000;
        border-top: 1px solid #333;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .spacer { margin-bottom: 400px; }
    </style>
    """, unsafe_allow_html=True)

# --- HAUPTBEREICH (Wird immer angezeigt) ---
st.title("Pomodoro Wächter")

# 1. Modus-Buttons
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    if st.button("Pomodoro"):
        st.session_state.mode = "Pomodoro"
        st.session_state.remaining_sec = 25 * 60
        st.session_state.active = False
with m_col2:
    if st.button("Short Break"):
        st.session_state.mode = "Short Break"
        st.session_state.remaining_sec = 5 * 60
        st.session_state.active = False
with m_col3:
    if st.button("Long Break"):
        st.session_state.mode = "Long Break"
        st.session_state.remaining_sec = 15 * 60
        st.session_state.active = False

# Timer Logik
if st.session_state.active and st.session_state.remaining_sec > 0:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now

# 2. Große Zeitanzeige
mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<h1 style='text-align: center; font-size: 80px;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)
st.write(f"Modus: {st.session_state.mode}")

# 3. Start / Stop Button
button_label = "STOP" if st.session_state.active else "START"
if st.button(button_label, use_container_width=True):
    st.session_state.active = not st.session_state.active
    st.session_state.last_tick = time.time()

# Platzhalter damit nichts verdeckt wird
st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

# --- AUTOMATISIERUNG ---
if st.session_state.active and st.session_state.mode == "Pomodoro":
    components.html(
        """
        <script>
        function autoClick() {
            const root = window.parent.document;
            const buttons = Array.from(root.querySelectorAll("button"));
            const takeBtn = buttons.find(btn =>
                btn.innerText.includes("Photo") ||
                btn.innerText.includes("aufnehmen") ||
                btn.getAttribute("aria-label") === "Take Photo"
            );
            if (takeBtn) takeBtn.click();
        }
        setInterval(autoClick, 5000);
        </script>
        """,
        height=0,
    )

# --- KAMERA BEREICH (Am unteren Rand) ---
if st.session_state.mode == "Pomodoro" and st.session_state.active:
    st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
    
    # Kamera Input
    img_file = st.camera_input("Kamera", key=f"cam_{st.session_state.cam_key}", label_visibility="collapsed")
    
    if img_file:
        img = Image.open(img_file)
        results = detector(img)
        handy = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
        
        if handy:
            st.error("Handy erkannt")
            st.image(ImageOps.colorize(img.convert("L"), black="red", white="white"), width=150)
        else:
            st.success("Fokus aktiv")
            
        st.session_state.cam_key += 1
        time.sleep(1)
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)

# Rerun für die Uhrzeit
if st.session_state.active:
    time.sleep(0.1)
    st.rerun()
