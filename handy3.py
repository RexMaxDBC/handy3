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

st.set_page_config(page_title="Pomodoro Clock AI", layout="centered")

# --- SESSION STATE ---
if "active" not in st.session_state:
    st.session_state.active = False
if "counter" not in st.session_state:
    st.session_state.counter = 0

st.title("🍅 Pomodoro AI Wächter")

with st.sidebar:
    st.header("Steuerung")
    minutes = st.number_input("Fokus-Zeit (Min)", min_value=1, value=25)
    if st.button("▶️ Start"):
        st.session_state.active = True
        st.session_state.timer_start = time.time()
    if st.button("⏹️ Stop"):
        st.session_state.active = False

# --- DIE JAVASCRIPT CLOCK ---
# Dieser Teil erzwingt das Klicken auf die Buttons im Browser-Intervall
if st.session_state.active:
    components.html(
        """
        <script>
        function clickCycle() {
            const parentDoc = window.parent.document;
            
            // 1. Suche nach dem Clear-Button (X)
            const clearBtn = Array.from(parentDoc.querySelectorAll("button")).find(el => 
                el.innerText === "Clear photo" || el.getAttribute("aria-label") === "Clear photo"
            );
            if (clearBtn) clearBtn.click();

            // 2. Warte kurz und klicke dann auf Aufnahme
            setTimeout(() => {
                const takeBtn = Array.from(parentDoc.querySelectorAll("button")).find(el => 
                    el.innerText === "Take Photo" || el.innerText === "Foto aufnehmen"
                );
                if (takeBtn) takeBtn.click();
            }, 1000);
        }
        
        // Startet den Zyklus alle 6 Sekunden
        setInterval(clickCycle, 6000);
        </script>
        """,
        height=0,
    )

# --- HAUPTTEIL ---
if st.session_state.active:
    elapsed = time.time() - st.session_state.timer_start
    remaining = (minutes * 60) - elapsed
    
    if remaining > 0:
        mins, secs = divmod(int(remaining), 60)
        st.subheader(f"⌛ Zeit übrig: {mins:02d}:{secs:02d}")

        # Das Kamera-Widget
        img_file = st.camera_input("Scanner", label_visibility="collapsed")

        if img_file:
            img = Image.open(img_file)
            with st.spinner("Prüfe auf Handy..."):
                results = detector(img)
            
            handy_gefunden = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
            
            if handy_gefunden:
                st.error("🚨 HANDY ERKANNT!")
                # Visueller Alarm
                st.image(ImageOps.colorize(img.convert("L"), black="red", white="white"))
            else:
                st.success("✅ Fokus aktiv!")
        
        # Kurze Pause für die Server-Last, dann Refresh
        time.sleep(1)
        st.rerun()
    else:
        # Hier war der Syntax-Fehler: Jetzt sauber getrennt
        st.session_state.active = False
        st.balloons()
        st.success("🎉 Zeit abgelaufen! Du hast jetzt Pause.")
else:
    st.info("Klicke in der Sidebar auf Start. Die Kamera wird dann automatisch gesteuert.")
# --- HAUPT-ANZEIGE & KI ---
if st.session_state.active:
    elapsed = time.time() - st.session_state.timer_start
    remaining = (minutes * 60) - elapsed
    
    if remaining > 0:
        mins, secs = divmod(int(remaining), 60)
        st.subheader(f"⌛ Zeit übrig: {mins:02d}:{secs:02d}")

        # Kamera Element
        img_file = st.camera_input("Kamera-Wächter aktiv", label_visibility="collapsed")

        if img_file:
            img = Image.open(img_file)
            
            # KI-Erkennung (DETR)
            with st.spinner("Analysiere..."):
                results = detector(img)
            
            # Prüfen auf Handy
            handy_gefunden = any(r['label'] == 'cell phone' and r['score'] > 0.5 for r in results)
            
            if handy_gefunden:
                st.error("🚨 HANDY ERKANNT! Leg es sofort weg!")
                # Visueller Alarm (Rot-Filter)
                st.image(ImageOps.colorize(img.convert("L"), black="red", white="white"), use_column_width=True)
            else:
                st.success("✅ Fokus gehalten! Kein Handy im Bild.")
                st.image(img, use_column_width=True)
    else:
        st.session_state.active = False
        st.balloons()
        st.success("🎉 Zeit abgelaufen! Du hast jetzt Pause.")
else:
    st.info("Klicke in der Sidebar auf Start. Der automatische Scan beginnt dann sofort.")
