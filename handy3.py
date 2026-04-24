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

# --- CSS BLOCK (PERFEKTE AUSRICHTUNG) ---
st.markdown(f'''
<style>
    .stApp {{
        background-color: {st.session_state.bg_color};
        transition: background-color 0.3s ease;
    }}
    
    /* Rückt den gesamten Inhalt tiefer von der Oberkante weg */
    .block-container {{
        padding-top: 5rem !important;
    }}

    /* Zentriert den Kasten auf der Seite */
    .header-wrapper {{
        display: flex;
        justify-content: center;
        width: 100%;
        margin-bottom: 50px;
    }}

    /* Der graue Kasten - Jetzt mit Flexbox für mittigen Text */
    .header-container {{
        border: 2px solid #D3D3D3;
        border-radius: 12px;
        background-color: rgba(211, 211, 211, 0.15);
        
        display: flex;          /* Aktiviert Flexbox */
        justify-content: center; /* Horizontale Zentrierung */
        align-items: center;     /* Vertikale Zentrierung */
        
        padding: 15px 40px;      /* Etwas mehr Futter */
        min-width: 300px;        /* Mindestbreite für Stabilität */
        height: 80px;            /* Feste Höhe für saubere vertikale Mitte */
    }}

    .title-text {{
        color: white !important;
        font-weight: bold !important;
        font-size: 2.2rem !important;
        margin: 0 !important;      /* WICHTIG: Entfernt Standard-Abstände */
        padding: 0 !important;
        text-align: center;
        line-height: 1 !important; /* Verhindert Versatz nach unten */
    }}

    .stButton>button {{
        border-radius: 6px;
        background-color: rgba(255, 255, 255, 0.15);
        color: white;
        border: none;
        font-weight: bold;
    }}
    
    div.stButton > button:last-child {{
        background-color: white !important;
        color: {st.session_state.bg_color} !important;
        font-size: 24px !important;
        height: 60px !important;
        width: 200px !important;
        margin: 30px auto !important;
        display: block !important;
        box-shadow: rgba(0, 0, 0, 0.2) 0px 5px 0px;
    }}

    .timer-text {{
        text-align: center; 
        font-size: 130px; 
        color: white; 
        font-weight: bold;
        margin: 20px 0;
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
''', unsafe_allow_html=True)

# --- LAYOUT INHALT ---
st.markdown("""
    <div class='header-wrapper'>
        <div class='header-container'>
            <h1 class='title-text'>Pomodoro Wächter</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 1. Modus Auswahl
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

# Timer Logik
if st.session_state.active and st.session_state.remaining_sec > 0:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now

# 2. Timer Anzeige
mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

# 3. Control Button
_, btn_center, _ = st.columns([0.5, 1, 0.5])
with btn_center:
    if st.button("STOP" if st.session_state.active else "START", use_container_width=True):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()

# --- KAMERA & KI ---
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
            st.image(img if not handy else ImageOps.colorize(img.convert("L"), "red", "white"), width=120)
            st.session_state.cam_key += 1
            time.sleep(0.5)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.active:
    time.sleep(0.1)
    st.rerun()    }}
    
    /* Sorgt dafür, dass der Inhalt nicht ganz oben klebt */
    .block-container {{
        padding-top: 3rem !important;
    }}

    /* Zentriert den Kasten auf der Seite */
    .header-wrapper {{
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin-bottom: 40px;
    }}

    /* Der graue Kasten - Sauber ausgerichtet */
    .header-container {{
        border: 2px solid #D3D3D3;
        border-radius: 12px;
        padding: 10px 30px;
        background-color: rgba(211, 211, 211, 0.15);
        display: flex;
        justify-content: center;
        align-items: center;
        min-width: 250px;
    }}

    .title-text {{
        color: white !important;
        font-weight: bold !important;
        font-size: 2rem !important;
        margin: 0 !important;
        padding: 0 !important;
        text-align: center;
        letter-spacing: 1px;
    }}

    .stButton>button {{
        border-radius: 6px;
        background-color: rgba(255, 255, 255, 0.15);
        color: white;
        border: none;
        font-weight: bold;
    }}
    
    div.stButton > button:last-child {{
        background-color: white !important;
        color: {st.session_state.bg_color} !important;
        font-size: 24px !important;
        height: 60px !important;
        width: 200px !important;
        margin: 30px auto !important;
        display: block !important;
        box-shadow: rgba(0, 0, 0, 0.2) 0px 5px 0px;
    }}

    .timer-text {{
        text-align: center; 
        font-size: 130px; 
        color: white; 
        font-weight: bold;
        margin: 20px 0;
        font-family: sans-serif;
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
''', unsafe_allow_html=True)

# --- LAYOUT INHALT ---
st.markdown("""
    <div class='header-wrapper'>
        <div class='header-container'>
            <h1 class='title-text'>Pomodoro Wächter</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 1. Modus Auswahl
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

# Timer Berechnung
if st.session_state.active and st.session_state.remaining_sec > 0:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now

# 2. Timer Anzeige
mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

# 3. Control Button
_, btn_center, _ = st.columns([0.5, 1, 0.5])
with btn_center:
    if st.button("STOP" if st.session_state.active else "START", use_container_width=True):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()

# --- KAMERA & KI LOGIK ---
if st.session_state.active and "Pomodoro" in st.session_state.mode:
    # Automatisches Foto alle 5 Sek
    components.html("<script>setInterval(() => { const b = Array.from(window.parent.document.querySelectorAll('button')).find(x => x.innerText.includes('Photo')); if(b) b.click(); }, 5000);</script>", height=0)
    
    st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        img_file = st.camera_input("Handy-Check", key=f"c_{st.session_state.cam_key}", label_visibility="collapsed")
    with c2:
        if img_file:
            img = Image.open(img_file)
            results = detector(img)
            handy = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
            st.session_state.bg_color = "#ba4949" if handy else "#2d5a27"
            if handy:
                st.error("HANDY ERKANNT!")
                st.image(ImageOps.colorize(img.convert("L"), "red", "white"), width=120)
            else:
                st.image(img, width=120)
            st.session_state.cam_key += 1
            time.sleep(0.5)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.active:
    time.sleep(0.1)
    st.rerun()
