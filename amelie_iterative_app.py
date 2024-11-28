def save_amelie_scenarios(selected_scenario):
    try:
        # Aggiorna il valore di "black_mass" nello scenario selezionato
        if selected_scenario in st.session_state.amelie_scenarios:
            st.session_state.amelie_scenarios[selected_scenario]["black_mass"] = st.session_state.black_mass

        # Salva tutti gli scenari su file
        with open(amelie_scenarios_file, "w") as file:
            json.dump(st.session_state.amelie_scenarios, file, indent=4)
        st.success("Amelie scenarios saved successfully.")
    except Exception as e:
        st.error(f"Failed to save Amelie scenarios: {e}")
