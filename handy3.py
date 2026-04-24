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
if "bg_color" not in st.session_state:
    st.session_state.bg_color = "#2d5a27" 

st.set_page_config(page_title="Pomodoro Wächter", layout="centered")

# --- CSS FÜR PERFEKTE ZENTRIERUNG ---
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {st.session_state.bg_color};
        transition: background-color 0.3s ease;
    }}
    
    .main-box {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
    }}

    /* Modus Buttons oben */
    .stButton>button {{
        border-radius: 5px;
        background-color: rgba(255, 255, 255, 0.15);
        color: white;
        border: none;
        font-weight: bold;
    }}

    /* Spezifisches Styling für den START/STOP Button */
    div.stButton > button[kind="primary"], 
    div.stButton > button:last-child {{
        background-color: white !important;
        color: {st.session_state.bg_color} !important;
        font-size: 25px !important;
        font-weight: bold !important;
        height: 60px !important;
        width: 200px !important;
        border: none !important;
        box-shadow: rgba(0, 0, 0, 0.2) 0px 6px 0px;
        margin: 0 auto;
        display: block;
    }}
    
    div.stButton > button:active {{
        transform: translateY(4px);
        box-shadow: none;
    }}

    .timer-text {{
        text-align: center; 
        font-size: 120px; 
        color: white; 
        font-weight: bold;
        margin: 20px 0;
        font-family: 'Arial', sans-serif;
    }}

    .fixed-bottom {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: rgba(255, 255, 255, 0.95);
        padding: 10px;
        z-index: 1000;
        box-shadow: 0px -5px 15px rgba(0,0,0,0.2);
    }}
    
    .spacer {{ margin-bottom: 300px; }}
    </style>
    """, unsafe_allow_html=True)

# --- HAUPTBEREICH ---
st.markdown("<h2 style='text-align: center; color: white; opacity: 0.8;'>Pomodoro Wächter</h2>", unsafe_allow_html=True)

# 1. Modus-Buttons mittig
m_col1, m_col2, m_col3 = st.columns([1, 1, 1])
with m_col1:
    if st.button("Pomodoro", use_container_width=True):
        st.session_state.mode = "Pomodoro"
        st.session_state.remaining_sec = 25 * 60
        st.session_state.active = False
        st.session_state.bg_color = "#2d5a27"
with m_col2:
    if st.button("Short", use_container_width=True):
        st.session_state.mode = "Short Break"
        st.session_state.remaining_sec = 5 * 60
        st.session_state.active = False
        st.session_state.bg_color = "#457b9d"
with m_col3:
    if st.button("Long", use_container_width=True):
        st.session_state.mode = "Long Break"
        st.session_state.remaining_sec = 15 * 60
        st.session_state.active = False
        st.session_state.bg_color = "#457b9d"

# Timer Logik
if st.session_state.active and st.session_state.remaining_sec > 0:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now

# 2. Zeitanzeige
mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

# 3. Start / Stop Button PERFEKT MITTIG
# Wir nutzen eine einzelne Spalte in der Mitte für die Zentrierung
_, btn_center, _ = st.columns([1, 1, 1])
with btn_center:
    button_label = "STOP" if st.session_state.active else "START"
    if st.button(button_label, use_container_width=True):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()
        if not st.session_state.active:
             st.session_state.bg_color = "#2d5a27" if "Pomodoro" in st.session_state.mode else "#457b9d"

st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

# --- AUTOMATISIERUNG ---
if st.session_state.active and "Pomodoro" in st.session_state.mode:
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
        setInterval(autoSnap, 5000);
        </script>
        """,
        height=0,
    )

# --- KAMERA BEREICH ---
if "Pomodoro" in st.session_state.mode and st.session_state.active:
    st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        img_file = st.camera_input("Scanner", key=f"cam_{st.session_state.cam_key}", label_visibility="collapsed")
    with c2:
        if img_file:
            img = Image.open(img_file)
            results = detector(img)
            handy = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
            if handy:
                st.session_state.bg_color = "#ba4949"
                st.error("Handy!")
                st.image(ImageOps.colorize(img.convert("L"), black="red", white="white"), width=100)
            else:
                st.session_state.bg_color = "#2d5a27"
                st.image(img, width=100)
            st.session_state.cam_key += 1
            time.sleep(1)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.active:
    time.sleep(0.1)
    st.rerun()
