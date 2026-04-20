import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import mediapipe as mp
from PIL import Image, ImageDraw, ImageFont
import av

# --- KI INITIALISIERUNG ---
mp_object_detection = mp.solutions.object_detection
detector = mp_object_detection.ObjectDetection(model_selection=0, min_detection_confidence=0.5)

# --- APP UI ---
st.title("🍅 Pomodoro AI (No-CV2 Edition)")

if "is_break" not in st.session_state:
    st.session_state.is_break = False

mode = st.radio("Aktueller Modus:", ["Fokus-Phase", "5-Minuten-Pause"])
st.session_state.is_break = (mode == "5-Minuten-Pause")

# --- VIDEO VERARBEITUNG ---
class PhoneDetector(VideoTransformerBase):
    def transform(self, frame):
        # Konvertiere Frame in ein Format, das MediaPipe/PIL verstehen (RGB)
        img = frame.to_image() 
        
        # KI-Erkennung
        results = detector.process(img.convert("RGB").__array__())
        
        phone_detected = False
        if results.detections:
            for detection in results.detections:
                for category in detection.label:
                    if category.display_name == "cell phone":
                        phone_detected = True

        # Zeichnen der Warnung ohne OpenCV (nur mit PIL)
        if phone_detected and not st.session_state.is_break:
            draw = ImageDraw.Draw(img)
            # Roter Balken oben als Warnung
            draw.rectangle([0, 0, img.width, 50], fill="red")
            draw.text((10, 10), "HANDY GEFUNDEN! KONZENTRIER DICH!", fill="white")

        # Zurückgeben als VideoFrame
        return av.VideoFrame.from_image(img)

# WebRTC Streamer starten
webrtc_streamer(key="example", video_transformer_factory=PhoneDetector)

if st.session_state.is_break:
    st.info("Es ist Pause. Die KI ignoriert dein Handy jetzt. 😊")
else:
    st.warning("Fokus-Modus aktiv: Die KI schlägt Alarm, wenn das Handy auftaucht!")
