import streamlit as st
from transformers import pipeline
from PIL import Image, ImageOps
import time
import os
import base64
import streamlit.components.v1 as components

# --- KI SETUP (Vortrainiertes Modell) ---
@st.cache_resource
def load_detector():
    # Lädt das facebook/detr-resnet-50 Modell für Objekterkennung
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
if "detail_task" not in st.session_state:
    st.session_state.detail_task = None

st.set_page_config(page_title="Pomodoro Wächter Pro", layout="centered")

# --- SOUND FUNKTIONEN ---
def play_alarm():
    if os.path.exists("batle-alarm-star-wars.mp3"):
        with open("batle-alarm-star-wars.mp3", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            audio_html = f"""
                <audio id="alarm_sound" autoplay="true" loop="true">
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                <script>
                    var audio = window.parent.document.getElementById("alarm_sound");
                    if (audio) {{ audio.play().catch(e => console.log(e)); }}
                </script>
                """
            st.markdown(audio_html, unsafe_allow_html=True)

def stop_alarm():
    stop_js = """
        <script>
        var audio = window.parent.document.getElementById("alarm_sound");
        if (audio) { audio.pause(); audio.currentTime = 0; audio.remove(); }
        </script>
        """
    components.html(stop_js, height=0)

# --- CSS DESIGN ---
st.markdown(f"""
<style>
    .stApp {{ background-color: {st.session_state.bg_color}; transition: background-color 0.8s ease; }}
    .header-container {{ border: 2px solid #D3D3D3; border-radius: 12px; background-color: rgba(211, 211, 211, 0.15); display: flex; justify-content: center; padding: 10px; margin-bottom: 30px; }}
    .title-text {{ color: white; font-weight: bold; font-size: 2.2rem; margin: 0; }}
    .timer-text {{ text-align: center; font-size: 110px; color: white; font-weight: bold; margin: 10px 0; line-height: 1; }}
    .fixed-bottom {{ position: fixed; bottom: 0; left: 0; width: 100%; background-color: white; padding: 15px; z-index: 1000; border-top: 1px solid #ddd; }}
    .active-task-box {{ background: rgba(255, 255, 255, 0.25); border: 2px solid white; border-radius: 10px; padding: 12px 15px; margin-bottom: 8px; color: white; }}
    .inactive-task-box {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 10px; padding: 12px 15px; margin-bottom: 8px; color: rgba(255, 255, 255, 0.7); }}
    
    /* Modal Styling */
    .modal-overlay {{ background: rgba(0,0,0,0.6); border-radius: 16px; padding: 28px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.2); }}
    .modal-title {{ color: white; font-size: 1.6rem; font-weight: bold; margin-bottom: 4px; }}
    .modal-subtitle {{ color: rgba(255,255,255,0.65); font-size: 0.9rem; margin-bottom: 20px; }}
    .progress-wrap {{ background: rgba(255,255,255,0.15); border-radius: 20px; height: 14px; margin-bottom: 6px; overflow: hidden; }}
    .progress-fill {{ height: 100%; border-radius: 20px; background: linear-gradient(90deg, #56ab2f, #a8e063); transition: width 0.4s; }}
    .progress-label {{ color: rgba(255,255,255,0.75); font-size: 0.85rem; margin-bottom: 20px; }}
    .comment-display {{ background: rgba(255,255,255,0.1); border-radius: 8px; padding: 10px 14px; color: white; font-size: 0.95rem; margin-top: 8px; font-style: italic; }}
</style>
""", unsafe_allow_html=True)

# --- UI HEADER ---
st.markdown("<div class='header-container'><h1 class='title-text'>Pomodoro Wächter Pro</h1></div>", unsafe_allow_html=True)

# --- DETAIL-MODAL (BEWERTUNGSSYSTEM) ---
if st.session_state.detail_task is not None:
    t = st.session_state.detail_task
    if t in st.session_state.tasks:
        task = st.session_state.tasks[t]
        if "stars" not in task: task["stars"] = 0
        if "comment" not in task: task["comment"] = ""
        
        done, target = task["done"], task["target"]
        pct = min(done / target, 1.0) if target > 0 else 0
        pct_int = int(pct * 100)

        st.markdown("<div class='modal-overlay'>", unsafe_allow_html=True)
        c_close, c_title = st.columns([1, 5])
        with c_close:
            if st.button("✕ Zu", use_container_width=True):
                st.session_state.detail_task = None
                st.rerun()
        with c_title:
            st.markdown(f"<div class='modal-title'>📚 {t}</div><div class='modal-subtitle'>Fach-Details & Bewertung</div>", unsafe_allow_html=True)

        st.markdown(f"""
            <div class='progress-wrap'><div class='progress-fill' style='width:{pct_int}%'></div></div>
            <div class='progress-label'>{done} von {target} Sessions ({pct_int}%) {' 🎉 Ziel erreicht!' if pct >= 1.0 else ''}</div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='color:white; font-weight:500; margin-bottom:6px;'>Meine Bewertung</div>", unsafe_allow_html=True)
        star_cols = st.columns(5)
        for i, col in enumerate(star_cols):
            star_num = i + 1
            icon = "⭐" if star_num <= task["stars"] else "☆"
            if col.button(f"{icon} {star_num}", key=f"star_{t}_{star_num}", use_container_width=True):
                task["stars"] = 0 if task["stars"] == star_num else star_num
                st.rerun()

        new_comment = st.text_area("Notiz", value=task["comment"], placeholder="Was war heute schwierig?", label_visibility="collapsed", key=f"txt_{t}")
        if st.button("💾 Speichern", key=f"save_{t}"):
            task["comment"] = new_comment
            st.success("Gespeichert!")
            st.rerun()
            
        if task["comment"]:
            st.markdown(f"<div class='comment-display'>\"{task['comment']}\"</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- MODUS AUSWAHL ---
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    if st.button("Pomodoro", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Pomodoro", 25*60, "#2d5a27"
        st.session_state.active = False
        st.rerun()
with m_col2:
    if st.button("Kurze Pause", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Pause", 5*60, "#457b9d"
        st.session_state.active = False
        st.rerun()
with m_col3:
    if st.button("Lange Pause", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Lange Pause", 15*60, "#457b9d"
        st.session_state.active = False
        st.rerun()

# --- TIMER LOGIK ---
if st.session_state.active:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now
    if st.session_state.remaining_sec <= 0:
        st.session_state.active = False
        if st.session_state.selected_task:
            st.session_state.tasks[st.session_state.selected_task]["done"] += 1
        st.balloons()
        st.rerun()

mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

_, btn_center, _ = st.columns([0.6, 1, 0.6])
with btn_center:
    if st.button("STOP" if st.session_state.active else "START", use_container_width=True):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()
        if not st.session_state.active: stop_alarm()
        st.rerun()

# --- TASK SYSTEM ---
st.markdown("<br>", unsafe_allow_html=True)
if st.session_state.selected_task:
    col_t, col_c = st.columns([3, 1])
    with col_t:
        t = st.session_state.selected_task
        st.markdown(f"<div class='active-task-box'>🎯 Fokus: <b>{t}</b> ({st.session_state.tasks[t]['done']}/{st.session_state.tasks[t]['target']})</div>", unsafe_allow_html=True)
    with col_c:
        if st.button("❌ Abwählen", use_container_width=True):
            st.session_state.selected_task = None
            st.rerun()

with st.expander("📝 Lernfächer verwalten"):
    c1, c2, c3 = st.columns([3, 1, 1])
    name = c1.text_input("Fach Name")
    target = c2.number_input("Ziel", min_value=1, value=4)
    if c3.button("Speichern"):
        if name:
            st.session_state.tasks[name] = {"done": 0, "target": target, "stars": 0, "comment": ""}
            st.rerun()

    for t_name, t_data in list(st.session_state.tasks.items()):
        is_active = (st.session_state.selected_task == t_name)
        css = "active-task-box" if is_active else "inactive-task-box"
        stars = "⭐" * t_data.get("stars", 0)
        st.markdown(f"<div class='{css}'>📚 <b>{t_name}</b> — {t_data['done']}/{t_data['target']} {stars}</div>", unsafe_allow_html=True)
        b1, b2, b3, b4 = st.columns([2, 1, 1, 1])
        if not is_active and b1.button("▶ Start", key=f"sel_{t_name}"):
            st.session_state.selected_task = t_name
            st.rerun()
        if b2.button("+1", key=f"p_{t_name}"):
            st.session_state.tasks[t_name]["done"] += 1
            st.rerun()
        if b3.button("📊", key=f"det_{t_name}"):
            st.session_state.detail_task = t_name
            st.rerun()
        if b4.button("🗑", key=f"del_{t_name}"):
            del st.session_state.tasks[t_name]
            if st.session_state.selected_task == t_name: st.session_state.selected_task = None
            st.rerun()

# --- KI SCANNER (Fehlalarm-Schutz auf 0.90) ---
if st.session_state.active and st.session_state.mode == "Pomodoro":
    components.html("<script>if(!window.parent.pI) window.parent.pI = setInterval(() => { const b = Array.from(window.parent.document.querySelectorAll('button')).find(x => x.innerText.includes('Photo')); if(b) b.click(); }, 6000);</script>", height=0)
    
    st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        img_f = st.camera_input("Scanner", key=f"c_{st.session_state.cam_key}", label_visibility="collapsed")
    with c2:
        if img_f:
            img = Image.open(img_f)
            results = detector(img)
            
            # Höherer Score (0.90) verhindert Fehlalarme
            handy_treffer = [r for r in results if r['label'] == 'cell phone' and r['score'] > 0.90]
            
            if handy_treffer:
                top_score = max([r['score'] for r in handy_treffer])
                st.session_state.bg_color = "#ba4949"
                play_alarm()
                st.error(f"🚨 HANDY! ({round(top_score * 100)}%)")
            else:
                st.session_state.bg_color = "#2d5a27"
                stop_alarm()
                st.success("✅ FOKUS")
            
            st.session_state.cam_key += 1
            time.sleep(1.2) # Etwas mehr Zeit für die UI
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.active:
    time.sleep(0.5)
    st.rerun()
