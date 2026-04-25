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

# NEU: Struktur für mehrere Fächer
if "tasks" not in st.session_state:
    st.session_state.tasks = {} # Format: {"Physik": [erledigt, ziel]}
if "selected_task" not in st.session_state:
    st.session_state.selected_task = None

st.set_page_config(page_title="Pomodoro Wächter", layout="centered")

# --- CSS (OPTIMIERTES LAYOUT) ---
st.markdown(f"""
<style>
    .stApp {{
        background-color: {st.session_state.bg_color};
        transition: background-color 0.3s ease;
    }}
    
    .block-container {{
        padding-top: 3rem !important;
    }}

    .header-container {{
        border: 2px solid #D3D3D3;
        border-radius: 12px;
        background-color: rgba(211, 211, 211, 0.15);
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 0 auto 30px auto;
        padding: 10px;
        width: fit-content;
        min-width: 300px;
    }}

    .title-text {{
        color: white !important;
        font-weight: bold !important;
        font-size: 2rem !important;
        margin: 0 !important;
    }}

    /* Task Card */
    .task-card {{
        background: rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid white;
        margin-bottom: 20px;
        color: white;
    }}

    .timer-text {{
        text-align: center; 
        font-size: 110px; 
        color: white; 
        font-weight: bold;
        line-height: 1;
        margin: 20px 0;
    }}

    /* Buttons */
    div.stButton > button {{
        border-radius: 8px;
        font-weight: bold;
    }}
    
    div.stButton > button:last-child {{
        background-color: white !important;
        color: {st.session_state.bg_color} !important;
        font-size: 22px !important;
        height: 55px !important;
        width: 180px !important;
        margin: 10px auto !important;
        display: block !important;
        box-shadow: 0px 5px 0px rgba(0,0,0,0.2);
    }}

    .fixed-bottom {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: rgba(255, 255, 255, 0.95);
        padding: 15px;
        z-index: 1000;
    }}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<div class='header-container'><h1 class='title-text'>Pomodoro Wächter</h1></div>", unsafe_allow_html=True)

# --- TASK MANAGEMENT ---
with st.expander("➕ Neues Fach hinzufügen / Verwalten", expanded=not st.session_state.tasks):
    c1, c2, c3 = st.columns([2, 1, 1])
    new_subject = c1.text_input("Fachname", placeholder="z.B. Physik")
    new_target = c2.number_input("Ziel (Pomodoros)", min_value=1, value=4)
    if c3.button("Hinzufügen", use_container_width=True):
        if new_subject:
            st.session_state.tasks[new_subject] = [0, new_target]
            st.rerun()

# --- TASK AUSWAHL & ANZEIGE ---
if st.session_state.tasks:
    st.session_state.selected_task = st.selectbox(
        "Aktuelles Lernprojekt wählen:", 
        options=list(st.session_state.tasks.keys()),
        index=0 if st.session_state.selected_task is None else list(st.session_state.tasks.keys()).index(st.session_state.selected_task)
    )
    
    current_task = st.session_state.selected_task
    done, target = st.session_state.tasks[current_task]
    
    st.markdown(f"""
        <div class='task-card'>
            <small>AKTIVES PROJEKT</small><br>
            <b style='font-size: 1.5rem;'>{current_task}</b><br>
            Fortschritt: {done} von {target} Einheiten erledigt
        </div>
    """, unsafe_allow_html=True)

# --- MODUS ---
m_col1, m_col2, m_col3 = st.columns([1, 1, 1])
with m_col1:
    if st.button("Pomodoro", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Pomodoro", 25*60, "#2d5a27"
with m_col2:
    if st.button("Kurze Pause", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Short Break", 5*60, "#457b9d"
with m_col3:
    if st.button("Lange Pause", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Long Break", 15*60, "#457b9d"

# --- TIMER LOGIK ---
if st.session_state.active:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now

    if st.session_state.remaining_sec <= 0:
        st.session_state.active = False
        st.session_state.remaining_sec = 0
        if st.session_state.mode == "Pomodoro" and st.session_state.selected_task:
            st.session_state.tasks[st.session_state.selected_task][0] += 1
            st.balloons()
        st.rerun()

# Anzeige
mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

_, btn_center, _ = st.columns([0.5, 1, 0.5])
with btn_center:
    if st.button("STOP" if st.session_state.active else "START", use_container_width=True):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()

# --- KI & KAMERA ---
if st.session_state.active and st.session_state.mode == "Pomodoro":
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
            st.image(img if not handy else ImageOps.colorize(img.convert("L"), "red", "white"), width=120)
            st.session_state.cam_key += 1
            time.sleep(0.5)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.active:
    time.sleep(0.1)
    st.rerun()
