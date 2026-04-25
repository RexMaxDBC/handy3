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

# Projekt-Speicher
if "tasks" not in st.session_state:
    st.session_state.tasks = {} 
if "selected_task" not in st.session_state:
    st.session_state.selected_task = "Standard"
    st.session_state.tasks["Standard"] = [0, 4]

st.set_page_config(page_title="Pomodoro Wächter", layout="centered")

# --- OPTIMIERTES CSS ---
st.markdown(f"""
<style>
    .stApp {{
        background-color: {st.session_state.bg_color};
        transition: background-color 0.3s ease;
    }}
    
    .block-container {{
        padding-top: 3rem !important;
    }}

    /* Header Styling bleibt wie gewünscht */
    .header-wrapper {{
        display: flex;
        justify-content: center;
        width: 100%;
        margin-bottom: 30px;
    }}

    .header-container {{
        border: 2px solid #D3D3D3;
        border-radius: 12px;
        background-color: rgba(211, 211, 211, 0.15);
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 0 40px;
        min-width: 320px;
        height: 80px;
    }}

    .title-text {{
        color: white !important;
        font-weight: bold !important;
        font-size: 2.2rem !important;
        margin: 0 !important;
        line-height: 80px !important;
    }}

    /* Neue Elemente: Task-Bereich Design */
    .task-status-box {{
        background: rgba(255, 255, 255, 0.08);
        border-radius: 15px;
        padding: 15px 25px;
        margin-bottom: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
    }}

    .task-label {{
        color: #D3D3D3;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 5px;
    }}

    .task-main-info {{
        color: white;
        font-size: 1.6rem;
        font-weight: bold;
    }}

    .progress-counter {{
        color: #7CFC00; /* Hellgrün für den Fortschritt */
        font-family: monospace;
        margin-left: 10px;
    }}

    /* Buttons & Timer (Unverändert im Stil) */
    .timer-text {{
        text-align: center; 
        font-size: 130px; 
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
        box-shadow: rgba(0, 0, 0, 0.2) 0px 5px 0px;
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
st.markdown("""
    <div class='header-wrapper'>
        <div class='header-container'>
            <h1 class='title-text'>Pomodoro Wächter</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- TASK MANAGEMENT (OPTIMIERT) ---
# Sidebar für das Management nutzen, um das Hauptlayout sauber zu halten
with st.sidebar:
    st.title("📚 Lern-Management")
    st.subheader("Neues Projekt")
    with st.form("task_form", clear_on_submit=True):
        name = st.text_input("Fach / Thema")
        target = st.number_input("Ziel (Pomodoros)", min_value=1, value=4)
        if st.form_submit_button("Hinzufügen"):
            if name:
                st.session_state.tasks[name] = [0, target]
                st.session_state.selected_task = name
                st.rerun()
    
    if st.button("Fortschritt zurücksetzen"):
        for t in st.session_state.tasks:
            st.session_state.tasks[t][0] = 0
        st.rerun()

# Hauptbereich: Auswahl und Anzeige
selected = st.selectbox("Aktuelles Ziel wählen:", options=list(st.session_state.tasks.keys()), label_visibility="collapsed")
st.session_state.selected_task = selected

done, total = st.session_state.tasks[st.session_state.selected_task]

st.markdown(f"""
    <div class='task-status-box'>
        <div class='task-label'>Fokus auf</div>
        <div class='task-main-info'>
            {st.session_state.selected_task} 
            <span class='progress-counter'>[{done}/{total}]</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- ALTBEWÄHRTE ELEMENTE (UNVERÄNDERT) ---
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
    
    if st.session_state.remaining_sec <= 0:
        st.session_state.active = False
        st.session_state.remaining_sec = 0
        if st.session_state.mode == "Pomodoro":
            st.session_state.tasks[st.session_state.selected_task][0] += 1
            st.balloons()
        st.rerun()

mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

_, btn_center, _ = st.columns([0.5, 1, 0.5])
with btn_center:
    if st.button("STOP" if st.session_state.active else "START", use_container_width=True):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()

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
