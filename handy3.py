import streamlit as st
from transformers import pipeline
from PIL import Image, ImageOps
import time
import os
import base64
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

if "tasks" not in st.session_state:
    st.session_state.tasks = {} 
if "selected_task" not in st.session_state:
    st.session_state.selected_task = None

st.set_page_config(page_title="Pomodoro Wächter", layout="centered")

# --- SOUND FUNKTIONEN ---
def play_alarm():
    """Spielt den Star Wars Alarm ab."""
    if os.path.exists("batle-alarm-star-wars.mp3"):
        with open("batle-alarm-star-wars.mp3", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""
                <audio id="alarm_sound" autoplay loop>
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """
            st.markdown(md, unsafe_allow_html=True)

def stop_alarm():
    """Stoppt das Audio-Element im Browser."""
    stop_js = """
        <script>
        var audio = window.parent.document.getElementById("alarm_sound");
        if (audio) {
            audio.pause();
            audio.currentTime = 0;
            audio.remove();
        }
        </script>
        """
    components.html(stop_js, height=0)

# --- CSS DESIGN ---
st.markdown(f"""
<style>
    .stApp {{
        background-color: {st.session_state.bg_color};
        transition: background-color 0.3s ease;
    }}
    
    .block-container {{
        padding-top: 5rem !important;
    }}

    .header-container {{
        border: 2px solid #D3D3D3;
        border-radius: 12px;
        background-color: rgba(211, 211, 211, 0.15);
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 0 auto 40px auto;
        padding: 0 40px;
        min-width: 320px;
        height: 85px;
    }}

    .title-text {{
        color: white !important;
        font-weight: bold !important;
        font-size: 2.2rem !important;
        margin: 0 !important;
    }}

    .timer-text {{
        text-align: center; 
        font-size: 120px; 
        color: white; 
        font-weight: bold;
        margin: 10px 0;
    }}

    .fixed-bottom {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: white;
        padding: 15px;
        z-index: 1000;
        border-top: 1px solid #ddd;
    }}
</style>
""", unsafe_allow_html=True)

# --- UI ELEMENTE ---
st.markdown("<div class='header-container'><h1 class='title-text'>Pomodoro Wächter</h1></div>", unsafe_allow_html=True)

# MODUS AUSWAHL
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    if st.button("Pomodoro", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Pomodoro", 25*60, "#2d5a27"
        st.session_state.active = False
with m_col2:
    if st.button("Kurze Pause", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Pause", 5*60, "#457b9d"
        st.session_state.active = False
with m_col3:
    if st.button("Lange Pause", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Lange Pause", 15*60, "#457b9d"
        st.session_state.active = False

# TIMER LOGIK
if st.session_state.active:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now
    if st.session_state.remaining_sec <= 0:
        st.session_state.active = False
        st.balloons()
        st.rerun()

mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

_, btn_center, _ = st.columns([0.5, 1, 0.5])
with btn_center:
    if st.button("STOP" if st.session_state.active else "START", use_container_width=True):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()
        if not st.session_state.active:
            stop_alarm() # Sofort stoppen, wenn User manuell Pause drückt
        st.rerun()

# --- KI & KAMERA (DETR MODELL + SOUND) ---
if st.session_state.active and st.session_state.mode == "Pomodoro":
    # Automatischer Foto-Trigger alle 5 Sekunden
    components.html("<script>if(!window.parent.pI) window.parent.pI = setInterval(() => { const b = Array.from(window.parent.document.querySelectorAll('button')).find(x => x.innerText.includes('Photo')); if(b) b.click(); }, 5000);</script>", height=0)
    
    st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        img_file = st.camera_input("Scanner", key=f"c_{st.session_state.cam_key}", label_visibility="collapsed")
    with c2:
        if img_file:
            img = Image.open(img_file)
            # DETR Suche nach 'cell phone'
            results = detector(img)
            handy = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
            
            if handy:
                st.session_state.bg_color = "#ba4949" # Rot
                st.error("HANDY ERKANNT!")
                play_alarm() # Sound an
            else:
                st.session_state.bg_color = "#2d5a27" # Grün
                st.success("FOKUS OK")
                stop_alarm() # Sound aus
            
            st.session_state.cam_key += 1
            time.sleep(0.5)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Laufendes Update für den Timer
if st.session_state.active:
    time.sleep(0.1)
    st.rerun()
