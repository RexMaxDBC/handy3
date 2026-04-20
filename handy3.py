import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import mediapipe as mp
from PIL import Image, ImageDraw, ImageFont
import av
import time

# --- SEITEN KONFIGURATION ---
st.set_page_config(page_title="KI Pomodoro Fokus", page_icon="🍅")

# --- KI INITIALISIERUNG (MediaPipe) ---
# Wir laden das Modell einmalig, um Ressourcen zu sparen
@st.cache_resource
def load_detector():
    mp_object_detection = mp.solutions.object_detection
    return mp_object_detection.ObjectDetection(model_selection=0, min_detection_confidence=0.5)

detector = load_detector()

# --- SESSION STATE (Speichert Variablen über Neuladen hinweg) ---
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "is_break" not in st.session_state:
    st.session_state.is_break = False

# --- UI LAYOUT ---
st.title("🍅 AI Pomodoro Timer")
st.markdown("Dieses Projekt nutzt **MediaPipe**, um dein Handy während der Fokus-Phase zu erkennen.")

with st.sidebar:
    st.header("Einstellungen")
    focus_minutes = st.slider("Fokus-Zeit (Minuten)", 1, 60, 25)
    break_minutes = st.slider("Pausen-Zeit (Minuten)", 1, 20, 5)
    
    if st.button("Timer Start/Reset"):
        st.session_state.start_time = time.time()
        st.session_state.is_break = False

# --- LOGIK FÜR DEN TIMER ---
timer_display = st.empty()
status_display = st.empty()

if st.session_state.start_time is not None:
    elapsed = time.time() - st.session_state.start_time
    total_focus_sec = focus_minutes * 60
    
    if elapsed < total_focus_sec:
        remaining = int(total_focus_sec - elapsed)
        st.session_state.is_break = False
        status_display.warning("🔥 FOKUS PHASE: Handy weglegen!")
    else:
        # Pause beginnt nach Ablauf der Fokus-Zeit
        pause_elapsed = elapsed - total_focus_sec
        remaining = int((break_minutes * 60) - pause_elapsed)
        st.session_state.is_break = True
        
        if remaining > 0:
            status_display.success("☕ PAUSE: Du darfst dein Handy nutzen.")
        else:
            status_display.info("Session beendet. Zeit für eine neue Runde!")
            remaining = 0

    mins, secs = divmod(remaining, 60)
    timer_display.metric("Verbleibende Zeit", f"{mins:02d}:{secs:02d}")

# --- VIDEO VERARBEITUNGS KLASSE ---
class VideoProcessor(VideoProcessorBase):
    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_image() # PIL Image
        
        # Nur scannen, wenn wir nicht in der Pause sind
        if not st.session_state.is_break:
            # MediaPipe braucht ein Array
            results = detector.process(img.convert("RGB").__array__())
            
            phone_detected = False
            if results.detections:
                for detection in results.detections:
                    for category in detection.label:
                        if category.display_name == "cell phone":
                            phone_detected = True

            if phone_detected:
                # Zeichne Warnung direkt aufs Bild mit PIL
                draw = ImageDraw.Draw(img)
                # Rotes Rechteck als Banner
                draw.rectangle([0, 0, img.width, 80], fill=(255, 0, 0))
                # Text hinzufügen (Standardfont)
                draw.text((20, 20), "WARNUNG: HANDY ERKANNT!", fill=(255, 255, 255))

        return av.VideoFrame.from_image(img)

# --- WEBCAM STARTEN ---
ctx = webrtc_streamer(
    key="pomodoro-detector",
    video_processor_factory=VideoProcessor,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}, # Wichtig für Browser-Zugriff
    media_stream_constraints={"video": True, "audio": False},
)

st.info("Hinweis: Klicke oben auf 'Start', um die Webcam zu aktivieren. Der Handy-Warner ist nur aktiv, wenn der Timer läuft und keine Pause ist.")
