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

st.title("🍅 Vollautomatischer Pomodoro-Wächter")

# --- SESSION STATE ---
if "active" not in st.session_state:
    st.session_state.active = False
if "cam_key" not in st.session_state:
    st.session_state.cam_key = 0  # Dieser Key erzwingt den Reset

with st.sidebar:
    st.header("Steuerung")
    minutes = st.number_input("Fokus-Zeit (Min)", min_value=1, value=25)
    if st.button("▶️ Fokus Starten"):
        st.session_state.active = True
        st.session_state.timer_start = time.time()
    if st.button("⏹️ Stop"):
        st.session_state.active = False

# --- AUTOMATISIERUNG (JavaScript) ---
if st.session_state.active:
    # Dieses Skript drückt alle 5 Sekunden auf "Aufnahme"
    components.html(
        """
        <script>
        function shoot() {
            const buttons = window.parent.document.querySelectorAll("button");
            const takeBtn = Array.from(buttons).find(el => 
                el.innerText.includes("Photo") || el.innerText.includes("aufnehmen")
            );
            if (takeBtn) {
                takeBtn.click();
            }
        }
        // Nach 2 Sekunden das erste Foto, dann alle 5 Sek
        setTimeout(shoot, 2000); 
        </script>
        """,
        height=0,
    )

# --- HAUPT-LOGIK ---
if st.session_state.active:
    elapsed = time.time() - st.session_state.timer_start
    remaining = (minutes * 60) - elapsed
    
    if remaining > 0:
        mins, secs = divmod(int(remaining), 60)
        st.subheader(f"⌛ Zeit übrig: {mins:02d}:{secs:02d}")

        # WICHTIG: Der key ändert sich nach jedem Scan!
        img_file = st.camera_input("Scanner", key=f"cam_{st.session_state.cam_key}")

        if img_file:
            img = Image.open(img_file)
            with st.spinner("KI prüft..."):
                results = detector(img)
            
            handy_gefunden = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
            
            if handy_gefunden:
                st.error("🚨 HANDY ERKANNT!")
                st.image(ImageOps.colorize(img.convert("L"), black="red", white="white"))
            else:
                st.success("✅ Fokus aktiv!")
            
            # DER TRICK: Wir erhöhen den Key und schlafen kurz.
            # Dadurch wird das camera_input Widget beim nächsten Rerun gelöscht und neu erstellt.
            st.session_state.cam_key += 1
            time.sleep(3) # Pause, damit man das Ergebnis kurz sieht
            st.rerun()
            
    else:
        st.session_state.active = False
        st.balloons()
        st.success("🎉 Pause!")
else:
    st.info("Klicke auf Start. Die Kamera macht dann alle 5 Sekunden automatisch ein neues Bild.")
