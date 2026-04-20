import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
from transformers import pipeline
from PIL import Image, ImageOps
import av
import time

# --- KI SETUP (Leichtes Modell für Live-Speed) ---
@st.cache_resource
def load_detector():
    # Wir nutzen ein sehr schnelles Objekterkennungs-Modell
    return pipeline("object-detection", model="google/vit-base-patch16-224") 

detector = load_detector()

# --- UI ---
st.set_page_config(page_title="Live Pomodoro AI", layout="centered")
st.title("🍅 Live Fokus-Wächter")

# Sidebar für Einstellungen
with st.sidebar:
    st.header("Timer")
    focus_minutes = st.number_input("Fokus-Dauer (Min)", min_value=1, value=25)
    start_timer = st.button("▶️ Start Fokus")
    stop_timer = st.button("⏹️ Pause")

if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "active" not in st.session_state:
    st.session_state.active = False

if start_timer:
    st.session_state.start_time = time.time()
    st.session_state.active = True
if stop_timer:
    st.session_state.active = False

# --- LIVE LOGIK ---
class PhoneGuard(VideoTransformerBase):
    def __init__(self):
        self.last_check = 0
        self.alert = False

    def transform(self, frame):
        img = frame.to_image()
        
        # Nur alle 3 Sekunden scannen, damit die App NICHT hängt
        now = time.time()
        if st.session_state.active and (now - self.last_check > 3):
            self.last_check = now
            # KI Check
            predictions = detector(img)
            # Wir prüfen auf "cell phone" oder ähnliche Labels (je nach Modell)
            self.alert = any(p['label'] in ['cell phone', 'mobile phone'] and p['score'] > 0.3 for p in predictions)

        # Visuelles Feedback direkt im Stream
        if self.alert and st.session_state.active:
            # Das Bild wird rot getönt, wenn das Handy da ist
            img = ImageOps.colorize(img.convert("L"), black="red", white="white")
        
        return av.VideoFrame.from_image(img)

# --- ANZEIGE ---
if st.session_state.active:
    elapsed = time.time() - st.session_state.start_time
    rem = max(0, int((focus_minutes * 60) - elapsed))
    mins, secs = divmod(rem, 60)
    st.subheader(f"⏳ Fokus aktiv: {mins:02d}:{secs:02d}")
    
    if rem <= 0:
        st.session_state.active = False
        st.balloons()
else:
    st.info("Klicke auf Start. In der Pause ist die KI deaktiviert.")

# Der Live-Stream
webrtc_streamer(
    key="guard",
    video_transformer_factory=PhoneGuard,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"video": True, "audio": False},
)
