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

# Task-Struktur
if "tasks" not in st.session_state:
    st.session_state.tasks = {} # {"Name": {"done": 0, "target": 4}}
if "selected_task" not in st.session_state:
    st.session_state.selected_task = None

st.set_page_config(page_title="Pomodoro Wächter", layout="centered")

# --- CSS (DESIGN OPTIMIERUNG) ---
st.markdown(f"""
<style>
    .stApp {{
        background-color: {st.session_state.bg_color};
        transition: background-color 0.3s ease;
    }}
    
    .block-container {{
        padding-top: 4rem !important;
    }}

    /* Header bleibt wie gewünscht */
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
        height: 80px;
    }}

    .title-text {{
        color: white !important;
        font-weight: bold !important;
        font-size: 2.2rem !important;
        margin: 0 !important;
        line-height: 80px !important;
    }}

    /* NEUES TASK DESIGN */
    .task-list-container {{
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        margin-top: 30px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}

    .active-task-box {{
        background: rgba(255, 255, 255, 0.2);
        border: 2px solid #D3D3D3;
        box-shadow: 0 0 15px rgba(211, 211, 211, 0.3);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        color: white;
    }}

    .inactive-task-box {{
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        color: rgba(255, 255, 255, 0.7);
    }}

    .progress-bar-bg {{
        background: rgba(0,0,0,0.2);
        border-radius: 5px;
        height: 8px;
        width: 100%;
        margin-top: 8px;
    }}

    .progress-bar-fill {{
        background: #D3D3D3;
        height: 100%;
        border-radius: 5px;
        transition: width 0.5s ease;
    }}

    /* Alte Elemente (Timer & Start/Stop) */
    .timer-text {{
        text-align: center; 
        font-size: 120px; 
        color: white; 
        font-weight: bold;
        margin: 10px 0;
    }}

    div.stButton > button:last-child {{
        background-color: white !important;
        color: {st.session_state.bg_color} !important;
        font-size: 24px !important;
        height: 60px !important;
        width: 200px !important;
        margin: 20px auto !important;
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
st.markdown("<div class='header-wrapper'><div class='header-container'><h1 class='title-text'>Pomodoro Wächter</h1></div></div>", unsafe_allow_html=True)

# --- MODUS (ALTE ELEMENTE UNVERÄNDERT) ---
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
            st.session_state.tasks[st.session_state.selected_task]["done"] += 1
            st.balloons()
        st.rerun()

mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

_, btn_center, _ = st.columns([0.5, 1, 0.5])
with btn_center:
    if st.button("STOP" if st.session_state.active else "START", use_container_width=True):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()

# --- NEUE ELEMENTE: TASK DASHBOARD ---
st.markdown("<hr style='opacity: 0.1'>", unsafe_allow_html=True)

# Fach hinzufügen (Kompakt)
with st.expander("📝 Neues Lern-Fach anlegen"):
    c1, c2, c3 = st.columns([2, 1, 1])
    name = c1.text_input("Name des Fachs", key="add_name")
    target = c2.number_input("Ziel-Einheiten", min_value=1, value=4, key="add_target")
    if c3.button("Speichern", use_container_width=True):
        if name:
            st.session_state.tasks[name] = {"done": 0, "target": target}
            if st.session_state.selected_task is None:
                st.session_state.selected_task = name
            st.rerun()

# Die Task Liste
if st.session_state.tasks:
    st.markdown("### Deine Lernziele")
    for t_name, t_data in st.session_state.tasks.items():
        is_active = (st.session_state.selected_task == t_name)
        css_class = "active-task-box" if is_active else "inactive-task-box"
        
        # Fortschrittsberechnung
        percent = min(100, (t_data["done"] / t_data["target"]) * 100)
        
        # HTML Card
        st.markdown(f"""
            <div class='{css_class}'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <b>{t_name} {' (Aktiv)' if is_active else ''}</b>
                    <span>{t_data["done"]} / {t_data["target"]} Einheiten</span>
                </div>
                <div class='progress-bar-bg'>
                    <div class='progress-bar-fill' style='width: {percent}%'></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Button zum Wechseln (nur wenn nicht aktiv)
        if not is_active:
            if st.button(f"Zu {t_name} wechseln", key=f"switch_{t_name}", size="small"):
                st.session_state.selected_task = t_name
                st.rerun()
        elif is_active:
             if st.button(f"Fach {t_name} entfernen", key=f"del_{t_name}", size="small"):
                 del st.session_state.tasks[t_name]
                 st.session_state.selected_task = next(iter(st.session_state.tasks)) if st.session_state.tasks else None
                 st.rerun()

# --- KI & KAMERA (UNVERÄNDERT) ---
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
