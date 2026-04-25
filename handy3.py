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
if "tasks" not in st.session_state:
    st.session_state.tasks = {} 
if "selected_task" not in st.session_state:
    st.session_state.selected_task = None

st.set_page_config(page_title="Pomodoro Wächter", layout="wide")

# --- CSS (CLEAN DASHBOARD LOOK) ---
st.markdown(f"""
<style>
    .stApp {{
        background-color: {st.session_state.bg_color};
        transition: background-color 0.3s ease;
    }}
    
    /* Titel-Kasten Design */
    .main-header {{
        border: 1.5px solid rgba(211, 211, 211, 0.4);
        border-radius: 10px;
        background-color: rgba(255, 255, 255, 0.1);
        padding: 10px 20px;
        text-align: center;
        margin-bottom: 2rem;
    }}
    
    .title-text {{
        color: white !important;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
        margin: 0 !important;
    }}

    /* Timer Große Anzeige */
    .timer-display {{
        text-align: center; 
        font-size: clamp(80px, 15vw, 150px); 
        color: white; 
        font-weight: 900;
        font-family: 'Courier New', Courier, monospace;
        margin: 20px 0;
        text-shadow: 2px 4px 10px rgba(0,0,0,0.3);
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.05);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }}

    /* Buttons */
    div.stButton > button {{
        border-radius: 12px;
        transition: all 0.2s;
    }}

    /* Start/Stop Button speziell */
    .start-btn button {{
        background-color: white !important;
        color: black !important;
        height: 70px !important;
        width: 100% !important;
        font-size: 1.5rem !important;
        font-weight: bold !important;
        box-shadow: 0px 6px 15px rgba(0,0,0,0.2) !important;
    }}

    .fixed-bottom {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: rgba(255, 255, 255, 0.98);
        padding: 10px;
        z-index: 1000;
        border-top: 2px solid #ddd;
    }}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: VERWALTUNG ---
with st.sidebar:
    st.title("⚙️ Verwaltung")
    
    with st.expander("📝 Neues Fach anlegen", expanded=not st.session_state.tasks):
        new_subj = st.text_input("Name des Fachs")
        new_target = st.number_input("Ziel-Einheiten", min_value=1, value=4)
        if st.button("Projekt speichern"):
            if new_subj:
                st.session_state.tasks[new_subj] = [0, new_target]
                st.session_state.selected_task = new_subj
                st.rerun()

    if st.session_state.tasks:
        st.divider()
        st.subheader("🎯 Aktives Projekt")
        st.session_state.selected_task = st.selectbox(
            "Wähle dein aktuelles Ziel:",
            options=list(st.session_state.tasks.keys())
        )
        
        # Kleine Fortschrittsanzeige in der Sidebar
        done, target = st.session_state.tasks[st.session_state.selected_task]
        st.progress(done / target if done < target else 1.0)
        st.write(f"Fortschritt: **{done} / {target}**")

# --- HAUPTBEREICH ---
# 1. Header
st.markdown('<div class="main-header"><h1 class="title-text">POMODORO WÄCHTER</h1></div>', unsafe_allow_html=True)

# 2. Status-Metriken (Nur wenn Task ausgewählt)
if st.session_state.selected_task:
    m1, m2, m3 = st.columns(3)
    done, target = st.session_state.tasks[st.session_state.selected_task]
    m1.metric("Projekt", st.session_state.selected_task)
    m2.metric("Fortschritt", f"{done} / {target}")
    m3.metric("Status", "Lernen" if st.session_state.mode == "Pomodoro" else "Pause")

# 3. Timer & Steuerung
st.markdown(f'<div class="timer-display">{time.strftime("%M:%S", time.gmtime(max(0, st.session_state.remaining_sec)))}</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    # Modus-Umschalter schöner nebeneinander
    mode_cols = st.columns(3)
    if mode_cols[0].button("Pomodoro", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color, st.session_state.active = "Pomodoro", 25*60, "#2d5a27", False
    if mode_cols[1].button("Pause", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color, st.session_state.active = "Short Break", 5*60, "#457b9d", False
    if mode_cols[2].button("Reset", use_container_width=True):
        st.session_state.remaining_sec, st.session_state.active = 25*60, False

    st.markdown('<div class="start-btn">', unsafe_allow_html=True)
    if st.button("STOP" if st.session_state.active else "START", use_container_width=True):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()
    st.markdown('</div>', unsafe_allow_html=True)

# --- LOGIK ---
if st.session_state.active:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now

    if st.session_state.remaining_sec <= 0:
        st.session_state.active = False
        if st.session_state.mode == "Pomodoro" and st.session_state.selected_task:
            st.session_state.tasks[st.session_state.selected_task][0] += 1
            st.balloons()
        st.rerun()

# --- KAMERA (FIXED BOTTOM) ---
if st.session_state.active and st.session_state.mode == "Pomodoro":
    components.html("<script>setInterval(() => { const b = Array.from(window.parent.document.querySelectorAll('button')).find(x => x.innerText.includes('Photo')); if(b) b.click(); }, 5000);</script>", height=0)
    
    st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
    cam_col1, cam_col2 = st.columns([3, 1])
    with cam_col1:
        img_file = st.camera_input("Überwachung", key=f"c_{st.session_state.cam_key}", label_visibility="collapsed")
    with cam_col2:
        if img_file:
            img = Image.open(img_file)
            handy = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in detector(img))
            st.session_state.bg_color = "#ba4949" if handy else "#2d5a27"
            st.image(img if not handy else ImageOps.colorize(img.convert("L"), "red", "white"), caption="Scan-Vorschau", width=150)
            st.session_state.cam_key += 1
            time.sleep(0.5)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.active:
    time.sleep(0.1)
    st.rerun()
