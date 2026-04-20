# --- DER VERBESSERTE AUTO-CLICKER (JavaScript) ---
if st.session_state.active:
    components.html(
        """
        <script>
        function autoStep() {
            const buttons = window.parent.document.querySelectorAll("button");
            
            // 1. Suche zuerst den "Löschen/Clear" Button (X-Icon oder Text)
            // Streamlit nutzt oft Aria-Labels für die Icons
            for (const btn of buttons) {
                if (btn.innerText === "Clear photo" || 
                    btn.innerText === "Foto löschen" || 
                    btn.getAttribute("aria-label") === "Clear photo") {
                    btn.click();
                }
            }

            // 2. Kurz warten und dann das neue Foto schießen
            setTimeout(() => {
                const newButtons = window.parent.document.querySelectorAll("button");
                for (const btn of newButtons) {
                    if (btn.innerText === "Take Photo" || btn.innerText === "Foto aufnehmen") {
                        btn.click();
                    }
                }
            }, 500); // 0,5 Sekunden Verzögerung zwischen Löschen und Neuaufnahme
        }

        // Alle 4 Sekunden den gesamten Prozess (Löschen -> Neu) starten
        setInterval(autoStep, 4000);
        </script>
        """,
        height=0,
    )
