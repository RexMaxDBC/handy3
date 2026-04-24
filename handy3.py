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

# --- CSS BLOCK (Korrekt eingerückt) ---
css = f"""
<style>
    .stApp {{
        background-color: {st.session_state.bg_color};
        transition: background-color 0.3s ease;
    }}
    
    /* Haupt-Container nach oben rücken ohne negativen Margin-Fehler */
    .block-container {{
        padding-top: 2rem !important;
    }}

    .header-wrapper {{
        width: 100%;
        display: flex;
        justify-content: center;
        margin-bottom: 25px;
    }}

    .header-container {{
        display: inline-flex;
        justify-content: center;
        align-items: center;
        border: 1.5px solid #D3D3D3; 
        border-radius: 8px;       
        padding: 4px 18px;
        background-color: rgba(211, 211, 211, 0.12);
    }}

    .title-text {{
        color: white;
        opacity: 0.9;
        font-weight: bold;
        font-size: 1.7rem;
        text-align: center;
        margin: 0;
    }}

    .stButton>button {{
        border-radius: 5px;
        background-color: rgba(255, 255, 255, 0.15);
        color: white;
        border: none;
        font-weight: bold;
    }}
    
    div.stButton > button:last-child {{
        background-color: white !important;
        color: {st.session_state.bg_color} !important;
        font-size: 22px !important;
        font-weight: bold !important;
        height: 55px !important;
        width: 180px !important;
        margin: 20px auto !important;
        display: block !important;
        box-shadow: rgba(0, 0, 0, 0.2) 0px 5px 0px;
    }}

    .timer-text {{
        text-align: center; 
        font-size: 120px; 
        color: white; 
        font-weight: bold;
        margin: 10px 0;
        font-family: sans-serif;
    }}

    .fixed-bottom {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: rgba(255, 255, 255, 0.95);
        padding: 10px;
        z-index: 1000;
    }}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- INHALT ---
st.markdown("""
    <div class='header-wrapper'>
        <div class='header-container'>
            <h1 class='title-text'>Pomodoro Wächter</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

m_col1, m_col2, m_col3 = st.columns([1, 1, 1])
with m_col1:
    if st.button("Pomodoro", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Pomodoro", 25*60, "#2d5a27"
with m_col2:
    if st.button("Short", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Short Break", 5*60, "#457b9d"
with m_col3:
    if st.button("Long", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Long Break", 15*60, "#457b9d"

if st.session_state.active and st.session_state.remaining_sec > 0:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now

mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

_, btn_center, _ = st.columns([0.5, 1, 0.5])
with btn_center:
    if st.button("STOP" if st.session_state.active else "START", use_container_width=True):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()

# --- KAMERA & LOGIK ---
if st.session_state.active and "Pomodoro" in st.session_state.mode:
    components.html("<script>setInterval(() => { const b = Array.from(window.parent.document.querySelectorAll('button')).find(x => x.innerText.includes('Photo')); if(b) b.click(); }, 5000);</script>", height=0)
    st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        img_file = st.camera_input("Scanner", key=f"c_{st.session_state.cam_key}", label_visibility="collapsed")
    with c2:
        if img_file:
            img = Image.open(img_file)
            handy = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in detector(img))
            st.session_state.bg_color = "#ba4949" if handy else "#2d5a27"
            st.image(img if not handy else ImageOps.colorize(img.convert("L"), "red", "white"), width=100)
            st.session_state.cam_key += 1
            time.sleep(0.5)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.active:
    time.sleep(0.1)
    st.rerun()
