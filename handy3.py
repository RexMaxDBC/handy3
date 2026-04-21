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
if "alarm" not in st.session_state:
    st.session_state.alarm = False

st.set_page_config(page_title="Pomodoro AI Station", layout="centered")

# --- DYNAMISCHES CSS (Hintergrundfarbe und Unsichtbarkeit) ---
# Wenn Alarm aktiv ist, wird der Hintergrund leuchtend rot
bg_color = "#FF0000" if st.session_state.alarm else "#ba4949"

st.markdown(f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        transition: background-color 0.5s ease;
    }}
    /* Versteckt die Kamera-Vorschau und den Button komplett */
    div[data-testid="stCameraInput"] {{
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0,0,0,0);
        border: 0;
    }}
    .stButton>button {{
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: rgba(255, 255, 255, 0.2);
        color: white;
        border: none;
    }}
    h1, h2, h3, p, span {{
        color: white !important;
    }}
    </style>
    """, unsafe_allow_html=True)

st.title("Pomodoro Wächter")

# --- MODUS NAVIGATION ---
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Pomodoro"):
        st.session_state.mode = "Pomodoro"
        st.session_state.remaining_sec = 25 * 60
        st.session_state.active = False
        st.session_state.alarm = False
with col2:
    if st.button("Short Break"):
        st.session_state.mode = "Short Break"
        st.session_state.remaining_sec = 5 * 60
        st.session_state.active = False
        st.session_state.alarm = False
with col3:
    if st.button("Long Break"):
        st.session_state.mode = "Long Break"
        st.session_state.remaining_sec = 15 * 60
        st.session_state.active = False
        st.session_state.alarm = False

# --- TIMER LOGIK ---
if st.session_state.active and st.session_state.remaining_sec > 0:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now

# --- TIMER ANZEIGE ---
mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<h1 style='text-align: center; font-size: 100px;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)

# --- START / PAUSE BUTTON ---
button_label = "STOP" if st.session_state.active else "START"
if st.button(button_label, use_container_width=True):
    st.session_state.active = not st.session_state.active
    st.session_state.last_tick = time.time()
    if not st.session_state.active:
        st.session_state.alarm = False

# --- AUTOMATISIERUNG (Unsichtbarer Clicker) ---
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
        setTimeout(forceClick, 4000); 
        </script>
        """,
        height=0,
    )

# --- VERSTECKTER KAMERA-BEREICH ---
if st.session_state.mode == "Pomodoro" and st.session_state.active:
    if st.session_state.remaining_sec > 0:
        # Widget ist durch CSS versteckt, aber funktional
        img_file = st.camera_input("versteckt", key=f"cam_{st.session_state.cam_key}")
        
        if img_file:
            img = Image.open(img_file)
            results = detector(img)
            
            handy_gefunden = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
            
            if handy_gefunden:
                st.session_state.alarm = True
            else:
                st.session_state.alarm = False
            
            st.session_state.cam_key += 1
            st.rerun()
    else:
        st.session_state.active = False
        st.session_state.alarm = False
        st.balloons()
