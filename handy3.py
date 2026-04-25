# --- TASK DASHBOARD (OPTIMIERT) ---
st.markdown("<hr style='opacity: 0.1'>", unsafe_allow_html=True)

with st.expander("📝 Neues Lern-Fach anlegen"):
    # Spaltenverhältnis angepasst: Name bekommt mehr Platz, Button weniger
    c1, c2, c3 = st.columns([3, 1, 1]) 
    name = c1.text_input("Name des Fachs", key="add_name")
    target = c2.number_input("Ziel", min_value=1, value=4, key="add_target")
    
    # Button-Container für vertikale Ausrichtung
    with c3:
        st.write("##") # Kleiner Platzhalter, um den Button auf eine Höhe mit den Inputs zu bringen
        # use_container_width entfernt, damit er nicht den gesamten Platz flutet
        if st.button("Speichern", key="save_btn"):
            if name:
                st.session_state.tasks[name] = {"done": 0, "target": target}
                if st.session_state.selected_task is None:
                    st.session_state.selected_task = name
                st.rerun()

if st.session_state.tasks:
    st.markdown("### Deine Lernziele")
    for t_name, t_data in list(st.session_state.tasks.items()):
        is_active = (st.session_state.selected_task == t_name)
        css_class = "active-task-box" if is_active else "inactive-task-box"
        percent = min(100, (t_data["done"] / t_data["target"]) * 100)
        
        st.markdown(f"""
            <div class='{css_class}'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <b style='font-size: 1.2rem;'>{t_name} {' <span style="font-size: 0.8rem; opacity: 0.7;">(Aktiv)</span>' if is_active else ''}</b>
                    <span style='font-family: monospace;'>{t_data["done"]} / {t_data["target"]}</span>
                </div>
                <div class='progress-bar-bg'>
                    <div class='progress-bar-fill' style='width: {percent}%'></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Aktions-Buttons kompakter nebeneinander
        col_actions = st.columns([1, 1, 2]) # Dritte Spalte als Puffer
        
        if not is_active:
            with col_actions[0]:
                if st.button(f"Start", key=f"switch_{t_name}"):
                    st.session_state.selected_task = t_name
                    st.rerun()
        
        with col_actions[1]:
            # Kurzes Label, um den Button klein zu halten
            if st.button(f"Löschen", key=f"del_{t_name}"):
                del st.session_state.tasks[t_name]
                if st.session_state.selected_task == t_name:
                    st.session_state.selected_task = next(iter(st.session_state.tasks)) if st.session_state.tasks else None
                st.rerun()
