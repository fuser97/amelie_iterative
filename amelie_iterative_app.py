# Confronto migliorato: Scenari uno accanto all'altro
    st.markdown("### Compact Comparison of Mass/Volume Ratios")

    if not mass_volume_df.empty:
        for phase_name in mass_volume_df["Phase"].unique():
            st.markdown(f"#### Phase: {phase_name}")

            # Filtra i dati per la fase corrente
            phase_specific_df = mass_volume_df[mass_volume_df["Phase"] == phase_name]

            # Crea una tabella pivot per confrontare gli scenari
            pivot_data = phase_specific_df.pivot_table(
                index="Liquid Type",
                columns="Source",
                values=["Phase Mass (kg)", "Liquid Volume (L)", "S/L Ratio"],
                aggfunc="first"
            )

            # Migliora le etichette delle colonne per leggibilità
            pivot_data.columns = [' '.join(col).strip() for col in pivot_data.columns.values]

            # Mostra la tabella migliorata
            st.table(pivot_data)
