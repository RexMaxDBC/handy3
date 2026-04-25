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
    st.session_state.tasks = {} # {"Fach": {"done": 0, "target": 4}}
if "selected_task" not in st.session_state:
    st.session_state.selected_task = None

st.set_page_config(page_title="Pomodoro Wächter Pro", layout="wide")

# --- CSS (MODERNES DASHBOARD DESIGN) ---
st.markdown(f"""
<style>
    .stApp {{
        background-color: {st.session_state.bg_color};
        transition: background-color 0.4s ease;
    }}
    
    /* Header Box */
    .main-header {{
        border: 2px solid rgba(255,255,255,0.3);
        border-radius: 15px;
        background-color: rgba(255, 255, 255, 0.1);
        padding: 15px;
        text-align: center;
        margin-bottom: 30px;
    }}
    
    .title-text {{
        color: white !important;
        font-weight: 800 !important;
        font-size: 2.5rem !important;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 2px;
    }}

    /* Timer Card */
    .timer-card {{
        background: rgba(0, 0, 0, 0.2);
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }}

    .timer-display {{
        font-size: 160px;
        font-weight: 900;
        color: white;
        font-family: 'Courier New', Courier, monospace;
        line-height: 1;
        margin: 20px 0;
    }}

    /* Task Card in Sidebar */
    .task-entry {{
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        border-left: 4px solid #D3D3D3;
    }}

    /* Buttons */
    .stButton>button {{
        border-radius: 10px !important;
        font-weight: bold !important;
        transition: all 0.2s;
    }}

    div.stButton > button:last-child {{
        background-color: white !important;
        color: black !important;
        height: 70px !important;
        font-size: 28px !important;
        width: 100%;
        border: none !important;
        box-shadow: 0 6px 0 #bcbcbc !important;
    }}

    .fixed-bottom {{
        position: fixed;
        bottom: 0;
        right: 0;
        width: 400px;
        background: white;
        padding: 15px;
        border-radius: 20px 0 0 0;
        z-index: 1000;
        box-shadow: -5px -5px 20px rgba(0,0,0,0.2);
    }}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: LERN-VERWALTUNG ---
with st.sidebar:
    st.markdown("## 📚 Lern-Zentrum")
    
    # Neues Fach hinzufügen
    with st.expander("✨ Neues Projekt", expanded=False):
        new_name = st.text_input("Fachname", placeholder="z.B. Physik")
        new_target = st.number_input("Ziel-Einheiten", min_value=1, value=4)
        if st.button("Hinzufügen"):
            if new_name:
                st.session_state.tasks[new_name] = {"done": 0, "target": new_target}
                st.session_state.selected_task = new_name
                st.rerun()

    st.divider()
    
    # Fach auswählen
    if st.session_state.tasks:
        st.markdown("### Aktuelles Ziel")
        task_list = list(st.session_state.tasks.keys())
        selected = st.selectbox("Wofür lernst du gerade?", task_list, 
                               index=task_list.index(st.session_state.selected_task) if st.session_state.selected_task in task_list else 0)
        st.session_state.selected_task = selected
        
        # Fortschrittsanzeige in Sidebar
        task_data = st.session_state.tasks[selected]
        progress = task_data["done"] / task_data["target"]
        st.progress(min(progress, 1.0))
        st.write(f"**{task_data['done']} von {task_data['target']}** Einheiten geschafft")
        
        if st.button("🗑️ Fach löschen"):
            del st.session_state.tasks[selected]
            st.session_state.selected_task = None
            st.rerun()
    else:
        st.info("Füge in der Sidebar ein Fach hinzu, um zu starten!")

# --- HAUPTBEREICH ---
st.markdown("<div class='main-header'><h1 class='title-text'>Pomodoro Wächter Pro</h1></div>", unsafe_allow_html=True)

col_main, col_spacer, col_info = st.columns([2, 0.1, 1])

with col_main:
    # Timer Modus Buttons
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        if st.button("🍅 Pomodoro", use_container_width=True):
            st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Pomodoro", 25*60, "#2d5a27"
    with m_col2:
        if st.button("☕ Pause", use_container_width=True):
            st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Short Break", 5*60, "#457b9d"
    with m_col3:
        if st.button("🛋️ Lang", use_container_width=True):
            st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Long Break", 15*60, "#1d3557"

    # Timer Card
    st.markdown("<div class='timer-card'>", unsafe_allow_html=True)
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
    st.markdown(f"<div class='timer-display'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)
    
    if st.button("STOP" if st.session_state.active else "START"):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()
    st.markdown("</div>", unsafe_allow_html=True)

with col_info:
    if st.session_state.selected_task:
        st.markdown(f"### 🎯 Fokus: {st.session_state.selected_task}")
        st.write("Bleib konzentriert! Die Kamera überwacht deine Aufmerksamkeit.")
    else:
        st.warning("Kein Projekt ausgewählt. Erstelle eins in der Sidebar!")

# --- KI ÜBERWACHUNG (UNTEN RECHTS) ---
if st.session_state.active and st.session_state.mode == "Pomodoro":
    components.html("<script>setInterval(() => { const b = Array.from(window.parent.document.querySelectorAll('button')).find(x => x.innerText.includes('Photo')); if(b) b.click(); }, 5000);</script>", height=0)
    
    with st.container():
        st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1])
        with c1:
            img_file = st.camera_input("Check", key=f"c_{st.session_state.cam_key}", label_visibility="collapsed")
        with c2:
            if img_file:
                img = Image.open(img_file)
                results = detector(img)
                handy = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
                st.session_state.bg_color = "#ba4949" if handy else "#2d5a27"
                if handy:
                    st.error("HANDY!")
                    st.image(ImageOps.colorize(img.convert("L"), "red", "white"), width=150)
                else:
                    st.success("Fokus ok")
                    st.image(img, width=150)
                st.session_state.cam_key += 1
                time.sleep(0.5)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.active:
    time.sleep(0.1)
    st.rerun()
