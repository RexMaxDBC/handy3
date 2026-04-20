import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
from transformers import pipeline
from PIL import Image
import av
import time

# --- MODELL LADEN ---
@st.cache_resource
def load_detector():
    # Wir laden das DETR Modell (Kein YOLO, kein OpenCV nötig)
    return pipeline("object-detection", model="facebook/detr-resnet-50")

detector = load_detector()

# --- STREAMLIT UI ---
st.set_page_config(page_title="Live Pomodoro AI", layout="wide")
st.title("🍅 Automatischer Fokus-Wächter")

if "is_break" not in st.session_state:
    st.session_state.is_break = False

with st.sidebar:
    st.header("Status")
    mode = st.radio("Modus wählen:", ["Fokus-Phase (Check AN)", "Pause (Check AUS)"])
    st.session_state.is_break = (mode == "Pause")
    st.info("Im Fokus-Modus scannt die KI automatisch alle paar Sekunden.")

# --- LIVE-KI LOGIK ---
class VideoProcessor(VideoTransformerBase):
    def __init__(self):
        self.last_check = 0
        self.alert = False

    def transform(self, frame):
        img = frame.to_image() # Konvertiert in PIL Image (Safe!)
        
        curr_time = time.time()
        # Nur alle 2 Sekunden scannen, um den Server nicht zu sprengen
        if not st.session_state.is_break and (curr_time - self.last_check > 2):
            self.last_check = curr_time
            
            # KI-Analyse
            predictions = detector(img)
            self.alert = any(res['label'] == 'cell phone' and res['score'] > 0.5 for res in predictions)

        # Wenn Handy erkannt, Bild verändern (z.B. rot färben)
        if self.alert and not st.session_state.is_break:
            # Hier nutzen wir PIL statt CV2 zum "Zeichnen"
            from PIL import ImageOps
            img = ImageOps.colorize(img.convert("L"), black="red", white="white")
            
        return av.VideoFrame.from_image(img)

# --- WEBCAM STREAM ---
ctx = webrtc_streamer(
    key="live-fokus",
    video_transformer_factory=VideoProcessor,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"video": True, "audio": False},
)

if st.session_state.is_break:
    st.success("☕ Genieße deine Pause. Die KI ist im Standby.")
else:
    st.warning("🚨 Fokus aktiv! Sobald ein Handy im Live-Bild erscheint, wird der Stream rot.")
